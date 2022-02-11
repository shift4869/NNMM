# coding: utf-8
"""ProcessVideoPlay のテスト
"""

import sys
import unittest
from contextlib import ExitStack
from mock import MagicMock, patch, call
from pathlib import Path

from NNMM.Process import *


class TestProcessVideoPlay(unittest.TestCase):

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
                 "15分", False] for i in range(num)]

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

    def ReturnMW(self):
        m_list = self.MakeMylistDB()
        mylist_url = m_list[0]["url"]

        def ReturnValues():
            r_wt = MagicMock()
            table_list = self.MakeMylistInfoDB(mylist_url)
            
            r_wt.Values = [list(r.values()) for r in table_list]
            return r_wt

        expect_window_dict = {
            "-TABLE-": ReturnValues()
        }
        expect_values_dict = {
            "-TABLE-": [0]
        }

        r = MagicMock()
        mockwindow = MagicMock()
        mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
        mockwindow.__iter__.side_effect = expect_window_dict.__iter__
        mockwindow.__contains__.side_effect = expect_window_dict.__contains__
        r.window = mockwindow
        mockvalues = MagicMock()
        mockvalues.__getitem__.side_effect = expect_values_dict.__getitem__
        mockvalues.__iter__.side_effect = expect_values_dict.__iter__
        mockvalues.__contains__.side_effect = expect_values_dict.__contains__
        r.values = mockvalues

        def ReturnSelectFromVideoID(video_id):
            table_list = self.MakeMylistInfoDB(mylist_url)
            return [r for r in table_list if r["video_id"] == video_id]

        r.mylist_info_db.SelectFromVideoID = ReturnSelectFromVideoID
        return r

    def test_PVPRun(self):
        """ProcessVideoPlay のRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessVideoPlay.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessVideoPlay.logger.error"))
            mockcmd = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig"))
            mockcecs = stack.enter_context(patch("NNMM.Process.ProcessVideoPlay.sg.execute_command_subprocess"))
            mockpok = stack.enter_context(patch("NNMM.Process.ProcessVideoPlay.sg.popup_ok"))
            mockpw = stack.enter_context(patch("NNMM.Process.ProcessVideoPlay.ProcessWatched"))

            pvp = ProcessVideoPlay.ProcessVideoPlay()

            # 正常系
            DUMMY_EXE = "./test/dummy.exe"
            dummy_path = Path(DUMMY_EXE)
            dummy_path.touch()

            mockcmd.return_value = {"general": {"browser_path": DUMMY_EXE}}
            mockmw = self.ReturnMW()
            actual = pvp.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認

            # 異常系

            # 引数エラー
            del mockmw.window
            actual = pvp.Run(mockmw)
            self.assertEqual(-1, actual)

            dummy_path.unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
