# coding: utf-8
"""ProcessShowMylistInfoAll のテスト
"""
import sys
import unittest
from contextlib import ExitStack
from mock import MagicMock, patch, call

from NNMM.Process import ProcessShowMylistInfoAll


class TestProcessShowMylistInfoAll(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def MakeMylistInfoDB(self):
        """mylist_info_db.Select()で取得される動画情報データセット
        """
        NUM = 5
        res = []

        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded_at", "registered_at", "video_url", "mylist_url"]
        n = 0
        for k in range(NUM):
            table_rows = [[n, f"sm{k+1}000000{i+1}", f"動画タイトル{k+1}_{i+1}", f"投稿者{k+1}", "",
                           f"2022-02-01 0{k+1}:00:0{i+1}",
                           f"2022-02-01 0{k+1}:01:0{i+1}",
                           f"https://www.nicovideo.jp/watch/sm{k+1}000000{i+1}",
                           f"https://www.nicovideo.jp/user/1000000{k+1}/video"] for i in range(NUM)]
            n = n + 1

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return res

    def ReturnMW(self):
        def ReturnWindow():
            r_wt = MagicMock()
            r_wt.get_indexes = lambda: [1]
            return r_wt

        expect_window_dict = {
            "-LIST-": ReturnWindow(),
            "-TABLE-": MagicMock(),
            "-INPUT1-": MagicMock()
        }

        r = MagicMock()
        mockwindow = MagicMock()
        mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
        mockwindow.__iter__.side_effect = expect_window_dict.__iter__
        mockwindow.__contains__.side_effect = expect_window_dict.__contains__
        type(r).window = mockwindow

        r.mylist_info_db.Select = self.MakeMylistInfoDB
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
            index = 1
            mc = mockmw.window["-LIST-"].mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.update(set_to_index=index), mc[0])
            mockmw.window["-LIST-"].reset_mock()

            NUM = 100
            m_list = self.MakeMylistInfoDB()
            records = sorted(m_list, key=lambda x: int(x["video_id"][2:]), reverse=True)[0:NUM]
            def_data = []
            for i, r in enumerate(records):
                a = [i + 1, r["video_id"], r["title"], r["username"], r["status"], r["uploaded_at"], r["registered_at"], r["video_url"], r["mylist_url"]]
                def_data.append(a)
            mc = mockmw.window["-TABLE-"].mock_calls
            self.assertEqual(3, len(mc))
            self.assertEqual(call.update(values=def_data), mc[0])
            self.assertEqual(call.update(select_rows=[0]), mc[1])
            self.assertEqual(call.update(row_colors=[(0, "", "")]), mc[2])
            mockmw.window["-TABLE-"].reset_mock()

            mc = mockmw.window["-INPUT1-"].mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.update(value=""), mc[0])
            mockmw.window["-INPUT1-"].reset_mock()

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
