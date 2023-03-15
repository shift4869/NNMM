# coding: utf-8
"""ProcessNotWatched のテスト
"""
import random
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch

from NNMM.Process import ProcessNotWatched


class TestProcessNotWatched(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PNWRun(self):
        """ProcessNotWatchedのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessNotWatched.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessNotWatched.logger.error"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessNotWatched.UpdateTableShow"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessNotWatched.UpdateMylistShow"))

            pnw = ProcessNotWatched.ProcessNotWatched()

            # 正常系
            NUM = 5
            mylist_url_s = "https://www.nicovideo.jp/user/11111111/video"

            def MakeTableRecords():
                table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
                records = [[str(i), f"sm1{i:07}", f"動画名{i}", f"投稿者1", "", "2022-01-28 22:00:00", "2022-01-28 22:01:00",
                            f"https://www.nicovideo.jp/watch/sm1{i:07}", mylist_url_s] for i in range(1, NUM + 1)]
                return records

            def ReturnMockValue(value):
                r = MagicMock()
                r.Values = value
                return r

            table_records_s = MakeTableRecords()
            selected_num_s = [0]

            def ReturnMW():
                expect_window_dict = {
                    "-TABLE-": ReturnMockValue(table_records_s)
                }
                expect_values_dict = {
                    "-TABLE-": selected_num_s,
                    "-INPUT1-": mylist_url_s,
                }

                r = MagicMock()
                mockwindow = MagicMock()
                mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
                mockwindow.__iter__.side_effect = expect_window_dict.__iter__
                mockwindow.__contains__.side_effect = expect_window_dict.__contains__
                type(r).window = mockwindow
                mockvalue = MagicMock()
                mockvalue.__getitem__.side_effect = expect_values_dict.__getitem__
                mockvalue.__iter__.side_effect = expect_values_dict.__iter__
                mockvalue.__contains__.side_effect = expect_values_dict.__contains__
                type(r).values = mockvalue
                r.mylist_info_db.update_status.return_value = 0
                return r

            mockmw = ReturnMW()
            actual = pnw.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                mc = mockmw.window.mock_calls
                self.assertEqual(3, len(mc))
                self.assertEqual(call.__getitem__("-TABLE-"), mc[0])
                self.assertEqual(call.__getitem__("-TABLE-"), mc[1])
                self.assertEqual(call.__getitem__("-TABLE-"), mc[2])
                mockmw.window.reset_mock()

                mc = mockmw.values.mock_calls
                self.assertEqual(4, len(mc))
                self.assertEqual(call.__getitem__("-TABLE-"), mc[0])
                self.assertEqual(call.__getitem__("-TABLE-"), mc[1])
                self.assertEqual(call.__getitem__("-TABLE-"), mc[2])
                self.assertEqual(call.__getitem__("-INPUT1-"), mc[3])
                mockmw.values.reset_mock()

                mc = mockmw.method_calls
                self.assertEqual(len(selected_num_s) * 2, len(mc))
                c_index = 0
                for s_index in selected_num_s:
                    v = table_records_s[s_index][1]
                    m = table_records_s[s_index][8]
                    self.assertEqual(call.mylist_info_db.update_status(v, m, "未視聴"), mc[c_index])
                    self.assertEqual(call.mylist_db.update_include_flag(m, True), mc[c_index + 1])
                    c_index = c_index + 2
                mockmw.reset_mock()

                mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db, mylist_url_s)
                mockuts.reset_mock()
                mockums.assert_called_once_with(mockmw.window, mockmw.mylist_db)
                mockums.reset_mock()

            assertMockCall()

            # 複数選択
            selected_num_s = random.sample(range(NUM), 3)
            mockmw = ReturnMW()
            actual = pnw.Run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 異常系
            # 行が選択されていない
            selected_num_s = []
            mockmw = ReturnMW()
            actual = pnw.Run(mockmw)
            self.assertEqual(-1, actual)

            # 引数エラー
            mockmw = ReturnMW()
            del mockmw.window
            del type(mockmw).window
            actual = pnw.Run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
