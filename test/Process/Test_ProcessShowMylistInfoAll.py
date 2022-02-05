# coding: utf-8
"""ProcessShowMylistInfoAll のテスト
"""

import re
import sys
import unittest
from contextlib import ExitStack
from mock import MagicMock, patch, call

from NNMM.Process import *


class TestProcessShowMylistInfoAll(unittest.TestCase):

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

    def MakeMylistInfoDB(self, mylist_url):
        """mylist_info_db.SelectFromMylistURL(mylist_url)で取得されるマイリストデータセット
        """
        NUM = 5
        res = []

        m = -1
        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        if re.search(pattern, mylist_url):
            m = int(re.search(pattern, mylist_url)[1])
        if m == -1:
            return []

        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded", "video_url", "mylist_url"]
        table_rows = [[i, f"sm{m}000000{i+1}", f"動画タイトル{m}_{i+1}", f"投稿者{m}", "",
                       "2022-02-01 02:30:00",
                       f"https://www.nicovideo.jp/watch/sm{m}000000{i+1}",
                       f"https://www.nicovideo.jp/user/1000000{m}/video"] for i in range(NUM)]

        for rows in table_rows:
            d = {}
            for r, c in zip(rows, table_cols):
                d[c] = r
            res.append(d)
        return res

    def MakeTableRecords(self, mylist_url):
        """表示中の動画テーブルから取得されるレコードセット
        """
        NUM = 5
        m = -1
        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        if re.search(pattern, mylist_url):
            m = int(re.search(pattern, mylist_url)[1])
        if m == -1:
            return []

        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL"]
        records = [[i, f"sm{m}000000{i+1}", f"動画タイトル{m}_{i+1}", f"投稿者{m}", "未視聴", "2022-01-28 22:00:00",
                    f"https://www.nicovideo.jp/watch/sm{m}000000{i+1}", mylist_url] for i in range(NUM)]
        return records

    def ReturnMW(self):
        expect_window_dict = {
            "-INPUT1-": MagicMock()
        }
        expect_values_dict = {
            "-LIST-": []
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

        def ReturnSelectFromShowname(showname):
            m_list = self.MakeMylistDB()
            for m in m_list:
                if m.get("showname") == showname:
                    return [m]
            return []

        r.mylist_db.SelectFromShowname = ReturnSelectFromShowname
        return r

    def test_PSMIARun(self):
        """ProcessShowMylistInfoAllのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessShowMylistInfoAll.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessShowMylistInfoAll.logger.error"))

            psmia = ProcessShowMylistInfoAll.ProcessShowMylistInfoAll()

            # 正常系
            mockmw = self.ReturnMW()
            actual = psmia.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            mc = mockmw.window["-INPUT1-"].mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.update(), mc[0])
            mockmw.window["-INPUT1-"].reset_mock()

            mc = mockmw.values.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.__getitem__("-LIST-"), mc[0])
            mockmw.values.reset_mock()

            # 異常系
            # 引数エラー
            mockmw = self.ReturnMW()
            del mockmw.window
            del type(mockmw).window
            actual = psmia.Run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
