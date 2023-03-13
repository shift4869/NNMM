# coding: utf-8
"""ProcessWatchedAllMylist のテスト
"""
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch

from NNMM.Process import ProcessWatchedAllMylist


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

    def MakeTableRecords(self):
        """表示中の動画テーブルから取得されるレコードセット
        """
        NUM = 5
        mylist_url = "https://www.nicovideo.jp/user/10000001/video"

        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL"]
        records = [[i, f"sm0000000{i+1}", f"動画タイトル_{i+1}", f"投稿者1", "未視聴", "2022-01-28 22:00:00",
                    f"https://www.nicovideo.jp/watch/sm1000000{i+1}", mylist_url] for i in range(NUM)]
        return records

    def ReturnMW(self):
        r = MagicMock()
        
        mylist_url = "https://www.nicovideo.jp/user/10000001/video"
        mockget = MagicMock()
        mockget.get.side_effect = lambda: mylist_url
        mockv = MagicMock()
        mockv.Values = self.MakeTableRecords()

        expect_window_dict = {
            "-INPUT1-": mockget,
            "-TABLE-": mockv
        }

        mockwindow = MagicMock()
        mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
        mockwindow.__iter__.side_effect = expect_window_dict.__iter__
        mockwindow.__contains__.side_effect = expect_window_dict.__contains__
        r.window = mockwindow

        r.mylist_db.Select.side_effect = lambda: self.MakeMylistDB()
        return r

    def test_PWAMRun(self):
        """ProcessWatchedAllMylist のRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessWatchedAllMylist.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessWatchedAllMylist.logger.error"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessWatchedAllMylist.UpdateMylistShow"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessWatchedAllMylist.UpdateTableShow"))

            pwam = ProcessWatchedAllMylist.ProcessWatchedAllMylist()

            # 正常系
            mylist_url_s = "https://www.nicovideo.jp/user/10000001/video"
            mockmw = self.ReturnMW()
            mockmw.reset_mock()
            actual = pwam.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                m_list = self.MakeMylistDB()
                records = [m for m in m_list if m["is_include_new"]]
                all_num = len(records)

                b_count = 4 if mylist_url_s == "" else 2
                index = 1
                mc = mockmw.mock_calls
                self.assertEqual(b_count + all_num * 2, len(mc))
                self.assertEqual(call.mylist_db.Select(), mc[0])
                for i, record in enumerate(records):
                    mylist_url = record.get("url")
                    self.assertEqual(call.mylist_info_db.UpdateStatusInMylist(mylist_url, ""), mc[index])
                    self.assertEqual(call.mylist_db.UpdateIncludeFlag(mylist_url, False), mc[index + 1])
                    index += 2

                self.assertEqual(call.window.__getitem__("-INPUT1-"), mc[index])
                if mylist_url_s == "":
                    self.assertEqual(call.window.__getitem__("-TABLE-"), mc[index + 1])
                    def_data = self.MakeTableRecords()
                    for i, record in enumerate(def_data):
                        # マイリスト情報ステータスDB更新
                        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL"]
                        def_data[i][4] = ""

                    mct = mockmw.window["-TABLE-"].mock_calls
                    self.assertEqual(1, len(mct))
                    self.assertEqual(call.update(values=def_data), mct[0])

                mockmw.reset_mock()

                mockums.assert_called_once_with(mockmw.window, mockmw.mylist_db)
                mockums.reset_mock()
                mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db, mylist_url_s)
                mockuts.reset_mock()

            assertMockCall()

            # 右上のテキストボックスが空（横断的にすべて表示時等）
            mylist_url_s = ""
            mockmw = self.ReturnMW()
            mockmw.window["-INPUT1-"].get.side_effect = lambda: mylist_url_s
            mockmw.reset_mock()
            actual = pwam.Run(mockmw)
            self.assertEqual(0, actual)
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
