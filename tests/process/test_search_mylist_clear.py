import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.search import MylistSearchClear
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestMylistSearchClear(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mockli = self.enterContext(patch("nnmm.process.search.logger.info"))
            mock_update_mylist_pane = self.enterContext(patch("nnmm.process.search.ProcessBase.update_mylist_pane"))
            instance = MylistSearchClear(self.process_info)
            actual = instance.run()
            self.assertIs(Result.success, actual)
            mock_update_mylist_pane.assert_called_once_with()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
