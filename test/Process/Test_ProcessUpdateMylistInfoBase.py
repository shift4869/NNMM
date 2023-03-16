# coding: utf-8
"""ProcessUpdateMylistInfoBase のテスト
"""
import sys
import unittest
from contextlib import ExitStack
from logging import WARNING, getLogger

from mock import AsyncMock, MagicMock, call, patch

from NNMM.Process import ProcessUpdateMylistInfoBase

logger = getLogger("NNMM.Process.ProcessUpdateMylistInfoBase")
logger.setLevel(WARNING)


class ConcreteProcessUpdateMylistInfo(ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase):
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

    def make_mylist_info_db(self, num: int = 5) -> list[dict]:
        """mylist_info_db.select()で取得される動画情報データセット
        """
        res = []
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded_at", "registered_at", "video_url", "mylist_url"]
        n = 0
        for k in range(num):
            table_rows = [[n, f"sm{k+1}000000{i+1}", f"動画タイトル{k+1}_{i+1}", f"投稿者{k+1}", "",
                           f"2022-02-01 0{k+1}:00:0{i+1}",
                           f"2022-02-01 0{k+1}:01:0{i+1}",
                           f"https://www.nicovideo.jp/watch/sm{k+1}000000{i+1}",
                           f"https://www.nicovideo.jp/user/1000000{k+1}/video"] for i in range(num)]
            n = n + 1

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return res

    def test_PUAMIrun(self):
        """ProcessUpdateMylistInfoBaseのrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mockthread = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.threading.Thread"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            mockmw = MagicMock()
            actual = puami.run(mockmw)
            self.assertEqual(0, actual)
            self.assertEqual(0, puami.done_count)

            # 実行後呼び出し確認
            mc = mockmw.window.mock_calls
            self.assertEqual(3, len(mc))
            self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
            self.assertEqual(call.__getitem__().update(value="更新中"), mc[1])
            self.assertEqual(call.refresh(), mc[2])
            mockmw.window.reset_mock()

            mc = mockthread.mock_calls
            self.assertEqual(2, len(mc))
            self.assertEqual(call(target=puami.update_mylist_info_thread, args=(mockmw, ), daemon=True), mc[0])
            self.assertEqual(call().start(), mc[1])
            mockthread.reset_mock()

            # 異常系
            # 引数エラー
            mockmw = MagicMock()
            del mockmw.window
            actual = puami.run(mockmw)
            self.assertEqual(-1, actual)

    def test_update_mylist_info_thread(self):
        """update_mylist_info_threadをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mocktime = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.time"))
            mockgfl = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase.get_function_list"))
            mockgpvl = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase.get_prev_video_lists"))
            mockgmie = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase.get_mylist_info_execute"))
            mockumie = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase.update_mylist_info_execute"))
            mockthread = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.threading.Thread"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            mocktime.time.return_value = 0
            mock_mw = MagicMock()
            puami.window = MagicMock()
            actual = puami.update_mylist_info_thread(mock_mw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            puami.window.assert_not_called()

            m_list = puami.get_target_mylist()
            mockgfl.assert_called_once_with(m_list)
            mockgpvl.assert_called_once_with(m_list)
            mockgmie.assert_called_once_with(mockgfl.return_value, m_list)
            mockumie.assert_called_once_with(m_list, mockgpvl.return_value, mockgmie.return_value)
            expect = [
                call(target=puami.thread_done, args=(mock_mw, ), daemon=False),
                call().start(),
            ]
            self.assertEqual(expect, mockthread.mock_calls)

            # 更新対象が空だった
            puami.get_target_mylist = lambda: []
            actual = puami.update_mylist_info_thread(mock_mw)
            self.assertEqual(1, actual)

            mc = puami.window.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.write_event_value(puami.E_DONE, ""), mc[0])
            puami.window.reset_mock()

            # 異常系
            # 属性エラー
            del puami.window
            actual = puami.update_mylist_info_thread(mock_mw)
            self.assertEqual(-1, actual)

    def test_get_function_list(self):
        """get_function_listをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            # mockagmi = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.VideoInfoHtmlFetcher.fetch_videoinfo"))
            mockagmilw = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.VideoInfoRssFetcher.fetch_videoinfo"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            prev_video_list = self.make_mylist_info_db(num=3)

            def Returnselect_from_mylist_url(mylist_url):
                res = []
                for record in prev_video_list:
                    if record.get("mylist_url") == mylist_url:
                        res.append(record)
                return res

            r = MagicMock()
            r.select_from_mylist_url = Returnselect_from_mylist_url
            puami.mylist_info_db = r

            m_list = self.make_mylist_db(num=5)
            expect = [mockagmilw for i in range(5)]
            actual = puami.get_function_list(m_list)
            self.assertEqual(expect, actual)

            # 引数に空リスト指定時
            actual = puami.get_function_list([])
            self.assertEqual([], actual)

            # 異常系
            # 属性エラー
            del puami.mylist_info_db
            actual = puami.get_function_list(m_list)
            self.assertEqual([], actual)

    def test_get_prev_video_lists(self):
        """get_prev_video_listsをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            prev_video_list = self.make_mylist_info_db()

            def Returnselect_from_mylist_url(mylist_url):
                res = []
                for record in prev_video_list:
                    if record.get("mylist_url") == mylist_url:
                        res.append(record)
                return res

            r = MagicMock()
            r.select_from_mylist_url = Returnselect_from_mylist_url
            puami.mylist_info_db = r

            m_list = self.make_mylist_db()
            expect = [Returnselect_from_mylist_url(m["url"]) for m in m_list]
            actual = puami.get_prev_video_lists(m_list)
            self.assertEqual(expect, actual)

            # 引数に空リスト指定時
            actual = puami.get_prev_video_lists([])
            self.assertEqual([], actual)

            # 異常系
            # 属性エラー
            del puami.mylist_info_db
            actual = puami.get_prev_video_lists(m_list)
            self.assertEqual([], actual)

    def test_get_mylist_info_execute(self):
        """get_mylist_info_executeをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mocktpe = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ThreadPoolExecutor"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            NUM = 5
            m_list = self.make_mylist_db(NUM)
            f_list = [MagicMock() for _ in range(NUM)]

            r = MagicMock()
            r.submit.side_effect = lambda f, func, mylist_url, all_index_num: MagicMock()
            mocktpe.return_value.__enter__.side_effect = lambda: r

            expect = []
            for func, record in zip(f_list, m_list):
                mylist_url = record.get("url")
                expect.append(mylist_url)

            actual = puami.get_mylist_info_execute(f_list, m_list)
            self.assertEqual(expect, [a[0] for a in actual])

            # 実行後呼び出し確認
            mc = r.submit.mock_calls
            self.assertEqual(NUM, len(mc))
            for mc_e, func, record in zip(mc, f_list, m_list):
                mylist_url = record.get("url")
                self.assertEqual(call(puami.get_mylist_info_worker, func, mylist_url, NUM), mc_e)
            r.submit.reset_mock()

            mc = mocktpe.mock_calls
            self.assertEqual(3, len(mc))
            self.assertEqual(call(max_workers=4, thread_name_prefix="ap_thread"), mc[0])
            self.assertEqual(call().__enter__(), mc[1])
            self.assertEqual(call().__exit__(None, None, None), mc[2])
            mocktpe.reset_mock()

            # 異常系
            # 引数のメソッドリストの中に呼び出し可能でないものが含まれている
            f_list = [f"不正なメソッド_{i}" for i in range(NUM)]
            actual = puami.get_mylist_info_execute(f_list, m_list)
            self.assertEqual([], actual)

            # マイリストURLが空
            m_list = [{"url": ""} for _ in range(NUM)]
            f_list = [MagicMock() for _ in range(NUM)]
            actual = puami.get_mylist_info_execute(f_list, m_list)
            self.assertEqual([], actual)

            # メソッドリストとマイリストレコードリストの大きさが異なる
            m_list = self.make_mylist_db(NUM)
            f_list = [MagicMock() for _ in range(NUM - 1)]
            actual = puami.get_mylist_info_execute(f_list, m_list)
            self.assertEqual([], actual)

    def test_get_mylist_info_worker(self):
        """get_mylist_info_worker をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            puami.window = MagicMock()
            NUM = 5
            func = AsyncMock()
            func.side_effect = lambda url: [url]
            mylist_url = "https://www.nicovideo.jp/user/10000001/video"
            expect = [mylist_url]
            actual = puami.get_mylist_info_worker(func, mylist_url, NUM)
            self.assertEqual(expect, actual)
            self.assertEqual(1, puami.done_count)

            # 実行後呼び出し確認
            p_str = f"取得中({puami.done_count}/{NUM})"
            mc = puami.window.mock_calls
            self.assertEqual(2, len(mc))
            self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
            self.assertEqual(call.__getitem__().update(value=p_str), mc[1])
            puami.window.reset_mock()
            puami.done_count = 0

            func.assert_called_once_with(mylist_url)
            func.reset_mock()

            # 異常系
            # funcが呼び出し可能でない
            func = "不正なメソッド指定"
            actual = puami.get_mylist_info_worker(func, mylist_url, NUM)
            self.assertEqual([], actual)

            # マイリストURLが空
            func = AsyncMock()
            mylist_url = ""
            actual = puami.get_mylist_info_worker(func, mylist_url, NUM)
            self.assertEqual([], actual)

            # 属性エラー
            del puami.window
            actual = puami.get_mylist_info_worker(func, mylist_url, NUM)
            self.assertEqual([], actual)

    def test_update_mylist_info_execute(self):
        """update_mylist_info_execute をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mocktpe = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ThreadPoolExecutor"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            NUM = 5
            m_list = self.make_mylist_db(NUM)
            p_list = []
            n_list = []

            def Returnselect_from_mylist_url(mylist_url):
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
                p_list.append(Returnselect_from_mylist_url(mylist_url))
                n_list.append(Returnselect_from_mylist_url(mylist_url))

            r = MagicMock()
            r.submit.side_effect = lambda f, m, p, n: MagicMock()
            mocktpe.return_value.__enter__.side_effect = lambda: r

            actual = puami.update_mylist_info_execute(m_list, p_list, n_list)
            self.assertEqual(expect, [a[0] for a in actual])

            # 実行後呼び出し確認
            mc = r.submit.mock_calls
            self.assertEqual(NUM, len(mc))
            for mc_e, m, p in zip(mc, m_list, p_list):
                self.assertEqual(call(puami.update_mylist_info_worker, m, p, n_list), mc_e)
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
            actual = puami.update_mylist_info_execute(m_list, p_list, n_list)
            self.assertEqual([], actual)

    def test_update_mylist_info_worker(self):
        """update_mylist_info_worker をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mockgdt = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.get_now_datetime"))
            mockmdb = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.MylistDBController"))
            mockmidb = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.MylistInfoDBController"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            dst = "2022-02-08 01:00:01"
            mockgdt.side_effect = lambda: dst
            NUM = 5
            m_list = self.make_mylist_db()
            m_record = m_list[0]
            p_list = []
            n_list = []

            def Returnselect_from_mylist_url(mylist_url):
                res = []
                records = self.make_mylist_info_db(NUM)
                for i, record in enumerate(records):
                    if record.get("mylist_url") == mylist_url:
                        record["status"] = "未視聴" if i % 2 == 0 else ""
                        record["id"] = record["no"]
                        del record["no"]
                        res.append(record)
                return res

            def ReturnGetMylistInfo(mylist_url):
                res = []
                records = self.make_mylist_info_db(NUM)
                for i, record in enumerate(records):
                    if record.get("mylist_url") == mylist_url:
                        record["status"] = "未視聴" if i % 2 == 0 else ""
                        res.append(record)
                return res

            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(Returnselect_from_mylist_url(mylist_url))
                n_list.append((mylist_url, ReturnGetMylistInfo(mylist_url)))
            p = p_list[0]

            puami.window = MagicMock()
            puami.mylist_db = MagicMock()
            puami.mylist_info_db = MagicMock()
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(0, actual)
            self.assertEqual(1, puami.done_count)

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

                if now_video_list:
                    now_username = now_video_list[0].get("username")
                    if prev_username != now_username:
                        self.assertEqual(call().update_username(mylist_url, now_username), mc_i[i])
                        i = i + 1
                        self.assertEqual(call().update_username_in_mylist(mylist_url, now_username), mc_j[j])
                        j = j + 1

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
                p_str = f"更新中({puami.done_count}/{all_index_num})"
                mc = puami.window.mock_calls
                self.assertEqual(2, len(mc))
                self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
                self.assertEqual(call.__getitem__().update(value=p_str), mc[1])
                puami.window.reset_mock()

            assertMockCall()
            puami.done_count = 0

            # 新規動画追加
            # 既存動画リストを少なくしてその差分だけ新規追加とみなす
            # ステータスが"未視聴"で設定されるかどうか
            p = [p[0]] + p[2:]
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(0, actual)
            self.assertEqual(1, puami.done_count)
            assertMockCall()
            puami.done_count = 0

            # ユーザーネームが変更されている
            # mylist_url = m_record.get("url")
            # for n in n_list:
            #     if n[0] == mylist_url:
            #         for nr in n[1]:
            #             nr["username"] = "新しい投稿者名1"
            # actual = puami.update_mylist_info_worker(m_record, p, n_list)
            # self.assertEqual(0, actual)
            # self.assertEqual(1, puami.done_count)
            # assertMockCall()
            # puami.done_count = 0

            # マイリストに登録されている動画情報の件数が0
            mylist_url = m_record.get("url")
            n_list[0] = (mylist_url, [])
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(1, actual)

            # 異常系
            # mylist_info_dbに格納するために必要なキーが存在しない
            n_list = [(m.get("url"), ReturnGetMylistInfo(m.get("url"))) for m in m_list]
            for n in n_list:
                if n[0] == mylist_url:
                    for nr in n[1]:
                        del nr["title"]
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 動画情報のリストのリストにマイリストの重複が含まれている
            n_list[0] = (mylist_url, n_list[1][1])
            n_list[1] = (mylist_url, n_list[1][1])
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストに想定外のキーがある
            n_list = [(m.get("url"), ReturnGetMylistInfo(m.get("url"))) for m in m_list]
            n_list[0][1][0]["不正なキー"] = "不正な値"
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストの一部がリストでない
            n_list[0] = (mylist_url, "不正な値")
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストの一部のマイリストURLが空
            n_list[0] = ("", n_list[1][1])
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが2重空リスト
            actual = puami.update_mylist_info_worker(m_record, p, [[]])
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが空リスト
            actual = puami.update_mylist_info_worker(m_record, p, [])
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストがNone
            actual = puami.update_mylist_info_worker(m_record, p, None)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが文字列
            actual = puami.update_mylist_info_worker(m_record, p, "不正な引数")
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストに想定外のキーがある
            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(Returnselect_from_mylist_url(mylist_url))
                n_list.append((mylist_url, ReturnGetMylistInfo(mylist_url)))
            p = p_list[0]
            p[0]["不正なキー"] = "不正な値"
            actual = puami.update_mylist_info_worker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが空リスト
            actual = puami.update_mylist_info_worker(m_record, [], n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストがNone
            actual = puami.update_mylist_info_worker(m_record, None, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが文字列
            actual = puami.update_mylist_info_worker(m_record, "不正な引数", n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトのurlが空
            del p[0]["不正なキー"]
            actual = puami.update_mylist_info_worker({"url": ""}, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが空辞書
            actual = puami.update_mylist_info_worker({}, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトがNone
            actual = puami.update_mylist_info_worker(None, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが文字列
            actual = puami.update_mylist_info_worker("不正な引数", p, n_list)
            self.assertEqual(-1, actual)

    def test_UAMITPrun(self):
        """ProcessUpdateMylistInfoBase のrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.update_table_pane"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.update_mylist_pane"))

            puamitd = ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoThreadDoneBase()

            # 正常系
            def Returnselect_from_mylist_url(mylist_url):
                res = []
                records = self.make_mylist_info_db(num=5)
                for i, record in enumerate(records):
                    if record.get("mylist_url") == mylist_url:
                        record["status"] = "未視聴" if i % 2 == 0 and i < 15 else ""
                        res.append(record)
                return res

            m_list = self.make_mylist_db()
            mylist_url = m_list[0].get("url")
            expect_valus_dict = {
                "-INPUT1-": mylist_url
            }

            mockmw = MagicMock()
            mockvalues = MagicMock()
            mockvalues.__getitem__.side_effect = expect_valus_dict.__getitem__
            mockvalues.__iter__.side_effect = expect_valus_dict.__iter__
            mockvalues.__contains__.side_effect = expect_valus_dict.__contains__
            mockmw.values = mockvalues
            mockmdb = MagicMock()
            mockmdb.select.side_effect = lambda: self.make_mylist_db()
            mockmw.mylist_db = mockmdb
            mockmidb = MagicMock()
            mockmidb.select_from_mylist_url.side_effect = Returnselect_from_mylist_url
            mockmw.mylist_info_db = mockmidb
            actual = puamitd.run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            mc = mockmw.window.mock_calls
            self.assertEqual(2, len(mc))
            self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
            self.assertEqual(call.__getitem__().update(value="更新完了！"), mc[1])
            mockmw.window.reset_mock()

            mc = mockmw.values.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.__getitem__("-INPUT1-"), mc[0])
            mockmw.values.reset_mock()

            mc = mockmw.mylist_db.mock_calls
            self.assertEqual(4, len(mc))
            self.assertEqual(call.select(), mc[0])
            for i, m in enumerate(m_list[:3]):
                mylist_url = m.get("url")
                self.assertEqual(call.update_include_flag(mylist_url, True), mc[i + 1])
            mockmw.mylist_db.reset_mock()

            mc = mockmw.mylist_info_db.mock_calls
            self.assertEqual(5, len(mc))
            for i, m in enumerate(m_list):
                mylist_url = m.get("url")
                self.assertEqual(call.select_from_mylist_url(mylist_url), mc[i])
            mockmw.mylist_info_db.reset_mock()

            mylist_url = m_list[0].get("url")
            mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db, mylist_url)
            mockums.assert_called_once_with(mockmw.window, mockmw.mylist_db)

            # 異常系
            # 引数エラー
            del mockmw.window
            actual = puamitd.run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
