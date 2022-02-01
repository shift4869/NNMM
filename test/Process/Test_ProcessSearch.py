# coding: utf-8
"""ProcessSearch のテスト
"""

import random
import re
import sys
import unittest
import warnings
from contextlib import ExitStack
from mock import MagicMock, patch, call

from NNMM.Process import *


class TestProcessSearch(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def MakeMylistShownameList(self):
        """表示マイリストデータセット
        """
        NUM = 5
        res = [f"投稿者{i+1}" for i in range(NUM)]
        return res

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

    def test_PNWRun(self):
        """ProcessSearchのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.error"))
            mocksgpgt = stack.enter_context(patch("NNMM.Process.ProcessSearch.sg.popup_get_text"))

            pms = ProcessSearch.ProcessMylistSearch()

            # 正常系
            def ReturnMW():
                def ReturnWindowList():
                    r_wl = MagicMock()
                    r_wl.get_indexes.return_value = [1]
                    r_wl.Values = self.MakeMylistShownameList()
                    return r_wl

                expect_window_dict = {
                    "-LIST-": ReturnWindowList(),
                    "-INPUT2-": MagicMock()
                }

                r = MagicMock()
                mockwindow = MagicMock()
                mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
                mockwindow.__iter__.side_effect = expect_window_dict.__iter__
                mockwindow.__contains__.side_effect = expect_window_dict.__contains__
                type(r).window = mockwindow

                r.mylist_db.Select.return_value = self.MakeMylistDB()
                return r

            mockmw = ReturnMW()
            mocksgpgt.return_value = "投稿者1"
            actual = pms.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                index = 1
                pattern = mocksgpgt.return_value
                NEW_MARK = "*:"
                m_list = self.MakeMylistDB()
                include_new_index_list = []
                match_index_list = []
                for i, m in enumerate(m_list):
                    if m["is_include_new"]:
                        m["showname"] = NEW_MARK + m["showname"]
                        include_new_index_list.append(i)
                    if re.search(pattern, m["showname"]):
                        match_index_list.append(i)
                        index = i  # 更新後にスクロールするインデックスを更新
                list_data = [m["showname"] for m in m_list]

                mc = mockmw.window["-LIST-"].mock_calls
                self.assertEqual(3 + len(include_new_index_list) + len(match_index_list) + 2, len(mc))
                self.assertEqual(call.get_indexes(), mc[0])
                self.assertEqual(call.get_indexes(), mc[1])
                self.assertEqual(call.update(values=list_data), mc[2])
                for c, i in enumerate(include_new_index_list):
                    self.assertEqual(call.Widget.itemconfig(i, fg="black", bg="light pink"), mc[3 + c])
                for c, i in enumerate(match_index_list):
                    self.assertEqual(call.Widget.itemconfig(i, fg="black", bg="light goldenrod"), mc[3 + len(include_new_index_list) + c])
                self.assertEqual(call.Widget.see(index), mc[-2])
                self.assertEqual(call.update(set_to_index=index), mc[-1])
                mockmw.window["-LIST-"].reset_mock()

                mc = mockmw.window["-INPUT2-"].mock_calls
                self.assertEqual(1, len(mc))
                if len(match_index_list) > 0:
                    self.assertEqual(call.update(value=f"{len(match_index_list)}件ヒット！"), mc[0])
                else:
                    self.assertEqual(call.update(value="該当なし"), mc[0])
                mockmw.window["-INPUT2-"].reset_mock()

                mocksgpgt.assert_called_once_with("マイリスト名検索（正規表現可）")
                mocksgpgt.reset_mock()

                mc = mockmw.mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual(call.mylist_db.Select(), mc[0])
                mockmw.reset_mock()

            assertMockCall()

            # 複数ヒット
            mockmw = ReturnMW()
            mocksgpgt.return_value = "投稿者"
            actual = pms.Run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 1件もヒットしなかった
            mockmw = ReturnMW()
            mocksgpgt.return_value = "ヒットしない検索条件"
            actual = pms.Run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 異常系
            # 検索条件が空白
            mockmw = ReturnMW()
            mocksgpgt.return_value = ""
            actual = pms.Run(mockmw)
            self.assertEqual(-1, actual)

            # 引数エラー
            mockmw = ReturnMW()
            del mockmw.window
            del type(mockmw).window
            actual = pms.Run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
