import sys
import unittest
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_config import ProcessConfigLoad
from NNMM.process.value_objects.process_info import ProcessInfo

CONFIG_FILE_PATH = "./config/config.ini"


class TestProcessConfigLoad(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        process_mylist_load = ProcessConfigLoad(self.process_info)
        self.assertEqual(self.process_info, process_mylist_load.process_info)

    def test_run(self):
        with ExitStack() as stack:
            mocksc = stack.enter_context(patch("NNMM.process.process_config.ProcessConfigBase.set_config"))
            mockgc = stack.enter_context(patch("NNMM.process.process_config.ProcessConfigBase.get_config"))

            expect_dict = {
                "general": {
                    "browser_path": "browser_path",
                    "auto_reload": "auto_reload",
                    "rss_save_path": "rss_save_path",
                },
                "db": {
                    "save_path": "save_path",
                },
            }
            mockgc.side_effect = [expect_dict]

            mockup = MagicMock()
            mockd = MagicMock()
            type(mockd).update = mockup
            mock_dict = {
                "-C_BROWSER_PATH-": mockd,
                "-C_AUTO_RELOAD-": mockd,
                "-C_RSS_PATH-": mockd,
                "-C_DB_PATH-": mockd,
                "-C_ACCOUNT_EMAIL-": mockd,
                "-C_ACCOUNT_PASSWORD-": mockd,
            }

            self.process_info.window = mock_dict
            process_config_load = ProcessConfigLoad(self.process_info)
            actual = process_config_load.run()
            self.assertIsNone(actual)

            # ucal[{n回目の呼び出し}][args=0]
            # ucal[{n回目の呼び出し}][kwargs=1]
            ucal = mockup.call_args_list
            self.assertEqual(len(ucal), 5)
            self.assertEqual({"value": expect_dict["general"]["browser_path"]}, ucal[0][1])
            self.assertEqual({"value": expect_dict["general"]["auto_reload"]}, ucal[1][1])
            self.assertEqual({"value": expect_dict["general"]["rss_save_path"]}, ucal[2][1])
            self.assertEqual({"value": expect_dict["db"]["save_path"]}, ucal[3][1])
            # self.assertEqual({"value": expect_dict["niconico"]["email"]}, ucal[4][1])
            # self.assertEqual({"value": expect_dict["niconico"]["password"]}, ucal[5][1])
            self.assertEqual({"select": False}, ucal[4][1])
            mockup.reset_mock()
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
