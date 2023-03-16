# coding: utf-8
"""ProcessShowMylistInfo のテスト
"""
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch

from NNMM.Process import ProcessShowMylistInfo


class TestProcessShowMylistInfo(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def MakeMylistDB(self):
        """mylist_db.Select()で取得されるマイリストデータセット
        """
        NUM = 5
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i+1}", "投稿動画", "uploaded", f"投稿者{i+1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i+1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", True if i % 2 == 0 else False] for i in range(NUM)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def ReturnMW(self, showname):
        expect_window_dict = {
            "-INPUT1-": MagicMock()
        }
        expect_values_dict = {
            "-LIST-": [showname]
        }

        r = MagicMock()
        mockwindow = MagicMock()
        mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
        mockwindow.__iter__.side_effect = expect_window_dict.__iter__
        mockwindow.__contains__.side_effect = expect_window_dict.__contains__
        type(r).window = mockwindow
        mockvalues = MagicMock()
        mockvalues.__getitem__.side_effect = expect_values_dict.__getitem__
        mockvalues.__iter__.side_effect = expect_values_dict.__iter__
        mockvalues.__contains__.side_effect = expect_values_dict.__contains__
        type(r).values = mockvalues

        def Returnselect_from_showname(showname):
            m_list = self.MakeMylistDB()
            for m in m_list:
                if m.get("showname") == showname:
                    return [m]
            return []

        r.mylist_db.select_from_showname = Returnselect_from_showname
        return r

    def test_PSMIrun(self):
        """ProcessShowMylistInfoのrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessShowMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessShowMylistInfo.logger.error"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessShowMylistInfo.update_table_pane"))

            psmi = ProcessShowMylistInfo.ProcessShowMylistInfo()

            # 正常系
            m_list = self.MakeMylistDB()
            mylist_url_s = m_list[0]["url"]
            showname_s = m_list[0]["showname"]
            mockmw = self.ReturnMW(showname_s)
            actual = psmi.run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                mc = mockmw.window["-INPUT1-"].mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual(call.update(value=mylist_url_s), mc[0])
                mockmw.window["-INPUT1-"].reset_mock()

                mc = mockmw.values.mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual(call.__getitem__("-LIST-"), mc[0])
                mockmw.values.reset_mock()

                mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db, mylist_url_s)
                mockuts.reset_mock()

            assertMockCall()

            # 新着マークつき
            NEW_MARK = "*:"
            showname_s = NEW_MARK + showname_s
            mockmw = self.ReturnMW(showname_s)
            actual = psmi.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 異常系
            # 引数エラー
            mockmw = self.ReturnMW(showname_s)
            del mockmw.window
            del type(mockmw).window
            actual = psmi.run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
