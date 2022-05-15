# coding: utf-8
"""ProcessBase のテスト
"""
import sys
import unittest

from NNMM.Process import ProcessBase


# テスト用具体化ProcessBase
class ConcreteProcessBase(ProcessBase.ProcessBase):
    
    def __init__(self, log_sflag: bool, log_eflag: bool, process_name: str) -> None:
        super().__init__(log_sflag, log_eflag, process_name)

    def Run(self, mw) -> int:
        return 0


class TestProcessBase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ProcessBaseInit(self):
        """ProcessBaseの初期化後の状態をテストする
        """
        e_log_sflag = True
        e_log_eflag = False
        e_process_name = "テスト用具体化処理"
        cpb = ConcreteProcessBase(e_log_sflag, e_log_eflag, e_process_name)

        self.assertEqual(e_log_sflag, cpb.log_sflag)
        self.assertEqual(e_log_eflag, cpb.log_eflag)
        self.assertEqual(e_process_name, cpb.process_name)
        self.assertEqual(None, cpb.main_window)

    def test_ProcessBaseRun(self):
        """ProcessBaseのRunをテストする
        """
        e_log_sflag = True
        e_log_eflag = False
        e_process_name = "テスト用具体化処理"
        cpb = ConcreteProcessBase(e_log_sflag, e_log_eflag, e_process_name)

        e_mw = "dummy window"
        actual = cpb.Run(e_mw)
        self.assertEqual(0, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
