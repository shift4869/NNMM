# coding: utf-8
"""ProcessWatchedMylist のテスト
"""

import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch

from NNMM.Process import ProcessWatchedMylist


class TestProcessWatchedMylist(unittest.TestCase):

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
                 "15分", i % 2 == 0] for i in range(num)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def ReturnMW(self):
        m_list = self.MakeMylistDB()
        showname = m_list[0]["showname"]

        r = MagicMock()

        expect_values_dict = {
            "-LIST-": [showname]
        }

        mockvalues = MagicMock()
        mockvalues.__getitem__.side_effect = expect_values_dict.__getitem__
        mockvalues.__iter__.side_effect = expect_values_dict.__iter__
        mockvalues.__contains__.side_effect = expect_values_dict.__contains__
        r.values = mockvalues

        def Returnselect_from_showname(v):
            return [m for m in m_list if m["showname"] == v]

        r.mylist_db.select_from_showname.side_effect = Returnselect_from_showname
        return r

    def test_PVPrun(self):
        """ProcessWatchedMylist のrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessWatchedMylist.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessWatchedMylist.logger.error"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessWatchedMylist.UpdateMylistShow"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessWatchedMylist.UpdateTableShow"))

            pwm = ProcessWatchedMylist.ProcessWatchedMylist()

            # 正常系
            mockmw = self.ReturnMW()
            actual = pwm.run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                m_list = self.MakeMylistDB()
                showname = m_list[0]["showname"]
                mylist_url = m_list[0]["url"]

                mc = mockmw.mock_calls
                self.assertEqual(5, len(mc))
                self.assertEqual(call.values.__getitem__("-LIST-"), mc[0])
                self.assertEqual(call.values.__getitem__("-LIST-"), mc[1])
                self.assertEqual(call.mylist_db.select_from_showname(showname), mc[2])
                self.assertEqual(call.mylist_info_db.update_status_in_mylist(mylist_url, ""), mc[3])
                self.assertEqual(call.mylist_db.update_include_flag(mylist_url, False), mc[4])
                mockmw.reset_mock()

                mockums.assert_called_once_with(mockmw.window, mockmw.mylist_db)
                mockums.reset_mock()
                mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db)
                mockuts.reset_mock()

            assertMockCall()

            # マイリストに新着フラグあり
            NEW_MARK = "*:"
            mockmw = self.ReturnMW()
            mockmw.values["-LIST-"][0] = NEW_MARK + mockmw.values["-LIST-"][0]
            mockmw.reset_mock()
            actual = pwm.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 異常系
            # マイリストが選択されていない
            mockmw = self.ReturnMW()
            expect_values_dict = {
                "-LIST-": []
            }
            mockvalues = MagicMock()
            mockvalues.__getitem__.side_effect = expect_values_dict.__getitem__
            mockvalues.__iter__.side_effect = expect_values_dict.__iter__
            mockvalues.__contains__.side_effect = expect_values_dict.__contains__
            mockmw.values = mockvalues
            actual = pwm.run(mockmw)
            self.assertEqual(-1, actual)

            # 引数エラー
            del mockmw.values
            actual = pwm.run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
