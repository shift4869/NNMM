# coding: utf-8
"""PopupWindowMain のテスト
"""

import copy
import shutil
import sys
import unittest
from contextlib import ExitStack
from logging import INFO, getLogger
from mock import MagicMock, patch, mock_open
from pathlib import Path

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase
from NNMM.PopupWindowMain import *


# テスト用具体化PopupWindowBase
class ConcretePopupWindowBase(PopupWindowBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None) -> None:
        super().__init__(log_sflag, log_eflag, process_name)

    def MakeWindowLayout(self, mw) -> list[list[sg.Frame]] | None:
        return mw

    def Init(self, mw) -> int:
        return 0

    def Run(self, mw) -> int:
        return super().Run(mw) if self.process_name == "テスト用具体化処理" else None


class TestPopupWindowMain(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PopupWindowBaseInit(self):
        """PopupWindowMainの初期化後の状態をテストする
        """
        e_log_sflag = True
        e_log_eflag = False
        e_process_name = "テスト用具体化処理"
        cpwb = ConcretePopupWindowBase(e_log_sflag, e_log_eflag, e_process_name)

        self.assertEqual(e_log_sflag, cpwb.log_sflag)
        self.assertEqual(e_log_eflag, cpwb.log_eflag)
        self.assertEqual(e_process_name, cpwb.process_name)

        self.assertEqual(None, cpwb.window)
        self.assertEqual("", cpwb.title)
        self.assertEqual((100, 100), cpwb.size)
        self.assertEqual({}, cpwb.ep_dict)
        pass

    def test_PopupWindowBaseRun(self):
        """PopupWindowMainの子windowイベントループをテストする
        """
        e_log_sflag = True
        e_log_eflag = False
        e_process_name = "テスト用具体化処理"
        cpwb = ConcretePopupWindowBase(e_log_sflag, e_log_eflag, e_process_name)
        cpwb.ep_dict = {"-DO-": ConcretePopupWindowBase}

        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.PopupWindowMain.logger.info"))
            mockwd = stack.enter_context(patch("NNMM.PopupWindowMain.sg.Window"))

            def r_mock_func(title, layout, size, finalize, resizable, modal):
                r_mock = MagicMock()
                v_mock = MagicMock()
                v_mock.side_effect = [("-DO-", "value1"), ("-EXIT-", "value2")]
                type(r_mock).read = v_mock
                type(r_mock).close = lambda s: 0
                return r_mock

            mockwd.side_effect = r_mock_func

            # 正常系
            e_mw = [["dummy window"]]
            res = cpwb.Run(e_mw)
            self.assertEqual(0, res)

            # 異常系
            e_mw = None
            res = cpwb.Run(e_mw)
            self.assertEqual(-1, res)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
