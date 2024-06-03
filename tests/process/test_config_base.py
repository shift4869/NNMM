import sys
import unittest
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import ConfigBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

CONFIG_FILE_PATH = "./config/config.ini"


class ConcreteConfigBase(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        return Result.success


class TestConfigBase(unittest.TestCase):
    def setUp(self):
        ConfigBase.config = None
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        process_config_base = ConcreteConfigBase(self.process_info)

        self.assertEqual(self.process_info, process_config_base.process_info)
        self.assertEqual(CONFIG_FILE_PATH, ConfigBase.CONFIG_FILE_PATH)
        self.assertEqual(None, ConfigBase.config)

    def test_make_layout(self):
        def expect_config_layout() -> sg.Frame:
            auto_reload_combo_box = sg.InputCombo(
                ("(使用しない)", "15分毎", "30分毎", "60分毎"),
                default_value="(使用しない)",
                key="-C_AUTO_RELOAD-",
                size=(20, 10),
            )

            horizontal_line = "-" * 100

            cf = [
                [sg.Text(horizontal_line)],
                [sg.Text("・「ブラウザで再生」時に使用するブラウザパス")],
                [sg.Input(key="-C_BROWSER_PATH-"), sg.FileBrowse()],
                [sg.Text("・オートリロードする間隔")],
                [auto_reload_combo_box],
                [sg.Text("・RSS保存先パス")],
                [sg.Input(key="-C_RSS_PATH-"), sg.FolderBrowse()],
                [sg.Text("・マイリスト一覧保存")],
                [sg.Button("保存", key="-C_MYLIST_SAVE-")],
                [sg.Text("・マイリスト一覧読込")],
                [sg.Button("読込", key="-C_MYLIST_LOAD-")],
                [sg.Text(horizontal_line)],
                [sg.Text("・マイリスト・動画情報保存DBのパス")],
                [sg.Input(key="-C_DB_PATH-"), sg.FileBrowse()],
                [sg.Text(horizontal_line)],
                [sg.Text("")],
                [sg.Text("")],
                [sg.Column([[sg.Button("設定保存", key="-C_CONFIG_SAVE-")]], justification="right")],
            ]
            layout = [[sg.Frame("Config", cf, size=(1070, 100))]]
            return layout

        expect = expect_config_layout()
        actual = ConfigBase.make_layout()

        self.assertEqual(type(expect), type(actual))
        self.assertEqual(len(expect), len(actual))
        for e1, a1 in zip(expect, actual):
            self.assertEqual(len(e1), len(a1))
            for e2, a2 in zip(e1, a1):
                for e3, a3 in zip(e2.Rows, a2.Rows):
                    self.assertEqual(len(e3), len(a3))
                    for e4, a4 in zip(e3, a3):
                        if hasattr(a4, "DisplayText") and a4.DisplayText:
                            self.assertEqual(e4.DisplayText, a4.DisplayText)
                        if hasattr(a4, "Key") and a4.Key:
                            self.assertEqual(e4.Key, a4.Key)

    def test_get_config(self):
        with ExitStack() as stack:
            mock_set_config = stack.enter_context(patch("nnmm.process.config.ConfigBase.set_config"))

            # 初回取得
            ConfigBase.config = None
            actual = ConfigBase.get_config()
            self.assertEqual(None, actual)
            mock_set_config.assert_called_once()
            mock_set_config.reset_mock()

            # 2回目
            ConfigBase.config = "loaded config"
            actual = ConfigBase.get_config()
            self.assertEqual("loaded config", actual)
            mock_set_config.assert_not_called()
            mock_set_config.reset_mock()

    def test_set_config(self):
        with ExitStack() as stack:
            mock_configparser = stack.enter_context(patch("nnmm.process.config.configparser.ConfigParser"))
            mock_config = MagicMock()
            mock_configparser.side_effect = lambda: mock_config

            actual = ConfigBase.set_config()
            self.assertEqual(mock_config, actual)

            self.assertEqual([call(CONFIG_FILE_PATH, encoding="utf-8")], mock_config.read.mock_calls)

        # 実際に取得してiniファイルの構造を調べる
        actual = ConfigBase.set_config()
        self.assertTrue("general" in actual)
        self.assertTrue("browser_path" in actual["general"])
        self.assertTrue("auto_reload" in actual["general"])
        self.assertTrue("rss_save_path" in actual["general"])
        self.assertTrue("db" in actual)
        self.assertTrue("save_path" in actual["db"])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
