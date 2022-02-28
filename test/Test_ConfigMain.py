# coding: utf-8
"""ConfigMain のテスト
"""

import configparser
import copy
import shutil
import sys
import unittest
from contextlib import ExitStack
from logging import INFO, getLogger
from mock import MagicMock, patch, mock_open
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
        ProcessConfigBase.config = None
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
                # [sg.Text("・ニコニコアカウント")],
                # [sg.Text("email:", size=(8, 1)), sg.Input(key="-C_ACCOUNT_EMAIL-")],
                # [sg.Text("password:", size=(8, 1)), sg.Input(key="-C_ACCOUNT_PASSWORD-", password_char="*")],
                # [sg.Text(horizontal_line)],
                [sg.Text("")],
                [sg.Text("")],
                [sg.Column([[sg.Button("設定保存", key="-C_CONFIG_SAVE-")]], justification="right")],
            ]
            layout = [[
                sg.Frame("Config", cf, size=(1070, 100))
            ]]
            return layout

        expect = ExpectConfigLayout()
        actual = ProcessConfigBase.GetConfigLayout()

        # self.assertEqual(expext, actual)
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

        # self.assertTrue("niconico" in actual)
        # self.assertTrue("email" in actual["niconico"])
        # self.assertTrue("password" in actual["niconico"])
        pass

    def test_GetConfig(self):
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

    def test_PMLLoadMylist(self):
        """マイリスト一覧読込ボタンのテスト
        """
        with ExitStack() as stack:
            mockpgf = stack.enter_context(patch("PySimpleGUI.popup_get_file"))
            mocklml = stack.enter_context(patch("NNMM.ConfigMain.LoadMylist"))
            mockpu = stack.enter_context(patch("PySimpleGUI.popup"))
            mockums = stack.enter_context(patch("NNMM.ConfigMain.UpdateMylistShow"))

            TEST_INPUT_PATH = "./test/input.csv"
            mockpgf.side_effect = [TEST_INPUT_PATH, None, TEST_INPUT_PATH]
            mocklml.side_effect = [0, -1]

            mw = MagicMock()
            type(mw).mylist_db = "mylist_db"

            pml = ProcessMylistLoadCSV()

            # 正常系
            # 実行
            actual = pml.Run(mw)
            self.assertEqual(0, actual)

            # 呼び出し確認
            default_path = Path("") / "input.csv"
            expect_kwargs = {
                "default_path": default_path.absolute(),
                "default_extension": "csv",
                "save_as": False
            }

            # pgfcal[{n回目の呼び出し}][args=0]
            # pgfcal[{n回目の呼び出し}][kwargs=1]
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("読込ファイル選択", ), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            # lmlcal[{n回目の呼び出し}][args=0]
            lmlcal = mocklml.call_args_list
            self.assertEqual(len(lmlcal), 1)
            self.assertEqual((mw.mylist_db, str(Path(TEST_INPUT_PATH))), lmlcal[0][0])
            mocklml.reset_mock()

            # pucal[{n回目の呼び出し}][args=0]
            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("読込完了", ), pucal[0][0])
            mockpu.reset_mock()

            # mockums[{n回目の呼び出し}][args=0]
            umscal = mockums.call_args_list
            self.assertEqual(len(umscal), 1)
            self.assertEqual((mw.window, mw.mylist_db), umscal[0][0])
            mockums.reset_mock()

            # 異常系
            # ファイル選択をキャンセルされた
            actual = pml.Run(mw)
            self.assertEqual(1, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("読込ファイル選択", ), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            mocklml.assert_not_called()
            mockpu.assert_not_called()

            # マイリスト読込に失敗
            actual = pml.Run(mw)
            self.assertEqual(-1, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("読込ファイル選択", ), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            lmlcal = mocklml.call_args_list
            self.assertEqual(len(lmlcal), 1)
            self.assertEqual((mw.mylist_db, str(Path(TEST_INPUT_PATH))), lmlcal[0][0])
            mocklml.reset_mock()

            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("読込失敗", ), pucal[0][0])
            mockpu.reset_mock()
        pass

    def test_PMSSaveMylist(self):
        """マイリスト一覧保存ボタンのテスト
        """
        with ExitStack() as stack:
            mockpgf = stack.enter_context(patch("PySimpleGUI.popup_get_file"))
            mocksml = stack.enter_context(patch("NNMM.ConfigMain.SaveMylist"))
            mockpu = stack.enter_context(patch("PySimpleGUI.popup"))

            TEST_RESULT_PATH = "./test/result.csv"
            mockpgf.side_effect = [TEST_RESULT_PATH, None, TEST_RESULT_PATH]
            mocksml.side_effect = [0, -1]

            mw = MagicMock()
            type(mw).mylist_db = "mylist_db"

            pms = ProcessMylistSaveCSV()

            # 正常系
            # 実行
            actual = pms.Run(mw)
            self.assertEqual(0, actual)

            # 呼び出し確認
            default_path = Path("") / "result.csv"
            expect_kwargs = {
                "default_path": default_path.absolute(),
                "default_extension": "csv",
                "save_as": True
            }

            # pgfcal[{n回目の呼び出し}][args=0]
            # pgfcal[{n回目の呼び出し}][kwargs=1]
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("保存先ファイル選択", ), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            # lmlcal[{n回目の呼び出し}][args=0]
            lmlcal = mocksml.call_args_list
            self.assertEqual(len(lmlcal), 1)
            self.assertEqual((mw.mylist_db, str(Path(TEST_RESULT_PATH))), lmlcal[0][0])
            mocksml.reset_mock()

            # pucal[{n回目の呼び出し}][args=0]
            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("保存完了", ), pucal[0][0])
            mockpu.reset_mock()

            # 異常系
            # ファイル選択をキャンセルされた
            actual = pms.Run(mw)
            self.assertEqual(1, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("保存先ファイル選択", ), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            mocksml.assert_not_called()
            mockpu.assert_not_called()

            # マイリスト保存に失敗
            actual = pms.Run(mw)
            self.assertEqual(-1, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("保存先ファイル選択", ), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            lmlcal = mocksml.call_args_list
            self.assertEqual(len(lmlcal), 1)
            self.assertEqual((mw.mylist_db, str(Path(TEST_RESULT_PATH))), lmlcal[0][0])
            mocksml.reset_mock()

            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("保存失敗", ), pucal[0][0])
            mockpu.reset_mock()
        pass

    def test_PCLConfigLoad(self):
        """設定タブを開いたときの処理のテスト
        """
        with ExitStack() as stack:
            mocksc = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.SetConfig"))
            mockgc = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig"))

            expect_dict = {
                "general": {
                    "browser_path": "browser_path",
                    "auto_reload": "auto_reload",
                    "rss_save_path": "rss_save_path",
                },
                "db": {
                    "save_path": "save_path",
                },
                # "niconico": {
                #     "email": "email",
                #     "password": "password",
                # },
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

            mw = MagicMock()
            type(mw).window = mock_dict

            pcl = ProcessConfigLoad()
            actual = pcl.Run(mw)
            self.assertEqual(0, actual)

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

    def test_PCSConfigSave(self):
        """設定タブを開いたときの処理のテスト
        """
        with ExitStack() as stack:
            mockcp = stack.enter_context(patch("configparser.ConfigParser"))
            mockfp = stack.enter_context(patch("pathlib.Path.open", mock_open()))
            mocksc = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.SetConfig"))

            mockread = MagicMock()
            TEST_PREV_SAVE_PATH = "./test/p_test.db"
            TEST_NEXT_SAVE_PATH = "./test/n_test.db"
            expect_prev_dict = {
                "general": {
                    "browser_path": "p_browser_path",
                    "auto_reload": "p_auto_reload",
                    "rss_save_path": "p_rss_save_path",
                },
                "db": {
                    "save_path": TEST_PREV_SAVE_PATH,
                },
                # "niconico": {
                #     "email": "p_email",
                #     "password": "p_password",
                # },
            }
            mockccp = MagicMock()
            mockread.side_effect = [expect_prev_dict]
            type(mockccp).read = mockread
            mockccp.__getitem__.side_effect = expect_prev_dict.__getitem__
            mockccp.__iter__.side_effect = expect_prev_dict.__iter__
            mockccp.__contains__.side_effect = expect_prev_dict.__contains__

            mockcp.side_effect = [mockccp]

            def getmock(str):
                r = MagicMock()
                type(r).get = lambda s: str
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
                # "niconico": {
                #     "email": "n_email",
                #     "password": "n_password",
                # },
            }
            mock_dict = {
                "-C_BROWSER_PATH-": getmock(expect_next_dict["general"]["browser_path"]),
                "-C_AUTO_RELOAD-": getmock(expect_next_dict["general"]["auto_reload"]),
                "-C_RSS_PATH-": getmock(expect_next_dict["general"]["rss_save_path"]),
                "-C_DB_PATH-": getmock(expect_next_dict["db"]["save_path"]),
                # "-C_ACCOUNT_EMAIL-": getmock(expect_next_dict["niconico"]["email"]),
                # "-C_ACCOUNT_PASSWORD-": getmock(expect_next_dict["niconico"]["password"]),
            }
            mockwin = MagicMock()
            mockwev = MagicMock()
            type(mockwin).write_event_value = mockwev
            mockwin.__getitem__.side_effect = mock_dict.__getitem__
            mockwin.__iter__.side_effect = mock_dict.__iter__
            mockwin.__contains__.side_effect = mock_dict.__contains__

            mw = MagicMock()
            type(mw).window = mockwin
            type(mw).db_fullpath = None
            type(mw).mylist_db = None
            type(mw).mylist_info_db = None

            # dbのパス先にダミーファイルを作っておく
            Path(TEST_PREV_SAVE_PATH).touch()

            # 実行
            pcs = ProcessConfigSave()
            actual = pcs.Run(mw)
            self.assertEqual(0, actual)

            # 呼び出し確認
            # rcal[{n回目の呼び出し}][args=0]
            # rcal[{n回目の呼び出し}][kwargs=1]
            rcal = mockread.call_args_list
            self.assertEqual(len(rcal), 1)
            self.assertEqual((CONFIG_FILE_PATH, ), rcal[0][0])
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
            self.assertIsNotNone(mw.db_fullpath)
            self.assertIsNotNone(mw.mylist_db)
            self.assertIsNotNone(mw.mylist_info_db)

            # 後始末
            Path(TEST_PREV_SAVE_PATH).unlink(missing_ok=True)
            Path(TEST_NEXT_SAVE_PATH).unlink(missing_ok=True)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
