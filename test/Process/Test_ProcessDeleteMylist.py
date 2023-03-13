# coding: utf-8
"""ProcessDeleteMylist のテスト
"""
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, patch

from NNMM.Process import ProcessDeleteMylist


class TestProcessDeleteMylist(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PCMRun(self):
        """ProcessDeleteMylistのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessDeleteMylist.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessDeleteMylist.logger.error"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessDeleteMylist.UpdateMylistShow"))
            mockpgt = stack.enter_context(patch("NNMM.Process.ProcessDeleteMylist.sg.popup_ok_cancel"))

            pdm = ProcessDeleteMylist.ProcessDeleteMylist()

            # 正常系
            showname_s = "sample_mylist_showname"
            mylist_url_s = "https://www.nicovideo.jp/user/11111111/video"

            def ReturnSelectFromShowname(s, showname):
                url_dict = {
                    showname_s: {"url": mylist_url_s},
                }
                res = url_dict.get(showname, {})
                return [res] if res else []

            def ReturnSelectFromURL(s, mylist_url):
                showname_dict = {
                    mylist_url_s: {"showname": showname_s},
                }
                return [showname_dict.get(mylist_url, {})]

            expect_values_dict = {
                "-LIST-": [showname_s]
            }

            mockmw = MagicMock()
            type(mockmw).values = expect_values_dict
            mockmylist_db = MagicMock()
            type(mockmylist_db).SelectFromShowname = ReturnSelectFromShowname
            type(mockmylist_db).SelectFromURL = ReturnSelectFromURL
            type(mockmw).mylist_db = mockmylist_db

            actual = pdm.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                mc = mockpgt.mock_calls
                self.assertEqual(2, len(mc))
                self.assertEqual((f"{showname_s}\n{mylist_url_s}\nマイリスト削除します",), mc[0][1])
                self.assertEqual({"title": "削除確認"}, mc[0][2])
                mockpgt.reset_mock()

                mc = mockmw.mock_calls
                self.assertEqual(7, len(mc))
                self.assertEqual("mylist_info_db.DeleteFromMylistURL", mc[0][0])
                self.assertEqual((mylist_url_s,), mc[0][1])
                self.assertEqual("window.__getitem__", mc[1][0])
                self.assertEqual(("-TABLE-",), mc[1][1])
                self.assertEqual("window.__getitem__().update", mc[2][0])
                self.assertEqual({"values": [[]]}, mc[2][2])
                self.assertEqual("window.__getitem__", mc[3][0])
                self.assertEqual(("-INPUT1-",), mc[3][1])
                self.assertEqual("window.__getitem__().update", mc[4][0])
                self.assertEqual({"value": ""}, mc[4][2])
                self.assertEqual("window.__getitem__", mc[5][0])
                self.assertEqual(("-INPUT2-",), mc[5][1])
                self.assertEqual("window.__getitem__().update", mc[6][0])
                self.assertEqual({"value": "マイリスト削除完了"}, mc[6][2])
                mockmw.reset_mock()

                mc = mockmylist_db.mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual("DeleteFromURL", mc[0][0])
                self.assertEqual((mylist_url_s,), mc[0][1])
                mockmylist_db.reset_mock()

                mockums.assert_called()
                mockums.reset_mock()

            assertMockCall()

            # 新規マークつき
            expect_values_dict["-LIST-"] = ["*:" + showname_s]
            actual = pdm.Run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # マイリスト取得元について別分岐1
            del expect_values_dict["-LIST-"]
            expect_values_dict["-INPUT1-"] = mylist_url_s
            actual = pdm.Run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # マイリスト取得元について別分岐2
            del expect_values_dict["-INPUT1-"]
            expect_values_dict["-INPUT2-"] = mylist_url_s
            actual = pdm.Run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 削除確認時にキャンセルが押された
            del expect_values_dict["-INPUT2-"]
            expect_values_dict["-LIST-"] = [showname_s]
            mockpgt.return_value = "Cancel"

            actual = pdm.Run(mockmw)
            self.assertEqual(1, actual)

            mc = mockpgt.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual((f"{showname_s}\n{mylist_url_s}\nマイリスト削除します",), mc[0][1])
            self.assertEqual({"title": "削除確認"}, mc[0][2])
            mockpgt.reset_mock()

            mc = mockmw.mock_calls
            self.assertEqual(2, len(mc))
            self.assertEqual("window.__getitem__", mc[0][0])
            self.assertEqual(("-INPUT2-",), mc[0][1])
            self.assertEqual("window.__getitem__().update", mc[1][0])
            self.assertEqual({"value": "マイリスト削除キャンセル"}, mc[1][2])
            mockmw.reset_mock()

            # 異常系
            # IndexError
            expect_values_dict["-LIST-"] = "invalid showname"
            actual = pdm.Run(mockmw)
            self.assertEqual(-1, actual)

            # 既存マイリストに存在しない場合
            del expect_values_dict["-LIST-"]
            expect_values_dict["-INPUT1-"] = "invalid showname"
            actual = pdm.Run(mockmw)
            self.assertEqual(-1, actual)

            # 引数エラー
            del mockmw.values
            del type(mockmw).values
            actual = pdm.Run(mockmw)
            self.assertEqual(-1, actual)
            pass
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
