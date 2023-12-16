import sys
import unittest
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_search import ProcessVideoSearchClear
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestProcessVideoSearchClear(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.process_search.logger.info"))
            mock_update_table_pane = stack.enter_context(patch("NNMM.process.process_search.update_table_pane"))
            
            instance = ProcessVideoSearchClear(self.process_info)
            mylist_url = "mylist_url_1"
            instance.window.__getitem__.return_value.get = lambda: mylist_url

            actual = instance.run()
            self.assertIs(Result.success, actual)
            mock_update_table_pane.assert_called_once_with(
                instance.window, instance.mylist_db, instance.mylist_info_db, mylist_url
            )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
