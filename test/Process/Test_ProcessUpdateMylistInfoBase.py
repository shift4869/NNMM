# coding: utf-8
"""ProcessUpdateMylistInfoBase のテスト
"""
import sys
import unittest
from contextlib import ExitStack

from mock import AsyncMock, MagicMock, call, patch

from NNMM.Process import ProcessUpdateMylistInfoBase


class ConcreteProcessUpdateMylistInfo(ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        """テスト用具体化クラス
        """
        super().__init__(True, False, "テスト用具体化クラス")

        self.L_KIND = "Concrete Kind"
        self.E_DONE = "Concrete Event Key"

    def MakeMylistDB(self, num: int = 5) -> list[dict]:
        """mylist_db.Select()で取得されるマイリストデータセット
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

    def GetTargetMylist(self) -> list[dict]:
        m_list = self.MakeMylistDB()
        return m_list


class TestProcessUpdateMylistInfoBase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def MakeMylistDB(self, num: int = 5) -> list[dict]:
        """mylist_db.Select()で取得されるマイリストデータセット
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

    def MakeMylistInfoDB(self, num: int = 5) -> list[dict]:
        """mylist_info_db.Select()で取得される動画情報データセット
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

    def test_PUAMIRun(self):
        """ProcessUpdateMylistInfoBaseのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))
            mockthread = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.threading.Thread"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            mockmw = MagicMock()
            actual = puami.Run(mockmw)
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
            self.assertEqual(call(target=puami.UpdateMylistInfoThread, args=(), daemon=True), mc[0])
            self.assertEqual(call().start(), mc[1])
            mockthread.reset_mock()

            # 異常系
            # 引数エラー
            mockmw = MagicMock()
            del mockmw.window
            actual = puami.Run(mockmw)
            self.assertEqual(-1, actual)

    def test_UpdateMylistInfoThread(self):
        """UpdateMylistInfoThreadをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))
            mocktime = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.time"))
            mockgfl = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase.GetFunctionList"))
            mockgpvl = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase.GetPrevVideoLists"))
            mockgmie = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase.GetMylistInfoExecute"))
            mockumie = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase.UpdateMylistInfoExecute"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            mocktime.time.return_value = 0
            puami.window = MagicMock()
            actual = puami.UpdateMylistInfoThread()
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            mc = puami.window.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.write_event_value(puami.E_DONE, ""), mc[0])
            puami.window.reset_mock()

            m_list = puami.GetTargetMylist()
            mockgfl.assert_called_once_with(m_list)
            mockgpvl.assert_called_once_with(m_list)
            mockgmie.assert_called_once_with(mockgfl.return_value, m_list)
            mockumie.assert_called_once_with(m_list, mockgpvl.return_value, mockgmie.return_value)

            # 更新対象が空だった
            puami.GetTargetMylist = lambda: []
            actual = puami.UpdateMylistInfoThread()
            self.assertEqual(1, actual)

            mc = puami.window.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.write_event_value(puami.E_DONE, ""), mc[0])
            puami.window.reset_mock()

            # 異常系
            # 属性エラー
            del puami.window
            actual = puami.UpdateMylistInfoThread()
            self.assertEqual(-1, actual)

    def test_GetFunctionList(self):
        """GetFunctionListをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))
            mockagmi = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.VideoInfoHtmlFetcher.fetch_videoinfo"))
            mockagmilw = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.VideoInfoRssFetcher.fetch_videoinfo"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            prev_video_list = self.MakeMylistInfoDB(num=3)

            def ReturnSelectFromMylistURL(mylist_url):
                res = []
                for record in prev_video_list:
                    if record.get("mylist_url") == mylist_url:
                        res.append(record)
                return res

            r = MagicMock()
            r.SelectFromMylistURL = ReturnSelectFromMylistURL
            puami.mylist_info_db = r

            m_list = self.MakeMylistDB(num=5)
            expect = [mockagmilw for i in range(3)] + [mockagmi for i in range(2)]
            actual = puami.GetFunctionList(m_list)
            self.assertEqual(expect, actual)

            # 引数に空リスト指定時
            actual = puami.GetFunctionList([])
            self.assertEqual([], actual)

            # 異常系
            # 属性エラー
            del puami.mylist_info_db
            actual = puami.GetFunctionList(m_list)
            self.assertEqual([], actual)

    def test_GetPrevVideoLists(self):
        """GetPrevVideoListsをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            prev_video_list = self.MakeMylistInfoDB()

            def ReturnSelectFromMylistURL(mylist_url):
                res = []
                for record in prev_video_list:
                    if record.get("mylist_url") == mylist_url:
                        res.append(record)
                return res

            r = MagicMock()
            r.SelectFromMylistURL = ReturnSelectFromMylistURL
            puami.mylist_info_db = r

            m_list = self.MakeMylistDB()
            expect = [ReturnSelectFromMylistURL(m["url"]) for m in m_list]
            actual = puami.GetPrevVideoLists(m_list)
            self.assertEqual(expect, actual)

            # 引数に空リスト指定時
            actual = puami.GetPrevVideoLists([])
            self.assertEqual([], actual)

            # 異常系
            # 属性エラー
            del puami.mylist_info_db
            actual = puami.GetPrevVideoLists(m_list)
            self.assertEqual([], actual)

    def test_GetMylistInfoExecute(self):
        """GetMylistInfoExecuteをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))
            mocktpe = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ThreadPoolExecutor"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            NUM = 5
            m_list = self.MakeMylistDB(NUM)
            f_list = [MagicMock() for _ in range(NUM)]

            r = MagicMock()
            r.submit.side_effect = lambda f, func, mylist_url, all_index_num: MagicMock()
            mocktpe.return_value.__enter__.side_effect = lambda: r

            expect = []
            for func, record in zip(f_list, m_list):
                mylist_url = record.get("url")
                expect.append(mylist_url)

            actual = puami.GetMylistInfoExecute(f_list, m_list)
            self.assertEqual(expect, [a[0] for a in actual])

            # 実行後呼び出し確認
            mc = r.submit.mock_calls
            self.assertEqual(NUM, len(mc))
            for mc_e, func, record in zip(mc, f_list, m_list):
                mylist_url = record.get("url")
                self.assertEqual(call(puami.GetMylistInfoWorker, func, mylist_url, NUM), mc_e)
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
            actual = puami.GetMylistInfoExecute(f_list, m_list)
            self.assertEqual([], actual)

            # マイリストURLが空
            m_list = [{"url": ""} for _ in range(NUM)]
            f_list = [MagicMock() for _ in range(NUM)]
            actual = puami.GetMylistInfoExecute(f_list, m_list)
            self.assertEqual([], actual)

            # メソッドリストとマイリストレコードリストの大きさが異なる
            m_list = self.MakeMylistDB(NUM)
            f_list = [MagicMock() for _ in range(NUM - 1)]
            actual = puami.GetMylistInfoExecute(f_list, m_list)
            self.assertEqual([], actual)

    def test_GetMylistInfoWorker(self):
        """GetMylistInfoWorker をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            puami.window = MagicMock()
            NUM = 5
            func = AsyncMock()
            func.side_effect = lambda url: [url]
            mylist_url = "https://www.nicovideo.jp/user/10000001/video"
            expect = [mylist_url]
            actual = puami.GetMylistInfoWorker(func, mylist_url, NUM)
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
            actual = puami.GetMylistInfoWorker(func, mylist_url, NUM)
            self.assertEqual([], actual)

            # マイリストURLが空
            func = AsyncMock()
            mylist_url = ""
            actual = puami.GetMylistInfoWorker(func, mylist_url, NUM)
            self.assertEqual([], actual)

            # 属性エラー
            del puami.window
            actual = puami.GetMylistInfoWorker(func, mylist_url, NUM)
            self.assertEqual([], actual)

    def test_UpdateMylistInfoExecute(self):
        """UpdateMylistInfoExecute をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))
            mocktpe = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.ThreadPoolExecutor"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            NUM = 5
            m_list = self.MakeMylistDB(NUM)
            p_list = []
            n_list = []

            def ReturnSelectFromMylistURL(mylist_url):
                res = []
                records = self.MakeMylistInfoDB(NUM)
                for record in records:
                    if record.get("mylist_url") == mylist_url:
                        res.append(record)
                return res

            expect = []
            for m in m_list:
                mylist_url = m.get("url")
                expect.append(mylist_url)
                p_list.append(ReturnSelectFromMylistURL(mylist_url))
                n_list.append(ReturnSelectFromMylistURL(mylist_url))

            r = MagicMock()
            r.submit.side_effect = lambda f, m, p, n: MagicMock()
            mocktpe.return_value.__enter__.side_effect = lambda: r

            actual = puami.UpdateMylistInfoExecute(m_list, p_list, n_list)
            self.assertEqual(expect, [a[0] for a in actual])

            # 実行後呼び出し確認
            mc = r.submit.mock_calls
            self.assertEqual(NUM, len(mc))
            for mc_e, m, p in zip(mc, m_list, p_list):
                self.assertEqual(call(puami.UpdateMylistInfoWorker, m, p, n_list), mc_e)
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
            actual = puami.UpdateMylistInfoExecute(m_list, p_list, n_list)
            self.assertEqual([], actual)

    def test_UpdateMylistInfoWorker(self):
        """UpdateMylistInfoWorker をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))
            mockgdt = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.GetNowDatetime"))
            mockmdb = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.MylistDBController"))
            mockmidb = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.MylistInfoDBController"))

            puami = ConcreteProcessUpdateMylistInfo()

            # 正常系
            dst = "2022-02-08 01:00:01"
            mockgdt.side_effect = lambda: dst
            NUM = 5
            m_list = self.MakeMylistDB()
            m_record = m_list[0]
            p_list = []
            n_list = []

            def ReturnSelectFromMylistURL(mylist_url):
                res = []
                records = self.MakeMylistInfoDB(NUM)
                for i, record in enumerate(records):
                    if record.get("mylist_url") == mylist_url:
                        record["status"] = "未視聴" if i % 2 == 0 else ""
                        record["id"] = record["no"]
                        del record["no"]
                        res.append(record)
                return res

            def ReturnGetMylistInfo(mylist_url):
                res = []
                records = self.MakeMylistInfoDB(NUM)
                for i, record in enumerate(records):
                    if record.get("mylist_url") == mylist_url:
                        record["status"] = "未視聴" if i % 2 == 0 else ""
                        res.append(record)
                return res

            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(ReturnSelectFromMylistURL(mylist_url))
                n_list.append((mylist_url, ReturnGetMylistInfo(mylist_url)))
            p = p_list[0]

            puami.window = MagicMock()
            puami.mylist_db = MagicMock()
            puami.mylist_info_db = MagicMock()
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
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
                        self.assertEqual(call().UpdateUsername(mylist_url, now_username), mc_i[i])
                        i = i + 1
                        self.assertEqual(call().UpdateUsernameInMylist(mylist_url, now_username), mc_j[j])
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

                self.assertEqual(call().UpsertFromList(records), mc_j[j])
                j = j + 1

                self.assertEqual(call().UpdateCheckedAt(mylist_url, dst), mc_i[i])
                i = i + 1
                if add_new_video_flag:
                    self.assertEqual(call().UpdateUpdatedAt(mylist_url, dst), mc_i[i])
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
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
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
            # actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            # self.assertEqual(0, actual)
            # self.assertEqual(1, puami.done_count)
            # assertMockCall()
            # puami.done_count = 0

            # マイリストに登録されている動画情報の件数が0
            mylist_url = m_record.get("url")
            n_list[0] = (mylist_url, [])
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(1, actual)

            # 異常系
            # mylist_info_dbに格納するために必要なキーが存在しない
            n_list = [(m.get("url"), ReturnGetMylistInfo(m.get("url"))) for m in m_list]
            for n in n_list:
                if n[0] == mylist_url:
                    for nr in n[1]:
                        del nr["title"]
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 動画情報のリストのリストにマイリストの重複が含まれている
            n_list[0] = (mylist_url, n_list[1][1])
            n_list[1] = (mylist_url, n_list[1][1])
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストに想定外のキーがある
            n_list = [(m.get("url"), ReturnGetMylistInfo(m.get("url"))) for m in m_list]
            n_list[0][1][0]["不正なキー"] = "不正な値"
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストの一部がリストでない
            n_list[0] = (mylist_url, "不正な値")
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストの一部のマイリストURLが空
            n_list[0] = ("", n_list[1][1])
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが2重空リスト
            actual = puami.UpdateMylistInfoWorker(m_record, p, [[]])
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが空リスト
            actual = puami.UpdateMylistInfoWorker(m_record, p, [])
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストがNone
            actual = puami.UpdateMylistInfoWorker(m_record, p, None)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが文字列
            actual = puami.UpdateMylistInfoWorker(m_record, p, "不正な引数")
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストに想定外のキーがある
            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(ReturnSelectFromMylistURL(mylist_url))
                n_list.append((mylist_url, ReturnGetMylistInfo(mylist_url)))
            p = p_list[0]
            p[0]["不正なキー"] = "不正な値"
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが空リスト
            actual = puami.UpdateMylistInfoWorker(m_record, [], n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストがNone
            actual = puami.UpdateMylistInfoWorker(m_record, None, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが文字列
            actual = puami.UpdateMylistInfoWorker(m_record, "不正な引数", n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトのurlが空
            del p[0]["不正なキー"]
            actual = puami.UpdateMylistInfoWorker({"url": ""}, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが空辞書
            actual = puami.UpdateMylistInfoWorker({}, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトがNone
            actual = puami.UpdateMylistInfoWorker(None, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが文字列
            actual = puami.UpdateMylistInfoWorker("不正な引数", p, n_list)
            self.assertEqual(-1, actual)

    def test_UAMITPRun(self):
        """UpdateAllMylistInfoThreadProgress のRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.logger.error"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.UpdateTableShow"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.UpdateMylistShow"))
            # mockiminv = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfoBase.IsMylistIncludeNewVideo"))

            puamitd = ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoThreadDoneBase()

            # 正常系
            def ReturnSelectFromMylistURL(mylist_url):
                res = []
                records = self.MakeMylistInfoDB(num=5)
                for i, record in enumerate(records):
                    if record.get("mylist_url") == mylist_url:
                        record["status"] = "未視聴" if i % 2 == 0 and i < 15 else ""
                        res.append(record)
                return res

            m_list = self.MakeMylistDB()
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
            mockmdb.Select.side_effect = lambda: self.MakeMylistDB()
            mockmw.mylist_db = mockmdb
            mockmidb = MagicMock()
            mockmidb.SelectFromMylistURL.side_effect = ReturnSelectFromMylistURL
            mockmw.mylist_info_db = mockmidb
            actual = puamitd.Run(mockmw)
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
            self.assertEqual(call.Select(), mc[0])
            for i, m in enumerate(m_list[:3]):
                mylist_url = m.get("url")
                self.assertEqual(call.UpdateIncludeFlag(mylist_url, True), mc[i + 1])
            mockmw.mylist_db.reset_mock()

            mc = mockmw.mylist_info_db.mock_calls
            self.assertEqual(5, len(mc))
            for i, m in enumerate(m_list):
                mylist_url = m.get("url")
                self.assertEqual(call.SelectFromMylistURL(mylist_url), mc[i])
            mockmw.mylist_info_db.reset_mock()

            mylist_url = m_list[0].get("url")
            mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db, mylist_url)
            mockums.assert_called_once_with(mockmw.window, mockmw.mylist_db)

            # 異常系
            # 引数エラー
            del mockmw.window
            actual = puamitd.Run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
