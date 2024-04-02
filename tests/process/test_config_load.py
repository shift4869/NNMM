import sys
import unittest
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.config import ConfigLoad
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result

CONFIG_FILE_PATH = "./config/config.ini"


class TestConfigLoad(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        process_mylist_load = ConfigLoad(self.process_info)
        self.assertEqual(self.process_info, process_mylist_load.process_info)

    def test_run(self):
        with ExitStack() as stack:
            mock_config_base = stack.enter_context(patch("NNMM.process.config.ConfigBase"))

            instance = ConfigLoad(self.process_info)
            actual = instance.run()
            self.assertIs(Result.success, actual)

            getitem_value = mock_config_base.get_config.return_value.__getitem__.return_value.__getitem__.return_value
            getboolean_value = (
                mock_config_base.get_config.return_value.__getitem__.return_value.getboolean.return_value
            )
            self.assertEqual(
                [
                    call.__getitem__("-C_BROWSER_PATH-"),
                    call.__getitem__().update(value=getitem_value),
                    call.__getitem__("-C_FOCUS_ON_VIDEO_PLAY-"),
                    call.__getitem__().update(value=getboolean_value),
                    call.__getitem__("-C_AUTO_RELOAD-"),
                    call.__getitem__().update(value=getitem_value),
                    call.__getitem__("-C_RSS_PATH-"),
                    call.__getitem__().update(value=getitem_value),
                    call.__getitem__("-C_DB_PATH-"),
                    call.__getitem__().update(value=getitem_value),
                    call.__getitem__("-C_BROWSER_PATH-"),
                    call.__getitem__().update(select=False),
                ],
                instance.window.mock_calls,
            )
            self.assertEqual(
                [
                    call.set_config(),
                    call.get_config(),
                    call.get_config().__getitem__("general"),
                    call.get_config().__getitem__().__getitem__("browser_path"),
                    call.get_config().__getitem__("general"),
                    call.get_config().__getitem__().getboolean("focus_on_video_play"),
                    call.get_config().__getitem__("general"),
                    call.get_config().__getitem__().__getitem__("auto_reload"),
                    call.get_config().__getitem__("general"),
                    call.get_config().__getitem__().__getitem__("rss_save_path"),
                    call.get_config().__getitem__("db"),
                    call.get_config().__getitem__().__getitem__("save_path"),
                ],
                mock_config_base.mock_calls,
            )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
