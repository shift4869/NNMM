# coding: utf-8
"""ProcessMoveDown のテスト
"""
import random
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch

from NNMM.Process import ProcessMoveDown


class TestProcessMoveDown(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PMDrun(self):
        """ProcessMoveDownのrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessMoveDown.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessMoveDown.logger.error"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessMoveDown.UpdateMylistShow"))

            pmd = ProcessMoveDown.ProcessMoveDown()

            # 正常系
            NUM = 5
            mylist_table_s = [f"mylist_{i}" for i in range(NUM)]

            def ReturnMW(index):
                r = MagicMock()
                r.get_indexes = lambda: [index]
                r.Values = mylist_table_s

                expect_window_dict = {
                    "-LIST-": r
                }
                expect_values_dict = {
                    "-LIST-": [mylist_table_s[index]]
                }

                def Returnselect_from_showname(showname):
                    for i, s in enumerate(mylist_table_s):
                        if showname in s:
                            return [{"id": i}]
                    return [{}]

                mockmw = MagicMock()
                mockmw.window = expect_window_dict
                mockmw.values = expect_values_dict
                mockmw.mylist_db.Select = lambda: mylist_table_s
                mockmw.mylist_db.select_from_showname = Returnselect_from_showname

                return mockmw

            index = random.randint(0, NUM - 2)
            mockmw = ReturnMW(index)
            actual = pmd.run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall(index):
                mc = mockmw.window["-LIST-"].mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual(call.update(set_to_index=index + 1), mc[0])
                mockmw.window["-LIST-"].reset_mock()

                mc = mockmw.mylist_db.mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual(call.swap_id(index, index + 1), mc[0])
                mockmw.mylist_db.reset_mock()

                mockums.assert_called()
                mockums.reset_mock()

            assertMockCall(index)

            # 新着マークつき
            mylist_table_s = [f"*:mylist_{i}" for i in range(NUM)]
            index = random.randint(0, NUM - 2)
            mockmw = ReturnMW(index)
            actual = pmd.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall(index)

            # 一番下のマイリストを選択した場合
            index = NUM - 1
            mockmw = ReturnMW(index)
            actual = pmd.run(mockmw)
            self.assertEqual(1, actual)

            # 異常系
            # マイリストが選択されていない
            index = random.randint(1, NUM - 1)
            mockmw = ReturnMW(index)
            mockmw.values["-LIST-"] = []
            actual = pmd.run(mockmw)
            self.assertEqual(-1, actual)

            # 引数エラー
            del mockmw.window
            actual = pmd.run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
