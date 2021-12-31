# coding: utf-8
"""ProcessDeleteMylist のテスト
"""

import sys
import unittest
import warnings
from contextlib import ExitStack
from logging import INFO, getLogger
from mock import MagicMock, patch, AsyncMock

from NNMM.Process import *


class TestProcessDeleteMylist(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PCMRun(self):
        """ProcessDeleteMylistのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessDeleteMylist.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessDeleteMylist.logger.error"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessDeleteMylist.UpdateMylistShow"))
            mockpgt = stack.enter_context(patch("NNMM.Process.ProcessDeleteMylist.sg.popup_ok_cancel"))

            pdm = ProcessDeleteMylist.ProcessDeleteMylist()
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
