# coding: utf-8
"""ProcessCreateMylist のテスト
"""

import sys
import unittest
from logging import INFO, getLogger

from NNMM.Process import *


class TestProcessCreateMylist(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_CreateMylistInit(self):
        """ProcessCreateMylistの初期化後の状態をテストする
        """
        pass

    def test_CreateMylistRun(self):
        """ProcessCreateMylistのRunをテストする
        """
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
