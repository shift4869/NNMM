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

            mockcpg.side_effect = lambda: {"db": {"save_path": TEST_DB_PATH}}
            
            def r_mock_window(title, layout, size, finalize, resizable):
                r_mock = MagicMock()
                b_mock = MagicMock()
                type(b_mock).bind = lambda s, b, k: f"{b}_{k}"
                r_mock = {"-LIST-": b_mock}
                return r_mock
            mockwd.side_effect = r_mock_window
            mw = MainWindow()
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
