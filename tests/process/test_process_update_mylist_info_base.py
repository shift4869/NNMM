"""ProcessUpdateMylistInfoBase のテスト
"""
import sys
import threading
import unittest
from contextlib import ExitStack
from logging import WARNING, getLogger

from mock import AsyncMock, MagicMock, call, patch

from NNMM.process.process_update_mylist_info_base import ProcessUpdateMylistInfoBase, ProcessUpdateMylistInfoThreadDoneBase

logger = getLogger("NNMM.process.process_update_mylist_info_base")
logger.setLevel(WARNING)


class ConcreteProcessUpdateMylistInfo(ProcessUpdateMylistInfoBase):
    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        """テスト用具体化クラス
        """
        super().__init__(True, False, "テスト用具体化クラス")
        self.L_KIND = "Concrete Kind"
        self.E_DONE = "Concrete Event Key"

    def make_mylist_db(self, num: int = 5) -> list[dict]:
        """mylist_db.select()で取得されるマイリストデータセット
        """
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i+1}", "投稿動画", "uploaded", f"投稿者{i+1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i+1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", True if i % 2 == 0 else False] for i in range(num)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def get_target_mylist(self) -> list[dict]:
        m_list = self.make_mylist_db()
        return m_list


class ConcreteProcessUpdateMylistInfoThreadDoneBase(ProcessUpdateMylistInfoThreadDoneBase):
    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        super().__init__(True, False, "テスト用具体化クラス")

    def get_target_mylist(self) -> list[dict]:
        return []


class TestProcessUpdateMylistInfoBase(unittest.TestCase):
    def make_mylist_db(self, num: int = 5) -> list[dict]:
        """mylist_db.select()で取得されるマイリストデータセット
        """
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i+1}", "投稿動画", "uploaded", f"投稿者{i+1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i+1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", True if i % 2 == 0 else False] for i in range(num)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def make_mylist_info_db(self, mylist_url: str) -> list[dict]:
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
            table_rows = [[n, f"sm{k+1}000000{i+1}", f"動画タイトル{k+1}_{i+1}", f"投稿者{k+1}", "",
                           f"2022-02-01 0{k+1}:00:0{i+1}",
                           f"2022-02-01 0{k+1}:01:0{i+1}",
                           f"https://www.nicovideo.jp/watch/sm{k+1}000000{i+1}",
                           mylist_url] for i in range(num)]
            n = n + 1

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return res

    def test_PUMIB_init(self):
        pumib = ConcreteProcessUpdateMylistInfo()
        self.assertIsNotNone(pumib.lock)
        self.assertEqual(0, pumib.done_count)
        self.assertEqual(ProcessUpdateMylistInfoThreadDoneBase, pumib.POST_PROCESS)
        self.assertEqual("Concrete Kind", pumib.L_KIND)
        self.assertEqual("Concrete Event Key", pumib.E_DONE)

    def test_PUMIB_get_target_mylist(self):
        pumib = ConcreteProcessUpdateMylistInfo()
        actual = pumib.get_target_mylist()
        expect = self.make_mylist_db()
        self.assertEqual(expect, actual)

    def test_PUMIB_get_prev_video_lists(self):
        with ExitStack() as stack:
            mockle = stack.enter_context(patch.object(logger, "error"))

            mock_mylist_info_db = MagicMock()
            mock_mylist_info_db.select_from_mylist_url.side_effect = self.make_mylist_info_db

            pumib = ConcreteProcessUpdateMylistInfo()
            pumib.mylist_info_db = mock_mylist_info_db

            m_list = self.make_mylist_db()
            actual = pumib.get_prev_video_lists(m_list)

            expect = []
            for record in m_list:
                mylist_url = record.get("url")
                prev_video_list = self.make_mylist_info_db(mylist_url)
                expect.append(prev_video_list)
            self.assertEqual(expect, actual)

            mylist_url_list = [record.get("url") for record in m_list]
            self.assertEqual(
                [call(mylist_url) for mylist_url in mylist_url_list],
                mock_mylist_info_db.select_from_mylist_url.mock_calls
            )

    def test_PUMIB_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mockthread = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.threading.Thread"))

            pumib = ConcreteProcessUpdateMylistInfo()

            mock_mw = MagicMock()
            actual = pumib.run(mock_mw)
            self.assertEqual(0, actual)
            self.assertEqual(0, pumib.done_count)

            mc = mock_mw.window.mock_calls
            self.assertEqual(3, len(mc))
            self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
            self.assertEqual(call.__getitem__().update(value="更新中"), mc[1])
            self.assertEqual(call.refresh(), mc[2])
            mock_mw.window.reset_mock()

            mc = mockthread.mock_calls
            self.assertEqual(2, len(mc))
            self.assertEqual(call(target=pumib.update_mylist_info_thread, args=(mock_mw, ), daemon=True), mc[0])
            self.assertEqual(call().start(), mc[1])
            mockthread.reset_mock()

            mock_mw = MagicMock()
            del mock_mw.window
            actual = pumib.run(mock_mw)
            self.assertEqual(-1, actual)

    def test_PUMIB_update_mylist_info_thread(self):
        """update_mylist_info_threadをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mocktime = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.time"))
            mockgpvl = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.ProcessUpdateMylistInfoBase.get_prev_video_lists"))
            mockgmie = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.ProcessUpdateMylistInfoBase.get_mylist_info_execute"))
            mockumie = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.ProcessUpdateMylistInfoBase.update_mylist_info_execute"))
            mockthread = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.threading.Thread"))

            pumib = ConcreteProcessUpdateMylistInfo()

            # 正常系
            mocktime.time.return_value = 0
            mock_mw = MagicMock()
            pumib.window = MagicMock()
            actual = pumib.update_mylist_info_thread(mock_mw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            pumib.window.assert_not_called()

            m_list = pumib.get_target_mylist()
            mockgpvl.assert_called_once_with(m_list)
            mockgmie.assert_called_once_with(m_list)
            mockumie.assert_called_once_with(m_list, mockgpvl.return_value, mockgmie.return_value)
            expect = [
                call(target=pumib.thread_done, args=(mock_mw, ), daemon=False),
                call().start(),
            ]
            self.assertEqual(expect, mockthread.mock_calls)

            # 更新対象が空だった
            pumib.get_target_mylist = lambda: []
            actual = pumib.update_mylist_info_thread(mock_mw)
            self.assertEqual(1, actual)

            mc = pumib.window.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.write_event_value(pumib.E_DONE, ""), mc[0])
            pumib.window.reset_mock()

            # 異常系
            # 属性エラー
            del pumib.window
            actual = pumib.update_mylist_info_thread(mock_mw)
            self.assertEqual(-1, actual)

    def test_PUMIB_get_mylist_info_execute(self):
        """get_mylist_info_executeをテストする
        """
        with ExitStack() as stack:
            mocktpe = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.ThreadPoolExecutor"))

            pumib = ConcreteProcessUpdateMylistInfo()

            # 正常系
            NUM = 5
            m_list = self.make_mylist_db(NUM)

            r = MagicMock()
            r.submit.side_effect = lambda f, mylist_url, all_index_num: MagicMock()
            mocktpe.return_value.__enter__.side_effect = lambda: r

            expect = []
            for record in m_list:
                mylist_url = record.get("url")
                expect.append(mylist_url)

            actual = pumib.get_mylist_info_execute(m_list)
            self.assertEqual(expect, [a[0] for a in actual])

            # 実行後呼び出し確認
            mc = r.submit.mock_calls
            self.assertEqual(NUM, len(mc))
            for mc_e, record in zip(mc, m_list):
                mylist_url = record.get("url")
                self.assertEqual(call(pumib.get_mylist_info_worker, mylist_url, NUM), mc_e)
            r.submit.reset_mock()

            mc = mocktpe.mock_calls
            self.assertEqual(3, len(mc))
            self.assertEqual(call(max_workers=8, thread_name_prefix="ap_thread"), mc[0])
            self.assertEqual(call().__enter__(), mc[1])
            self.assertEqual(call().__exit__(None, None, None), mc[2])
            mocktpe.reset_mock()

    def test_PUMIB_get_mylist_info_worker(self):
        """get_mylist_info_worker をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mock_fetch_videoinfo = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.VideoInfoRssFetcher.fetch_videoinfo"))

            pumib = ConcreteProcessUpdateMylistInfo()

            mock_fetch_videoinfo.side_effect = lambda mylist_url: [mylist_url]

            # 正常系
            pumib.window = MagicMock()
            NUM = 5
            mylist_url = "https://www.nicovideo.jp/user/10000001/video"
            expect = [mylist_url]
            actual = pumib.get_mylist_info_worker(mylist_url, NUM)
            self.assertEqual(expect, actual)
            self.assertEqual(1, pumib.done_count)

            # 実行後呼び出し確認
            p_str = f"取得中({pumib.done_count}/{NUM})"
            mc = pumib.window.mock_calls
            self.assertEqual(2, len(mc))
            self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
            self.assertEqual(call.__getitem__().update(value=p_str), mc[1])
            pumib.window.reset_mock()
            pumib.done_count = 0

    def test_PUMIB_update_mylist_info_execute(self):
        """update_mylist_info_execute をテストする
        """
        with ExitStack() as stack:
            mocktpe = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.ThreadPoolExecutor"))

            pumib = ConcreteProcessUpdateMylistInfo()

            # 正常系
            NUM = 5
            m_list = self.make_mylist_db(NUM)
            p_list = []
            n_list = []

            def return_select_from_mylist_url(mylist_url):
                res = []
                records = self.make_mylist_info_db(NUM)
                for record in records:
                    if record.get("mylist_url") == mylist_url:
                        res.append(record)
                return res

            expect = []
            for m in m_list:
                mylist_url = m.get("url")
                expect.append(mylist_url)
                p_list.append(return_select_from_mylist_url(mylist_url))
                n_list.append(return_select_from_mylist_url(mylist_url))

            r = MagicMock()
            r.submit.side_effect = lambda f, m, p, n: MagicMock()
            mocktpe.return_value.__enter__.side_effect = lambda: r

            actual = pumib.update_mylist_info_execute(m_list, p_list, n_list)
            self.assertEqual(expect, [a[0] for a in actual])

            # 実行後呼び出し確認
            mc = r.submit.mock_calls
            self.assertEqual(NUM, len(mc))
            for mc_e, m, p in zip(mc, m_list, p_list):
                self.assertEqual(call(pumib.update_mylist_info_worker, m, p, n_list), mc_e)
            r.submit.reset_mock()

            mc = mocktpe.mock_calls
            self.assertEqual(3, len(mc))
            self.assertEqual(call(max_workers=8, thread_name_prefix="np_thread"), mc[0])
            self.assertEqual(call().__enter__(), mc[1])
            self.assertEqual(call().__exit__(None, None, None), mc[2])
            mocktpe.reset_mock()

            # 異常系
            # マイリストレコードとprev_video_listの大きさが異なる
            p_list = p_list[:-1]
            actual = pumib.update_mylist_info_execute(m_list, p_list, n_list)
            self.assertEqual([], actual)

    def test_PUMIB_update_mylist_info_worker(self):
        """update_mylist_info_worker をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mockgdt = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.get_now_datetime"))
            mockmdb = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.MylistDBController"))
            mockmidb = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.MylistInfoDBController"))

            pumib = ConcreteProcessUpdateMylistInfo()

            # 正常系
            dst = "2022-02-08 01:00:01"
            mockgdt.side_effect = lambda: dst
            NUM = 5
            m_list = self.make_mylist_db()
            m_record = m_list[0]
            p_list = []
            n_list = []

            def return_select_from_mylist_url(mylist_url):
                res = []
                records = self.make_mylist_info_db(mylist_url)
                for i, record in enumerate(records):
                    if record.get("mylist_url") == mylist_url:
                        record["status"] = "未視聴" if i % 2 == 0 else ""
                        record["id"] = record["no"]
                        del record["no"]
                        res.append(record)
                return res

            def return_get_mylist_info(mylist_url):
                records = self.make_mylist_info_db(mylist_url)
                records[0]["status"] = "未視聴"
                return records

            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(return_select_from_mylist_url(mylist_url))
                n_list.append((mylist_url, return_get_mylist_info(mylist_url)))
            p = p_list[0]

            pumib.window = MagicMock()
            pumib.mylist_db = MagicMock()
            pumib.mylist_info_db = MagicMock()
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(0, actual)
            self.assertEqual(1, pumib.done_count)

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
                p_str = f"更新中({pumib.done_count}/{all_index_num})"
                mc = pumib.window.mock_calls
                self.assertEqual(2, len(mc))
                self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
                self.assertEqual(call.__getitem__().update(value=p_str), mc[1])
                pumib.window.reset_mock()

            assertMockCall()
            pumib.done_count = 0

            # 新規動画追加
            # 既存動画リストを少なくしてその差分だけ新規追加とみなす
            # ステータスが"未視聴"で設定されるかどうか
            p = [p[0]] + p[2:]
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(0, actual)
            self.assertEqual(1, pumib.done_count)
            assertMockCall()
            pumib.done_count = 0

            # ユーザーネームが変更されている
            # mylist_url = m_record.get("url")
            # for n in n_list:
            #     if n[0] == mylist_url:
            #         for nr in n[1]:
            #             nr["username"] = "新しい投稿者名1"
            # actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            # self.assertEqual(0, actual)
            # self.assertEqual(1, pumib.done_count)
            # assertMockCall()
            # pumib.done_count = 0

            # マイリストに登録されている動画情報の件数が0
            mylist_url = m_record.get("url")
            n_list[0] = (mylist_url, [])
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(1, actual)

            # 異常系
            # mylist_info_dbに格納するために必要なキーが存在しない
            n_list = [(m.get("url"), return_get_mylist_info(m.get("url"))) for m in m_list]
            for n in n_list:
                if n[0] == mylist_url:
                    for nr in n[1]:
                        del nr["title"]
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 動画情報のリストのリストにマイリストの重複が含まれている
            n_list[0] = (mylist_url, n_list[1][1])
            n_list[1] = (mylist_url, n_list[1][1])
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストに想定外のキーがある
            n_list = [(m.get("url"), return_get_mylist_info(m.get("url"))) for m in m_list]
            n_list[0][1][0]["不正なキー"] = "不正な値"
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストの一部がリストでない
            n_list[0] = (mylist_url, "不正な値")
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストの一部のマイリストURLが空
            n_list[0] = ("", n_list[1][1])
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが2重空リスト
            actual = pumib.update_mylist_info_worker(m_record, p, [[]])
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが空リスト
            actual = pumib.update_mylist_info_worker(m_record, p, [])
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストがNone
            actual = pumib.update_mylist_info_worker(m_record, p, None)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが文字列
            actual = pumib.update_mylist_info_worker(m_record, p, "不正な引数")
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストに想定外のキーがある
            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(return_select_from_mylist_url(mylist_url))
                n_list.append((mylist_url, return_get_mylist_info(mylist_url)))
            p = p_list[0]
            p[0]["不正なキー"] = "不正な値"
            actual = pumib.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが空リスト
            actual = pumib.update_mylist_info_worker(m_record, [], n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストがNone
            actual = pumib.update_mylist_info_worker(m_record, None, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが文字列
            actual = pumib.update_mylist_info_worker(m_record, "不正な引数", n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトのurlが空
            del p[0]["不正なキー"]
            actual = pumib.update_mylist_info_worker({"url": ""}, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが空辞書
            actual = pumib.update_mylist_info_worker({}, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトがNone
            actual = pumib.update_mylist_info_worker(None, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが文字列
            actual = pumib.update_mylist_info_worker("不正な引数", p, n_list)
            self.assertEqual(-1, actual)

    def test_PUMIB_thread_done(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            pumib = ConcreteProcessUpdateMylistInfo()

            mock_post_process = MagicMock()
            mock_mw = MagicMock()
            pumib.POST_PROCESS = mock_post_process

            actual = pumib.thread_done(mock_mw)
            self.assertEqual(None, actual)
            mock_post_process.assert_called_once_with()
            mock_post_process().run.assert_called_once_with(mock_mw)

    def test_PUMITDB_init(self):
        pumitdb = ConcreteProcessUpdateMylistInfoThreadDoneBase()
        self.assertEqual("UpdateMylist Base", pumitdb.L_KIND)

    def test_PUMITDB_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mock_update_table_pane = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.update_table_pane"))
            mock_is_mylist_include_new_video = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.is_mylist_include_new_video"))
            mock_update_mylist_pane = stack.enter_context(patch("NNMM.process.process_update_mylist_info_base.update_mylist_pane"))

            pumitdb = ConcreteProcessUpdateMylistInfoThreadDoneBase()
            mock_mylist_db = MagicMock()
            mock_mylist_db.select.side_effect = self.make_mylist_db
            mock_mylist_info_db = MagicMock()
            mock_mylist_info_db.select_from_mylist_url.side_effect = self.make_mylist_info_db
            mock_is_mylist_include_new_video.side_effect = lambda def_data: True

            m_list = self.make_mylist_db()
            mock_mw = MagicMock()
            mock_mw.values = {"-INPUT1-": m_list[0]["url"]}
            mock_mw.mylist_db = mock_mylist_db
            mock_mw.mylist_info_db = mock_mylist_info_db

            actual = pumitdb.run(mock_mw)
            self.assertEqual(0, actual)

            def mock_check(mylist_url_empty, is_mylist_include_new_video_flag):
                mylist_url = mock_mw.values["-INPUT1-"]
                if not mylist_url_empty:
                    mock_update_table_pane.assert_called_once_with(
                        mock_mw.window, mock_mw.mylist_db, mock_mw.mylist_info_db, mylist_url
                    )
                mock_mylist_db.select.assert_called_once_with()
                for m in m_list:
                    mylist_url = m["url"]
                    mock_mylist_info_db.select_from_mylist_url.assert_any_call(mylist_url)
                    video_list = self.make_mylist_info_db(mylist_url)
                    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
                    def_data = []
                    for i, t in enumerate(video_list):
                        a = [i + 1, t["video_id"], t["title"], t["username"], t["status"], t["uploaded_at"], t["registered_at"], t["video_url"], t["mylist_url"]]
                        def_data.append(a)

                    if is_mylist_include_new_video_flag:
                        mock_is_mylist_include_new_video.assert_any_call(def_data)
                        mock_mylist_db.update_include_flag.assert_any_call(mylist_url, True)
                mock_update_mylist_pane.assert_called_once_with(mock_mw.window, mock_mw.mylist_db)

                mock_update_table_pane.reset_mock()
                mock_mylist_db.select.reset_mock()
                mock_mylist_info_db.select_from_mylist_url.reset_mock()
                mock_is_mylist_include_new_video.reset_mock()
                mock_mylist_db.update_include_flag.reset_mock()
                mock_update_mylist_pane.reset_mock()
            mock_check(False, True)

            mock_is_mylist_include_new_video.side_effect = lambda def_data: False
            mock_mw.values = {"-INPUT1-": m_list[0]["url"]}
            actual = pumitdb.run(mock_mw)
            self.assertEqual(0, actual)
            mock_check(False, False)

            mock_is_mylist_include_new_video.side_effect = lambda def_data: True
            mock_mw.values = {"-INPUT1-": ""}
            actual = pumitdb.run(mock_mw)
            self.assertEqual(0, actual)
            mock_check(True, True)

            mock_is_mylist_include_new_video.side_effect = lambda def_data: False
            mock_mw.values = {"-INPUT1-": ""}
            actual = pumitdb.run(mock_mw)
            self.assertEqual(0, actual)
            mock_check(True, False)

            del mock_mw.window
            actual = pumitdb.run(mock_mw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
