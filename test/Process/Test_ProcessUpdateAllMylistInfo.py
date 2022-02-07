# coding: utf-8
"""ProcessUpdateAllMylistInfo のテスト
"""

import re
import sys
import unittest
from contextlib import ExitStack
from mock import MagicMock, AsyncMock, patch, call

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


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
