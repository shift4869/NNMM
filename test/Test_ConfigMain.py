# coding: utf-8
"""ConfigMain のテスト
"""

import configparser
import shutil
import sys
import unittest
from contextlib import ExitStack
from logging import INFO, getLogger
from mock import MagicMock, patch, AsyncMock, PropertyMock
from pathlib import Path

import PySimpleGUI as sg

from NNMM.CSVSaveLoad import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.Process import ProcessBase
from NNMM.ConfigMain import *

CONFIG_FILE_PATH = "./config/config.ini"


# テスト用具体化ProcessConfigBase
class ConcreteProcessConfigBase(ProcessConfigBase):
    
    def __init__(self, log_sflag: bool, log_eflag: bool, process_name: str) -> None:
        super().__init__(log_sflag, log_eflag, process_name)

    def Run(self, mw) -> int:
        return 0


class TestConfigMain(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ProcessConfigBaseInit(self):
        """ProcessConfigBaseの初期化後の状態をテストする
        """
        e_log_sflag = True
        e_log_eflag = False
        e_process_name = "テスト用具体化処理"
        cpcb = ConcreteProcessConfigBase(e_log_sflag, e_log_eflag, e_process_name)

        self.assertEqual(e_log_sflag, cpcb.log_sflag)
        self.assertEqual(e_log_eflag, cpcb.log_eflag)
        self.assertEqual(e_process_name, cpcb.process_name)
        self.assertEqual(None, cpcb.main_window)

        self.assertEqual(CONFIG_FILE_PATH, cpcb.CONFIG_FILE_PATH)
        self.assertEqual(None, cpcb.config)

    def test_GetConfigLayout(self):
        """設定画面のレイアウトをテストする
        """
        def ExpectConfigLayout() -> sg.Frame:
            # オートリロード間隔
            auto_reload_combo_box = sg.InputCombo(
                ("(使用しない)", "15分毎", "30分毎", "60分毎"), default_value="(使用しない)", key="-C_AUTO_RELOAD-", size=(20, 10)
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
                [sg.Text("・ニコニコアカウント")],
                [sg.Text("email:", size=(8, 1)), sg.Input(key="-C_ACCOUNT_EMAIL-")],
                [sg.Text("password:", size=(8, 1)), sg.Input(key="-C_ACCOUNT_PASSWORD-", password_char="*")],
                [sg.Text(horizontal_line)],
                [sg.Text("")],
                [sg.Text("")],
                [sg.Column([[sg.Button("設定保存", key="-C_CONFIG_SAVE-")]], justification="right")],
            ]
            layout = [[
                sg.Frame("Config", cf, size=(1070, 100))
            ]]
            return layout

        expext = ExpectConfigLayout()
        actual = ProcessConfigBase.GetConfigLayout()

        # self.assertEqual(expext, actual)
        self.assertEqual(type(expext), type(actual))
        self.assertEqual(len(expext), len(actual))
        for e1, a1 in zip(expext, actual):
            self.assertEqual(len(e1), len(a1))
            for e2, a2 in zip(e1, a1):
                for e3, a3 in zip(e2.Rows, a2.Rows):
                    self.assertEqual(len(e3), len(a3))
                    for e4, a4 in zip(e3, a3):
                        if hasattr(a4, "DisplayText") and a4.DisplayText:
                            self.assertEqual(e4.DisplayText, a4.DisplayText)
                        if hasattr(a4, "Key") and a4.Key:
                            self.assertEqual(e4.Key, a4.Key)
        pass

    def test_SetConfig(self):
        """設定iniのロードをテストする
        """
        with ExitStack() as stack:
            r_mock = MagicMock()
            r_readmock = MagicMock()
            type(r_mock).read = r_readmock
            mock = stack.enter_context(patch("configparser.ConfigParser", lambda: r_mock))

            actual = ProcessConfigBase.SetConfig()

            # rcal[{n回目の呼び出し}][args=0]
            # rcal[{n回目の呼び出し}][kwargs=1]
            rcal = r_readmock.call_args_list
            self.assertEqual(len(rcal), 1)
            self.assertEqual((CONFIG_FILE_PATH, ), rcal[0][0])
            self.assertEqual({"encoding": "utf-8"}, rcal[0][1])
            r_readmock.reset_mock()

        # 実際に取得してiniファイルの構造を調べる
        actual = ProcessConfigBase.SetConfig()
        self.assertTrue("general" in actual)
        self.assertTrue("browser_path" in actual["general"])
        self.assertTrue("auto_reload" in actual["general"])
        self.assertTrue("rss_save_path" in actual["general"])

        self.assertTrue("db" in actual)
        self.assertTrue("save_path" in actual["db"])

        self.assertTrue("niconico" in actual)
        self.assertTrue("email" in actual["niconico"])
        self.assertTrue("password" in actual["niconico"])
        pass

    def test_SetConfig(self):
        """設定iniの取得をテストする
        """
        with ExitStack() as stack:
            mock = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.SetConfig"))

            # 初回取得
            ProcessConfigBase.config = None
            actual = ProcessConfigBase.GetConfig()
            self.assertEqual(None, actual)
            mock.assert_called_once()
            mock.reset_mock()

            # 2回目
            ProcessConfigBase.config = "loaded config"
            actual = ProcessConfigBase.GetConfig()
            self.assertEqual("loaded config", actual)
            mock.assert_not_called()
            mock.reset_mock()
        pass

    def test_SetConfig(self):
        """マイリスト一覧読込ボタンのテスト
        """
        with ExitStack() as stack:
            mockpgf = stack.enter_context(patch("PySimpleGUI.popup_get_file"))
            mocklml = stack.enter_context(patch("NNMM.ConfigMain.LoadMylist"))

            mockpgf.return_value = "./test/input.csv"
            mocklml.side_effect = [0, -1]

            mw = MagicMock()
            type(mw).mylist_db = "mylist_db"

            pml = ProcessMylistLoadCSV()
            actual = pml.Run(mw)
            self.assertEqual(0, actual)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
