import sys
import threading
import unittest
from collections import namedtuple
from contextlib import ExitStack
from copy import deepcopy

import PySimpleGUI as sg
from mock import AsyncMock, MagicMock, ThreadingMock, call, patch

from NNMM.model import Mylist, MylistInfo
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist_info_base import ProcessUpdateMylistInfoBase, ProcessUpdateMylistInfoThreadDoneBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class ConcreteProcessUpdateMylistInfoBase(ProcessUpdateMylistInfoBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.L_KIND = "Concrete Kind"
        self.E_DONE = "Concrete Event Key"

    def get_target_mylist(self) -> list[dict]:
        return []


class TestProcessUpdateMylistInfoBase(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_db(self, num: int = 5) -> list[dict]:
        """mylist_db.select()で取得されるマイリストデータセット
        """
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i + 1}", "投稿動画", "uploaded",
                 f"投稿者{i + 1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i + 1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", True if i % 2 == 0 else False] for i in range(num)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_mylist_info_db(self, mylist_url: str) -> list[dict]:
        """mylist_info_db.select()で取得される動画情報データセット
        """
        res = []
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded_at", "registered_at", "video_url", "mylist_url"]
        num = 5
        n = 0
        for k in range(num):
            table_rows = [[n, f"sm{k + 1}000000{i + 1}", f"動画タイトル{k + 1}_{i + 1}",
                           f"投稿者{k + 1}", "",
                           f"2022-02-01 0{k + 1}:00:0{i + 1}",
                           f"2022-02-01 0{k + 1}:01:0{i + 1}",
                           f"https://www.nicovideo.jp/watch/sm{k + 1}000000{i + 1}",
                           mylist_url] for i in range(num)]
            n = n + 1

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return res

    def _make_prev_video_lists(self, m_list: list[Mylist]) -> list[list[MylistInfo]]:
        """prev_video_lists データセット
        """
        prev_video_lists = []
        for record in m_list:
            mylist_url = record.get("url")
            prev_video_list = self._make_mylist_info_db(mylist_url)
            prev_video_lists.append(prev_video_list)
        return prev_video_lists

    def test_init(self):
        instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)
        self.assertIsNotNone(instance.lock)
        self.assertEqual(0, instance.done_count)
        self.assertEqual(ProcessUpdateMylistInfoThreadDoneBase, instance.post_process)
        self.assertEqual("Concrete Kind", instance.L_KIND)
        self.assertEqual("Concrete Event Key", instance.E_DONE)

    def test_get_target_mylist(self):
        instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)
        actual = instance.get_target_mylist()
        self.assertEqual([], actual)

    def test_get_prev_video_lists(self):
        mock_mylist_info_db = MagicMock()
        mock_mylist_info_db.select_from_mylist_url.side_effect = self._make_mylist_info_db

        instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)
        instance.mylist_info_db = mock_mylist_info_db

        m_list = self._make_mylist_db()
        actual = instance.get_prev_video_lists(m_list)
        expect = self._make_prev_video_lists(m_list)
        self.assertEqual(expect, actual)

        mylist_url_list = [record.get("url") for record in m_list]
        self.assertEqual(
            [call(mylist_url) for mylist_url in mylist_url_list],
            mock_mylist_info_db.select_from_mylist_url.mock_calls
        )

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.update_mylist_info_base.logger.info"))
            mock_thread = stack.enter_context(patch("NNMM.process.update_mylist_info_base.threading.Thread"))

            instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)

            actual = instance.run()
            self.assertIs(Result.success, actual)

            self.assertEqual([
                call.__getitem__("-INPUT2-"),
                call.__getitem__().update(value="更新中"),
                call.refresh(),
            ], instance.window.mock_calls)

            self.assertEqual([
                call(target=instance.update_mylist_info_thread, 
                     daemon=True),
                call().start(),
            ], mock_thread.mock_calls)

    def test_update_mylist_info_thread(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.update_mylist_info_base.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.update_mylist_info_base.logger.error"))
            mock_time = stack.enter_context(patch("NNMM.process.update_mylist_info_base.time"))
            mock_thread = stack.enter_context(patch("NNMM.process.update_mylist_info_base.threading"))
            mock_get_target_mylist = MagicMock()
            mock_get_prev_video_lists = MagicMock()
            mock_get_mylist_info_execute = MagicMock()
            mock_update_mylist_info_execute = MagicMock()

            instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)

            def pre_run(valid_m_list):
                instance.window.reset_mock()
                mock_get_target_mylist.reset_mock()
                if valid_m_list:
                    m_list = self._make_mylist_db()
                    mock_get_target_mylist.side_effect = lambda: m_list
                else:
                    mock_get_target_mylist.side_effect = lambda: []
                instance.get_target_mylist = mock_get_target_mylist
                mock_get_prev_video_lists.reset_mock()
                instance.get_prev_video_lists = mock_get_prev_video_lists
                mock_get_mylist_info_execute.reset_mock()
                instance.get_mylist_info_execute = mock_get_mylist_info_execute
                mock_update_mylist_info_execute.reset_mock()
                instance.update_mylist_info_execute = mock_update_mylist_info_execute
                mock_time.reset_mock()
                mock_time.time.side_effect = lambda: 0

            def post_run(valid_m_list):
                self.assertEqual([
                    call()
                ], mock_get_target_mylist.mock_calls)

                if not valid_m_list:
                    self.assertEqual([
                        call.write_event_value(instance.E_DONE, "")
                    ], instance.window.mock_calls)
                    return
                else:
                    instance.window.assert_not_called()

                m_list = self._make_mylist_db()
                self.assertEqual([
                    call(m_list)
                ], mock_get_prev_video_lists.mock_calls)

                self.assertEqual([
                    call(m_list)
                ], mock_get_mylist_info_execute.mock_calls)

                prev_video_lists = mock_get_prev_video_lists.return_value
                now_video_lists = mock_get_mylist_info_execute.return_value
                self.assertEqual([
                    call(m_list, prev_video_lists, now_video_lists)
                ], mock_update_mylist_info_execute.mock_calls)

                self.assertEqual([
                    call.Lock(),
                    call.Thread(target=instance.thread_done, daemon=False),
                    call.Thread().start(),
                ], mock_thread.mock_calls)

            Params = namedtuple("Params", ["valid_m_list", "result"])
            params_list = [
                Params(True, None),
                Params(False, None),
            ]
            for params in params_list:
                pre_run(params.valid_m_list)
                actual = instance.update_mylist_info_thread()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.valid_m_list)

    def test_get_mylist_info_worker(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.update_mylist_info_base.logger.info"))
            mock_fetcher = stack.enter_context(patch("NNMM.process.update_mylist_info_base.VideoInfoRssFetcher.fetch_videoinfo"))

            instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)

            m_list = self._make_mylist_db()
            all_index_num = len(m_list)
            mylist_url = m_list[0]["url"]
            def pre_run(valid_fetch):
                mock_fetcher.reset_mock()
                if valid_fetch:
                    mock_fetcher.side_effect = lambda mylist_url: f"fetch_result_{mylist_url}"
                else:
                    mock_fetcher.side_effect = ValueError
                instance.window.reset_mock()
                instance.done_count = 0

            def post_run(valid_fetch):
                self.assertEqual([
                    call(mylist_url)
                ], mock_fetcher.mock_calls)

                p_str = f"取得中({instance.done_count}/{all_index_num})"
                self.assertEqual([
                    call.__getitem__("-INPUT2-"),
                    call.__getitem__().update(value=p_str),
                ], instance.window.mock_calls)

                self.assertEqual(1, instance.done_count)

            Params = namedtuple("Params", ["valid_m_list", "result"])
            params_list = [
                Params(True, f"fetch_result_{mylist_url}"),
                Params(False, None),
            ]
            for params in params_list:
                pre_run(params.valid_m_list)
                actual = instance.get_mylist_info_worker(mylist_url, all_index_num)
                expect = params.result
                self.assertEqual(expect, actual)
                post_run(params.valid_m_list)

    def test_get_mylist_info_execute(self):
        with ExitStack() as stack:
            mock_executor = stack.enter_context(patch("NNMM.process.update_mylist_info_base.ThreadPoolExecutor"))

            instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)

            m_list = self._make_mylist_db()
            all_index_num = len(m_list)
            mylist_urls = [
                record["url"] for record in m_list
            ]
            actual = instance.get_mylist_info_execute(m_list)

            expect_executor_calls = [
                call(max_workers=8, thread_name_prefix="ap_thread"),
                call().__enter__(),
            ]
            expect_executor_calls.extend([
                call().__enter__().submit(
                    instance.get_mylist_info_worker, mylist_url, all_index_num
                ) for mylist_url in mylist_urls
            ])
            expect_executor_calls.extend([
                call().__enter__().submit().result() for _ in range(all_index_num)
            ])
            expect_executor_calls.append(
                 call().__exit__(None, None, None)
            )
            self.assertEqual(expect_executor_calls, mock_executor.mock_calls)

            futures = [
                mock_executor().__enter__().submit().result() for _ in range(all_index_num)
            ]
            expect = [
                (mylist_url, future) for mylist_url, future in zip(mylist_urls, futures)
            ]
            self.assertEqual(expect, actual)

    def test_update_mylist_info_execute(self):
        with ExitStack() as stack:
            mock_executor = stack.enter_context(patch("NNMM.process.update_mylist_info_base.ThreadPoolExecutor"))

            instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)

            m_list = self._make_mylist_db()
            prev_video_lists = self._make_prev_video_lists(m_list)
            now_video_lists = deepcopy(prev_video_lists)
            future_result = mock_executor().__enter__().submit().result()
            def pre_run(s_m_list, s_prev_video_lists, s_now_video_lists):
                mock_executor.reset_mock()

            def post_run(s_m_list, s_prev_video_lists, s_now_video_lists):
                if len(s_m_list) != len(s_prev_video_lists):
                    mock_executor.assert_not_called()
                    return
                all_index_num = len(s_m_list)
                expect_executor_calls = [
                    call(max_workers=8, thread_name_prefix="np_thread"),
                    call().__enter__(),
                ]
                expect_executor_calls.extend([
                    call().__enter__().submit(
                        instance.update_mylist_info_worker,
                        m, prev_video_list, s_now_video_lists
                    ) for m, prev_video_list in zip(m_list, prev_video_lists)
                ])
                expect_executor_calls.extend([
                    call().__enter__().submit().result() for _ in range(all_index_num)
                ])
                expect_executor_calls.append(
                    call().__exit__(None, None, None)
                )
                self.assertEqual(expect_executor_calls, mock_executor.mock_calls)

            def make_expect(s_m_list, s_prev_video_lists, s_now_video_lists):
                mylist_urls = [
                    record["url"] for record in s_m_list
                ]
                all_index_num = len(s_m_list)
                futures = [
                    future_result for _ in range(all_index_num)
                ]
                return [
                    (mylist_url, future) for mylist_url, future in zip(mylist_urls, futures)
                ]

            Params = namedtuple("Params", ["m_list", "prev_video_lists", "now_video_lists", "result"])
            params_list = [
                Params(m_list, prev_video_lists, now_video_lists,
                       make_expect(m_list, prev_video_lists, now_video_lists)),
                Params(m_list, prev_video_lists[1:], now_video_lists, []),
            ]
            for params in params_list:
                pre_run(params.m_list, params.prev_video_lists, params.now_video_lists)
                actual = instance.update_mylist_info_execute(
                    params.m_list, params.prev_video_lists, params.now_video_lists
                )
                expect = params.result
                self.assertEqual(expect, actual)
                post_run(params.m_list, params.prev_video_lists, params.now_video_lists)

    def test_update_mylist_info_worker(self):
        return
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.update_mylist_info_base.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.update_mylist_info_base.logger.error"))
            mockgdt = stack.enter_context(patch("NNMM.process.update_mylist_info_base.get_now_datetime"))
            mockmdb = stack.enter_context(patch("NNMM.process.update_mylist_info_base.MylistDBController"))
            mockmidb = stack.enter_context(patch("NNMM.process.update_mylist_info_base.MylistInfoDBController"))

            instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)

            # 正常系
            dst = "2022-02-08 01:00:01"
            mockgdt.side_effect = lambda: dst
            NUM = 5
            m_list = self._make_mylist_db()
            m_record = m_list[0]
            p_list = []
            n_list = []

            def return_select_from_mylist_url(mylist_url):
                res = []
                records = self._make_mylist_info_db(mylist_url)
                for i, record in enumerate(records):
                    if record.get("mylist_url") == mylist_url:
                        record["status"] = "未視聴" if i % 2 == 0 else ""
                        record["id"] = record["no"]
                        del record["no"]
                        res.append(record)
                return res

            def return_get_mylist_info(mylist_url):
                records = self._make_mylist_info_db(mylist_url)
                records[0]["status"] = "未視聴"
                return records

            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(return_select_from_mylist_url(mylist_url))
                n_list.append((mylist_url, return_get_mylist_info(mylist_url)))
            p = p_list[0]

            instance.window = MagicMock()
            instance.mylist_db = MagicMock()
            instance.mylist_info_db = MagicMock()
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(0, actual)
            self.assertEqual(1, instance.done_count)

            # 実行後呼び出し確認
            def assertMockCall():
                mc_i = mockmdb.mock_calls
                i = 1
                mc_j = mockmidb.mock_calls
                j = 1
                prev_video_list = p
                mylist_url = m_record.get("url")
                records = [r[1] for r in n_list if r[0] == mylist_url][0]

                prev_videoid_list = [m["video_id"] for m in prev_video_list]
                prev_username = ""
                if prev_video_list:
                    prev_username = prev_video_list[0].get("username")
                now_video_list = records
                now_videoid_list = [m["video_id"] for m in now_video_list]

                status_check_list = []
                add_new_video_flag = False
                for n in now_videoid_list:
                    if n in prev_videoid_list:
                        s = [p["status"] for p in prev_video_list if p["video_id"] == n]
                        status_check_list.append(s[0])
                    else:
                        status_check_list.append("未視聴")
                        add_new_video_flag = True

                for m, s in zip(now_video_list, status_check_list):
                    m["status"] = s

                # if now_video_list:
                #     now_username = now_video_list[0].get("username")
                #     if prev_username != now_username:
                #         self.assertEqual(call().update_username(mylist_url, now_username), mc_i[i])
                #         i = i + 1
                #         self.assertEqual(call().update_username_in_mylist(mylist_url, now_username), mc_j[j])
                #         j = j + 1

                records = []
                for m in now_video_list:
                    r = {
                        "video_id": m["video_id"],
                        "title": m["title"],
                        "username": m["username"],
                        "status": m["status"],
                        "uploaded_at": m["uploaded_at"],
                        "registered_at": m["registered_at"],
                        "video_url": m["video_url"],
                        "mylist_url": m["mylist_url"],
                        "created_at": dst
                    }
                    records.append(r)

                self.assertEqual(call().upsert_from_list(records), mc_j[j])
                j = j + 1

                self.assertEqual(call().update_checked_at(mylist_url, dst), mc_i[i])
                i = i + 1
                if add_new_video_flag:
                    self.assertEqual(call().update_updated_at(mylist_url, dst), mc_i[i])
                    i = i + 1

                mockmdb.reset_mock()
                mockmidb.reset_mock()

                all_index_num = len(n_list)
                p_str = f"更新中({instance.done_count}/{all_index_num})"
                mc = instance.window.mock_calls
                self.assertEqual(2, len(mc))
                self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
                self.assertEqual(call.__getitem__().update(value=p_str), mc[1])
                instance.window.reset_mock()

            assertMockCall()
            instance.done_count = 0

            # 新規動画追加
            # 既存動画リストを少なくしてその差分だけ新規追加とみなす
            # ステータスが"未視聴"で設定されるかどうか
            p = [p[0]] + p[2:]
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(0, actual)
            self.assertEqual(1, instance.done_count)
            assertMockCall()
            instance.done_count = 0

            # ユーザーネームが変更されている
            # mylist_url = m_record.get("url")
            # for n in n_list:
            #     if n[0] == mylist_url:
            #         for nr in n[1]:
            #             nr["username"] = "新しい投稿者名1"
            # actual = instance.update_mylist_info_worker(m_record, p, n_list)
            # self.assertEqual(0, actual)
            # self.assertEqual(1, instance.done_count)
            # assertMockCall()
            # instance.done_count = 0

            # マイリストに登録されている動画情報の件数が0
            mylist_url = m_record.get("url")
            n_list[0] = (mylist_url, [])
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(1, actual)

            # 異常系
            # mylist_info_dbに格納するために必要なキーが存在しない
            n_list = [(m.get("url"), return_get_mylist_info(m.get("url"))) for m in m_list]
            for n in n_list:
                if n[0] == mylist_url:
                    for nr in n[1]:
                        del nr["title"]
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 動画情報のリストのリストにマイリストの重複が含まれている
            n_list[0] = (mylist_url, n_list[1][1])
            n_list[1] = (mylist_url, n_list[1][1])
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストに想定外のキーがある
            n_list = [(m.get("url"), return_get_mylist_info(m.get("url"))) for m in m_list]
            n_list[0][1][0]["不正なキー"] = "不正な値"
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストの一部がリストでない
            n_list[0] = (mylist_url, "不正な値")
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストの一部のマイリストURLが空
            n_list[0] = ("", n_list[1][1])
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが2重空リスト
            actual = instance.update_mylist_info_worker(m_record, p, [[]])
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが空リスト
            actual = instance.update_mylist_info_worker(m_record, p, [])
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストがNone
            actual = instance.update_mylist_info_worker(m_record, p, None)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが文字列
            actual = instance.update_mylist_info_worker(m_record, p, "不正な引数")
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストに想定外のキーがある
            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(return_select_from_mylist_url(mylist_url))
                n_list.append((mylist_url, return_get_mylist_info(mylist_url)))
            p = p_list[0]
            p[0]["不正なキー"] = "不正な値"
            actual = instance.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが空リスト
            actual = instance.update_mylist_info_worker(m_record, [], n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストがNone
            actual = instance.update_mylist_info_worker(m_record, None, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが文字列
            actual = instance.update_mylist_info_worker(m_record, "不正な引数", n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトのurlが空
            del p[0]["不正なキー"]
            actual = instance.update_mylist_info_worker({"url": ""}, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが空辞書
            actual = instance.update_mylist_info_worker({}, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトがNone
            actual = instance.update_mylist_info_worker(None, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが文字列
            actual = instance.update_mylist_info_worker("不正な引数", p, n_list)
            self.assertEqual(-1, actual)

    def test_thread_done(self):
        return
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.update_mylist_info_base.logger.info"))
            instance = ConcreteProcessUpdateMylistInfoBase(self.process_info)

            mock_post_process = MagicMock()
            mock_mw = MagicMock()
            instance.POST_PROCESS = mock_post_process

            actual = instance.thread_done(mock_mw)
            self.assertEqual(None, actual)
            mock_post_process.assert_called_once_with()
            mock_post_process().run.assert_called_once_with(mock_mw)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
