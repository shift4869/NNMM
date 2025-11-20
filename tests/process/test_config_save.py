import copy
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path

from mock import MagicMock, mock_open, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import ConfigSave
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

CONFIG_FILE_PATH = "./config/config.ini"


class TestConfigSave(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        process_mylist_save = ConfigSave(self.process_info)
        self.assertEqual(self.process_info, process_mylist_save.process_info)

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mockcp = stack.enter_context(patch("nnmm.process.config.configparser.ConfigParser"))
            mockfp = stack.enter_context(patch("nnmm.process.config.Path.open", mock_open()))
            mocksc = stack.enter_context(patch("nnmm.process.config.ConfigBase.set_config"))
            mockmc = stack.enter_context(patch("nnmm.process.config.MylistDBController"))
            mockmbc = stack.enter_context(patch("nnmm.process.config.MylistInfoDBController"))

            mockread = MagicMock()
            TEST_PREV_SAVE_PATH = "./tests/p_test.db"
            TEST_NEXT_SAVE_PATH = "./tests/n_test.db"
            expect_prev_dict = {
                "general": {
                    "browser_path": "p_browser_path",
                    "auto_reload": "p_auto_reload",
                    "rss_save_path": "p_rss_save_path",
                },
                "db": {
                    "save_path": TEST_PREV_SAVE_PATH,
                },
            }
            mockccp = MagicMock()
            mockread.side_effect = [expect_prev_dict]
            mockccp.read = mockread
            mockccp.__getitem__.side_effect = expect_prev_dict.__getitem__
            mockccp.__iter__.side_effect = expect_prev_dict.__iter__
            mockccp.__contains__.side_effect = expect_prev_dict.__contains__

            mockcp.side_effect = [mockccp]

            def getmock(str):
                r = MagicMock()
                r.get = lambda: str
                return r

            expect_next_dict = {
                "general": {
                    "browser_path": "n_browser_path",
                    "auto_reload": "n_auto_reload",
                    "rss_save_path": "n_rss_save_path",
                },
                "db": {
                    "save_path": TEST_NEXT_SAVE_PATH,
                },
            }
            mock_dict = {
                "-C_BROWSER_PATH-": getmock(expect_next_dict["general"]["browser_path"]),
                "-C_AUTO_RELOAD-": getmock(expect_next_dict["general"]["auto_reload"]),
                "-C_RSS_PATH-": getmock(expect_next_dict["general"]["rss_save_path"]),
                "-C_DB_PATH-": getmock(expect_next_dict["db"]["save_path"]),
            }
            mockwin = MagicMock()
            mockwev = MagicMock()
            mockwin.write_event_value = mockwev
            mockwin.__getitem__.side_effect = mock_dict.__getitem__
            mockwin.__iter__.side_effect = mock_dict.__iter__
            mockwin.__contains__.side_effect = mock_dict.__contains__

            self.process_info.window = mockwin
            self.process_info.db_fullpath = None
            self.process_info.mylist_db = None
            self.process_info.mylist_info_db = None

            # dbのパス先にダミーファイルを作っておく
            Path(TEST_PREV_SAVE_PATH).touch()

            # 実行
            process_mylist_save = ConfigSave(self.process_info)
            actual = process_mylist_save.run()
            self.assertIs(Result.success, actual)

            # 呼び出し確認
            # rcal[{n回目の呼び出し}][args=0]
            # rcal[{n回目の呼び出し}][kwargs=1]
            rcal = mockread.call_args_list
            self.assertEqual(len(rcal), 1)
            self.assertEqual((CONFIG_FILE_PATH,), rcal[0][0])
            self.assertEqual({"encoding": "utf-8"}, rcal[0][1])

            # wcal[{n回目の呼び出し}][args=0]
            wcal = mockwev.call_args_list
            self.assertEqual(len(wcal), 1)
            self.assertEqual(("-TIMER_SET-", "-FIRST_SET-"), wcal[0][0])

            mockfp.assert_called()
            mocksc.assert_called()

            # 設定更新結果比較
            actual_next_dict = copy.deepcopy(expect_next_dict)
            self.assertEqual(expect_prev_dict, actual_next_dict)

            # 新しい場所のDBへ繋ぎ変えができているか
            self.assertIsNotNone(process_mylist_save.db_fullpath)
            self.assertIsNotNone(process_mylist_save.process_info.mylist_db)
            self.assertIsNotNone(process_mylist_save.process_info.mylist_info_db)

            # 後始末
            Path(TEST_PREV_SAVE_PATH).unlink(missing_ok=True)
            Path(TEST_NEXT_SAVE_PATH).unlink(missing_ok=True)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
