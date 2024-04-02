import copy
import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import call

import PySimpleGUI as sg
from mock import MagicMock, mock_open, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.config import ConfigSave
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result

CONFIG_FILE_PATH = "./config/config.ini"


class TestConfigSave(unittest.TestCase):
    def setUp(self) -> None:
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)
        self.save_path = Path("./tests/dummy_db.db")
        self.save_new_path = Path("./tests/new_db.db")
        return super().setUp()

    def tearDown(self) -> None:
        self.save_path.unlink(missing_ok=True)
        self.save_new_path.unlink(missing_ok=True)
        return super().tearDown()

    def test_init(self):
        process_mylist_save = ConfigSave(self.process_info)
        self.assertEqual(self.process_info, process_mylist_save.process_info)

    def test_run(self):
        with ExitStack() as stack:
            mock_configparser = stack.enter_context(patch("NNMM.process.config.configparser.ConfigParser"))
            mock_path_open = stack.enter_context(patch("NNMM.process.config.Path.open", mock_open()))
            mock_config_base = stack.enter_context(patch("NNMM.process.config.ConfigBase.set_config"))
            mock_mylist_db = stack.enter_context(patch("NNMM.process.config.MylistDBController"))
            mock_mylist_info_db = stack.enter_context(patch("NNMM.process.config.MylistInfoDBController"))

            def get_property_mock(value):
                r = MagicMock()
                r.get.side_effect = lambda: value
                return r

            def pre_run(instance, is_focus, is_db_path_update):
                self.save_path.unlink(missing_ok=True)
                self.save_new_path.unlink(missing_ok=True)

                def general_dict(key):
                    window_dict = {
                        "-C_BROWSER_PATH-": get_property_mock("dummy_browser_path"),
                        "-C_FOCUS_ON_VIDEO_PLAY-": get_property_mock(is_focus),
                        "-C_RSS_PATH-": get_property_mock("dummy_rss_path"),
                        "-C_AUTO_RELOAD-": get_property_mock("dummy_auto_reload"),
                        "-C_DB_PATH-": get_property_mock(str(self.save_new_path)),
                    }
                    return window_dict[key]

                instance.window.reset_mock()
                instance.window.__getitem__.side_effect = general_dict

                mock_configparser.reset_mock(return_value=True)
                if is_db_path_update:

                    def config_dict(key):
                        c_dict = {
                            "general": {
                                "browser_path": "dummy_browser_path",
                                "focus_on_video_play": is_focus,
                                "rss_save_path": "dummy_rss_path",
                                "auto_reload": "dummy_auto_reload",
                            },
                            "db": {"save_path": str(self.save_path)},
                        }
                        return c_dict[key]

                    mock_configparser.return_value.__getitem__.side_effect = config_dict
                    self.save_path.touch()
                else:
                    pass

                mock_path_open.reset_mock()
                mock_config_base.reset_mock()
                mock_mylist_db.reset_mock()
                mock_mylist_info_db.reset_mock()

            def post_run(instance, is_focus, is_db_path_update):
                if is_db_path_update:
                    self.assertFalse(self.save_path.is_file())
                    self.assertTrue(self.save_new_path.is_file())
                    self.assertEqual(
                        [
                            call(),
                            call().read("./config/config.ini", encoding="utf-8"),
                            call().__getitem__("general"),
                            call().__getitem__("general"),
                            call().__getitem__("general"),
                            call().__getitem__("general"),
                            call().__getitem__("db"),
                            call().__getitem__("db"),
                            call().write(mock_path_open.return_value),
                        ],
                        mock_configparser.mock_calls,
                    )
                    db_fullpath = str(self.save_new_path)
                    self.assertEqual(db_fullpath, instance.db_fullpath)
                    mock_mylist_db.assert_called_once_with(db_fullpath=str(db_fullpath))
                    mock_mylist_info_db.assert_called_once_with(db_fullpath=str(db_fullpath))
                    self.assertEqual(
                        [
                            call.__getitem__("-C_BROWSER_PATH-"),
                            call.__getitem__("-C_FOCUS_ON_VIDEO_PLAY-"),
                            call.__getitem__("-C_RSS_PATH-"),
                            call.__getitem__("-C_AUTO_RELOAD-"),
                            call.write_event_value("-TIMER_SET-", "-FIRST_SET-"),
                            call.__getitem__("-C_DB_PATH-"),
                            call.__getitem__("-C_DB_PATH-"),
                        ],
                        instance.window.mock_calls,
                    )
                else:
                    focus_on_video_play = "True" if is_focus else "False"
                    self.assertEqual(
                        [
                            call(),
                            call().read("./config/config.ini", encoding="utf-8"),
                            call().__getitem__("general"),
                            call().__getitem__().__setitem__("browser_path", "dummy_browser_path"),
                            call().__getitem__("general"),
                            call().__getitem__().__setitem__("focus_on_video_play", focus_on_video_play),
                            call().__getitem__("general"),
                            call().__getitem__().__setitem__("rss_save_path", "dummy_rss_path"),
                            call().__getitem__("general"),
                            call().__getitem__().__setitem__("auto_reload", "dummy_auto_reload"),
                            call().__getitem__("db"),
                            call().__getitem__().__getitem__("save_path"),
                            call().__getitem__().__getitem__().__fspath__(),
                            call().write(mock_path_open.return_value),
                        ],
                        mock_configparser.mock_calls,
                    )
                    mock_mylist_db.assert_not_called()
                    mock_mylist_info_db.assert_not_called()
                    self.assertEqual(
                        [
                            call.__getitem__("-C_BROWSER_PATH-"),
                            call.__getitem__("-C_FOCUS_ON_VIDEO_PLAY-"),
                            call.__getitem__("-C_RSS_PATH-"),
                            call.__getitem__("-C_AUTO_RELOAD-"),
                            call.write_event_value("-TIMER_SET-", "-FIRST_SET-"),
                            call.__getitem__("-C_DB_PATH-"),
                        ],
                        instance.window.mock_calls,
                    )

                self.assertEqual(
                    [
                        call("w", encoding="utf-8"),
                        call().__enter__(),
                        call().__exit__(None, None, None),
                        call().close(),
                    ],
                    mock_path_open.mock_calls,
                )
                self.assertEqual([call()], mock_config_base.mock_calls)

            Params = namedtuple("Params", ["is_focus", "is_db_path_update", "result"])
            params_list = [
                Params(False, False, Result.success),
                Params(False, True, Result.success),
                Params(True, False, Result.success),
                Params(True, True, Result.success),
            ]

            for params in params_list:
                instance = ConfigSave(self.process_info)
                pre_run(instance, params.is_focus, params.is_db_path_update)
                actual = instance.run()
                self.assertIs(params.result, actual)
                post_run(instance, params.is_focus, params.is_db_path_update)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
