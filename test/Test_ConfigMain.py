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
        cpb = ConcreteProcessConfigBase(True, True, "")
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
