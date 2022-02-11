# coding: utf-8
"""ProcessUpdateMylistInfo のテスト
"""

import sys
import unittest
from contextlib import ExitStack
from mock import MagicMock, patch, call

from NNMM.Process import *


class TestProcessUpdateMylistInfo(unittest.TestCase):

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

    def MakeMylistInfoDB(self, mylist_url, num: int = 5) -> list[dict]:
        """mylist_info_db.SelectFromMylistURL()で取得される動画情報データセット
        """
        res = []
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded_at", "video_url", "mylist_url"]
        n = 0
        for k in range(num):
            table_rows = [[n + i, f"sm{k+1}000000{i+1}", f"動画タイトル{k+1}_{i+1}", f"投稿者{k+1}",
                           "未視聴" if i % 2 == 0 else "",
                           f"2022-02-01 0{k+1}:00:0{i+1}",
                           f"https://www.nicovideo.jp/watch/sm{k+1}000000{i+1}",
                           f"https://www.nicovideo.jp/user/1000000{k+1}/video"] for i in range(num)]
            n = n + 1 + num

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return [r for r in res if r["mylist_url"] == mylist_url]

    def test_PUMIInit(self):
        """ProcessUpdateMylistInfo の初期状態をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfo.logger.error"))

            pumi = ProcessUpdateMylistInfo.ProcessUpdateMylistInfo()

            self.assertEqual("Mylist", pumi.L_KIND)
            self.assertEqual("-UPDATE_THREAD_DONE-", pumi.E_DONE)

    def test_PUMIGetTargetMylist(self):
        """GetTargetMylist をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfo.logger.error"))

            pumi = ProcessUpdateMylistInfo.ProcessUpdateMylistInfo()

            # 正常系
            m_list = self.MakeMylistDB()
            mylist_url = m_list[0].get("url")
            expect_values_dict = {
                "-INPUT1-": mylist_url
            }

            def ReturnSelectFromURL(url):
                return [m for m in m_list if m["url"] == url]

            mockmw = MagicMock()
            mockvalues = MagicMock()
            mockvalues.__getitem__.side_effect = expect_values_dict.__getitem__
            mockvalues.__iter__.side_effect = expect_values_dict.__iter__
            mockvalues.__contains__.side_effect = expect_values_dict.__contains__
            mockmw.values = mockvalues
            mockmdb = MagicMock()
            mockmdb.SelectFromURL.side_effect = lambda url: ReturnSelectFromURL(url)
            mockmw.mylist_db = mockmdb

            pumi.values = mockmw.values
            pumi.mylist_db = mockmw.mylist_db
            expect = [m_list[0]]
            actual = pumi.GetTargetMylist()
            self.assertEqual(expect, actual)

            # 実行後呼び出し確認
            mc = mockmw.values.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.__getitem__("-INPUT1-"), mc[0])
            mockmw.values.reset_mock()

            mc = mockmw.mylist_db.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.SelectFromURL(mylist_url), mc[0])
            mockmw.mylist_db.reset_mock()

            # 異常系
            # 指定マイリストURLが不正
            expect_values_dict["-INPUT1-"] = "不正なマイリストURL"
            actual = pumi.GetTargetMylist()
            self.assertEqual([], actual)

            # 指定マイリストURLが空
            expect_values_dict["-INPUT1-"] = ""
            actual = pumi.GetTargetMylist()
            self.assertEqual([], actual)

            # 属性エラー
            del pumi.values
            actual = pumi.GetTargetMylist()
            self.assertEqual([], actual)

    def test_PUMITDRun(self):
        """ProcessUpdateMylistInfoThreadDone のRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfo.logger.error"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfo.UpdateTableShow"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessUpdateMylistInfo.UpdateMylistShow"))

            pumitd = ProcessUpdateMylistInfo.ProcessUpdateMylistInfoThreadDone()

            # 正常系
            m_list = self.MakeMylistDB()
            mylist_url = m_list[0].get("url")
            table_list = self.MakeMylistInfoDB(mylist_url)
            records = []
            for record in table_list:
                records.append(list(record.values()))
            r = MagicMock()
            r.Values = records
            expect_window_dict = {
                "-TABLE-": r,
                "-INPUT2-": MagicMock()
            }
            expect_values_dict = {
                "-INPUT1-": mylist_url
            }

            mockmw = MagicMock()
            mockwindow = MagicMock()
            mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
            mockwindow.__iter__.side_effect = expect_window_dict.__iter__
            mockwindow.__contains__.side_effect = expect_window_dict.__contains__
            mockmw.window = mockwindow
            mockvalues = MagicMock()
            mockvalues.__getitem__.side_effect = expect_values_dict.__getitem__
            mockvalues.__iter__.side_effect = expect_values_dict.__iter__
            mockvalues.__contains__.side_effect = expect_values_dict.__contains__
            mockmw.values = mockvalues

            actual = pumitd.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            mc = mockmw.window.mock_calls
            self.assertEqual(3, len(mc))
            self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
            self.assertEqual(call.refresh(), mc[1])
            self.assertEqual(call.__getitem__("-TABLE-"), mc[2])
            mockmw.window.reset_mock()

            mc = mockmw.values.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.__getitem__("-INPUT1-"), mc[0])
            mockmw.values.reset_mock()

            mc = mockmw.mock_calls
            self.assertEqual(5, len(mc))
            self.assertEqual(call.window.__getitem__("-INPUT2-"), mc[0])
            self.assertEqual(call.values.__getitem__("-INPUT1-"), mc[1])
            self.assertEqual(call.window.refresh(), mc[2])
            self.assertEqual(call.window.__getitem__("-TABLE-"), mc[3])
            self.assertEqual(call.mylist_db.UpdateIncludeFlag(mylist_url, True), mc[4])
            mockmw.reset_mock()

            mockuts.assert_called_once_with(pumitd.window, pumitd.mylist_db, pumitd.mylist_info_db, mylist_url)
            mockums.assert_called_once_with(pumitd.window, pumitd.mylist_db)

            # 異常系
            # 引数エラー
            del mockmw.window
            actual = pumitd.Run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
