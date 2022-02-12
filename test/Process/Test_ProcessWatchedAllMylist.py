# coding: utf-8
"""ProcessWatchedAllMylist のテスト
"""

import sys
import unittest
from contextlib import ExitStack
from mock import MagicMock, patch, call
from pathlib import Path

from NNMM.Process import *


class TestProcessWatchedAllMylist(unittest.TestCase):

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
        r = MagicMock()
        r.mylist_db.Select.side_effect = lambda: self.MakeMylistDB()
        return r

    def test_PVPRun(self):
        """ProcessWatchedAllMylist のRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessWatchedAllMylist.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessWatchedAllMylist.logger.error"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessWatchedAllMylist.UpdateMylistShow"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessWatchedAllMylist.UpdateTableShow"))

            pwam = ProcessWatchedAllMylist.ProcessWatchedAllMylist()

            # 正常系
            mockmw = self.ReturnMW()
            actual = pwam.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                m_list = self.MakeMylistDB()
                records = [m for m in m_list if m["is_include_new"]]
                all_num = len(records)

                index = 1
                mc = mockmw.mock_calls
                self.assertEqual(1 + all_num * 2, len(mc))
                self.assertEqual(call.mylist_db.Select(), mc[0])
                for i, record in enumerate(records):
                    mylist_url = record.get("url")
                    self.assertEqual(call.mylist_info_db.UpdateStatusInMylist(mylist_url, ""), mc[index])
                    self.assertEqual(call.mylist_db.UpdateIncludeFlag(mylist_url, False), mc[index + 1])
                    index += 2
                mockmw.reset_mock()

                mockums.assert_called_once_with(mockmw.window, mockmw.mylist_db)
                mockums.reset_mock()
                mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db)
                mockuts.reset_mock()

            assertMockCall()

            # 異常系
            # 引数エラー
            del mockmw.window
            actual = pwam.Run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
