# coding: utf-8
"""MainWindow のテスト
"""

import copy
import sys
import unittest
from contextlib import ExitStack
from logging import INFO, getLogger
from mock import MagicMock, patch, mock_open
from pathlib import Path

import PySimpleGUI as sg

from NNMM.MainWindow import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import *

TEST_DB_PATH = "./test/test.db"


class TestWindowMain(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_MainWindowInit(self):
        """WindowMainの初期化後の状態をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.MainWindow.logger.info"))
            mockwd = stack.enter_context(patch("NNMM.MainWindow.sg.Window"))
            mockcps = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.SetConfig"))
            mockcpg = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig"))
            mockmdbc = stack.enter_context(patch("NNMM.MainWindow.MylistDBController"))
            mockmidbc = stack.enter_context(patch("NNMM.MainWindow.MylistInfoDBController"))
            mockmmwl = stack.enter_context(patch("NNMM.MainWindow.MainWindow.MakeMainWindowLayout"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mockums = stack.enter_context(patch("NNMM.MainWindow.UpdateMylistShow"))

            mockmmwl.return_value = [["dummy layout"]]

            expect_config = {"db": {"save_path": TEST_DB_PATH}}
            mockcpg.side_effect = lambda: expect_config

            r_mock = MagicMock()
            b_mock = MagicMock()
            type(b_mock).bind = lambda s, b, k: f"{b}_{k}"
            u_mock = MagicMock()
            type(u_mock).update = lambda s, values: values
            expect_window_dict = {
                "-LIST-": b_mock,
                "-TABLE-": u_mock,
            }
            r_mock.__getitem__.side_effect = expect_window_dict.__getitem__
            r_mock.__iter__.side_effect = expect_window_dict.__iter__
            r_mock.__contains__.side_effect = expect_window_dict.__contains__
            type(r_mock).write_event_value = lambda s, k, v: f"{k}_{v}"

            def r_mock_window(title, layout, size, finalize, resizable):
                return r_mock
            mockwd.side_effect = r_mock_window

            # インスタンス生成->__init__実行
            mw = MainWindow()

            # インスタンス生成後状態確認
            # config
            test_db_path = str(Path(TEST_DB_PATH))
            mockcps.assert_called_once()
            mockcpg.assert_called_once()
            self.assertEqual(expect_config, mw.config)
            self.assertEqual(test_db_path, str(Path(mw.db_fullpath)))

            # cal[{n回目の呼び出し}][args=0]
            # cal[{n回目の呼び出し}][kwargs=1]
            mdbccal = mockmdbc.call_args_list
            self.assertEqual(len(mdbccal), 1)
            self.assertEqual({"db_fullpath": test_db_path}, mdbccal[0][1])
            self.assertEqual(mockmdbc(), mw.mylist_db)
            mockmdbc.reset_mock()

            midbccal = mockmidbc.call_args_list
            self.assertEqual(len(midbccal), 1)
            self.assertEqual({"db_fullpath": test_db_path}, midbccal[0][1])
            self.assertEqual(mockmidbc(), mw.mylist_info_db)
            mockmidbc.reset_mock()

            mockmmwl.assert_called_once()

            wdcal = mockwd.call_args_list
            self.assertEqual(len(wdcal), 1)
            self.assertEqual(("NNMM", mockmmwl.return_value), wdcal[0][0])
            self.assertEqual({
                "size": (1130, 900),
                "finalize": True,
                "resizable": True,
            }, wdcal[0][1])
            self.assertEqual(r_mock, mw.window)
            mockwd.reset_mock()

            lcfccal = mocklcfc.call_args_list
            self.assertEqual(len(lcfccal), 1)
            self.assertEqual(("./log/logging.ini", ), lcfccal[0][0])
            self.assertEqual({"disable_existing_loggers": False}, lcfccal[0][1])
            mocklcfc.reset_mock()

            umscal = mockums.call_args_list
            self.assertEqual(len(umscal), 1)
            self.assertEqual((r_mock, mockmdbc()), umscal[0][0])
            mockums.reset_mock()

            # イベントと処理の辞書
            # 新機能を追加したらここにも追加する
            expect_ep_dict = {
                "ブラウザで開く::-TR-": ProcessVideoPlay.ProcessVideoPlay,
                "視聴済にする::-TR-": ProcessWatched.ProcessWatched,
                "未視聴にする::-TR-": ProcessNotWatched.ProcessNotWatched,
                "検索（動画名）::-TR-": ProcessSearch.ProcessVideoSearch,
                "強調表示を解除::-TR-": ProcessSearch.ProcessVideoSearchClear,
                "情報表示::-TR-": PopupWindowMain.PopupVideoWindow,
                "動画ダウンロード::-TR-": ProcessDownload.ProcessDownload,
                "全動画表示::-MR-": ProcessShowMylistInfoAll.ProcessShowMylistInfoAll,
                "視聴済にする（選択）::-MR-": ProcessWatchedMylist.ProcessWatchedMylist,
                "視聴済にする（全て）::-MR-": ProcessWatchedAllMylist.ProcessWatchedAllMylist,
                "上に移動::-MR-": ProcessMoveUp.ProcessMoveUp,
                "下に移動::-MR-": ProcessMoveDown.ProcessMoveDown,
                "マイリスト追加::-MR-": ProcessCreateMylist.ProcessCreateMylist,
                "マイリスト削除::-MR-": ProcessDeleteMylist.ProcessDeleteMylist,
                "検索（マイリスト名）::-MR-": ProcessSearch.ProcessMylistSearch,
                "検索（動画名）::-MR-": ProcessSearch.ProcessMylistSearchFromVideo,
                "強調表示を解除::-MR-": ProcessSearch.ProcessMylistSearchClear,
                "情報表示::-MR-": PopupWindowMain.PopupMylistWindow,
                "-LIST-+DOUBLE CLICK+": ProcessShowMylistInfo.ProcessShowMylistInfo,
                "-CREATE-": ProcessCreateMylist.ProcessCreateMylist,
                "-CREATE_THREAD_DONE-": ProcessCreateMylist.ProcessCreateMylistThreadDone,
                "-DELETE-": ProcessDeleteMylist.ProcessDeleteMylist,
                "-DOWNLOAD-": ProcessDownload.ProcessDownload,
                "-DOWNLOAD_THREAD_DONE-": ProcessDownload.ProcessDownloadThreadDone,
                "-UPDATE-": ProcessUpdateMylistInfo.ProcessUpdateMylistInfo,
                "-UPDATE_THREAD_DONE-": ProcessUpdateMylistInfo.ProcessUpdateMylistInfoThreadDone,
                "-ALL_UPDATE-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo,
                "-ALL_UPDATE_THREAD_PROGRESS-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadProgress,
                "-ALL_UPDATE_THREAD_DONE-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadDone,
                "-PARTIAL_UPDATE-": ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfo,
                "-PARTIAL_UPDATE_THREAD_PROGRESS-": ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfoThreadProgress,
                "-PARTIAL_UPDATE_THREAD_DONE-": ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfoThreadDone,
                "-C_CONFIG_SAVE-": ConfigMain.ProcessConfigSave,
                "-C_MYLIST_SAVE-": ConfigMain.ProcessMylistSaveCSV,
                "-C_MYLIST_LOAD-": ConfigMain.ProcessMylistLoadCSV,
                "-TIMER_SET-": Timer.ProcessTimer,
            }
            self.assertEqual(expect_ep_dict, mw.ep_dict)
        pass

    def test_MakeMainWindowLayout(self):
        """WindowMainのレイアウトをテストする
        """
        pass

    def test_Run(self):
        """WindowMainのメインベントループをテストする
        """
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
