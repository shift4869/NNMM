import sys
import unittest

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.search import VideoSearchClear
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestVideoSearchClear(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.search.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> VideoSearchClear:
        instance = VideoSearchClear(self.process_info)
        return instance

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)

    def test_create_component(self):
        instance = self._get_instance()
        self.assertIsNone(instance.create_component())

    def test_callback(self):
        instance = self._get_instance()
        instance.update_table_pane = MagicMock()
        instance.get_upper_textbox = MagicMock()

        self.assertEqual(Result.success, instance.callback())

        self.assertEqual([call(), call().to_str()], instance.get_upper_textbox.mock_calls)
        rt = instance.get_upper_textbox.return_value.to_str.return_value
        instance.update_table_pane.assert_called_once_with(rt)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
