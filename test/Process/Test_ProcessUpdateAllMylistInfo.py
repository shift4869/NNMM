# coding: utf-8
"""ProcessUpdateAllMylistInfo のテスト
"""

import re
import sys
import unittest
from contextlib import ExitStack
from mock import MagicMock, AsyncMock, patch, call
from sqlalchemy import all_

from NNMM.Process import *


class TestProcessUpdateAllMylistInfo(unittest.TestCase):

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
                           "投稿日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded_at", "video_url", "mylist_url"]
        n = 0
        for k in range(num):
            table_rows = [[n, f"sm{k+1}000000{i+1}", f"動画タイトル{k+1}_{i+1}", f"投稿者{k+1}", "",
                           f"2022-02-01 0{k+1}:00:0{i+1}",
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
        """ProcessUpdateAllMylistInfoのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))
            mockthread = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.threading.Thread"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

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
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))
            mocktime = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.time"))
            mockgtm = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo.GetTargetMylist"))
            mockgfl = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo.GetFunctionList"))
            mockgpvl = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo.GetPrevVideoLists"))
            mockgmie = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo.GetMylistInfoExecute"))
            mockumie = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo.UpdateMylistInfoExecute"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

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

            mockgtm.assert_called_once_with()
            mockgfl.assert_called_once_with(mockgtm.return_value)
            mockgpvl.assert_called_once_with(mockgtm.return_value)
            mockgmie.assert_called_once_with(mockgfl.return_value, mockgtm.return_value)
            mockumie.assert_called_once_with(mockgtm.return_value, mockgpvl.return_value, mockgmie.return_value)

            # 更新対象が空だった
            mockgtm.return_value = []
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

    def test_GetTargetMylist(self):
        """GetTargetMylistをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

            # 正常系
            expect = ["TargetMylist list"]
            r = MagicMock()
            r.Select = lambda: expect
            puami.mylist_db = r
            actual = puami.GetTargetMylist()
            self.assertEqual(expect, actual)

            # 異常系
            # 属性エラー
            del puami.mylist_db
            actual = puami.GetTargetMylist()
            self.assertEqual([], actual)

    def test_GetFunctionList(self):
        """GetFunctionListをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))
            mockagmi = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.GetMyListInfo.AsyncGetMyListInfo"))
            mockagmilw = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.GetMyListInfo.AsyncGetMyListInfoLightWeight"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

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
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

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
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))
            mocktpe = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.ThreadPoolExecutor"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

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
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

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
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))
            mocktpe = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.ThreadPoolExecutor"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

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
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))
            mockgdt = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.GetNowDatetime"))
            mockmdb = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.MylistDBController"))
            mockmidb = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.MylistInfoDBController"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

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
                        record["uploaded"] = record["uploaded_at"]
                        del record["uploaded_at"]
                        res.append(record)
                return res

            for m in m_list:
                mylist_url = m.get("url")
                p_list.append(ReturnSelectFromMylistURL(mylist_url))
                n_list.append((mylist_url, ReturnSelectFromMylistURL(mylist_url)))
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
                        "uploaded_at": m["uploaded"],
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
            mylist_url = m_record.get("url")
            for n in n_list:
                if n[0] == mylist_url:
                    for nr in n[1]:
                        nr["username"] = "新しい投稿者名1"
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(0, actual)
            self.assertEqual(1, puami.done_count)
            assertMockCall()
            puami.done_count = 0

            # 異常系
            # mylist_info_dbに格納するために必要なキーが存在しない
            for n in n_list:
                if n[0] == mylist_url:
                    for nr in n[1]:
                        del nr["title"]
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # マイリストに登録されている動画情報の件数が0
            n_list[0] = (mylist_url, [])
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：マイリストレコードオブジェクトが空
            actual = puami.UpdateMylistInfoWorker(None, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストが不正
            # actual = puami.UpdateMylistInfoWorker(m_record, None, n_list)
            # self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが重複している
            n_list[0] = (mylist_url, n_list[1][1])
            n_list[1] = (mylist_url, n_list[1][1])
            actual = puami.UpdateMylistInfoWorker(m_record, p, n_list)
            self.assertEqual(-1, actual)

            # 引数が不正：動画情報のリストのリストが不正
            # actual = puami.UpdateMylistInfoWorker(m_record, p, None)
            # actual = puami.UpdateMylistInfoWorker(m_record, p, [])
            # self.assertEqual(-1, actual)
            pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
