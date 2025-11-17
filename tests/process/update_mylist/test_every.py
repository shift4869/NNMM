import sys
import unittest

from mock import MagicMock
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.every import Every, EveryThreadDone
from nnmm.process.value_objects.process_info import ProcessInfo


class TestEvery(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = Every(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(EveryThreadDone, instance.post_process)
        self.assertEqual("Every mylist", instance.L_KIND)
        self.assertEqual("-ALL_UPDATE_THREAD_DONE-", instance.E_DONE)

    def test_get_target_mylist(self):
        instance = Every(self.process_info)

        expect = "mylist_record"
        instance.mylist_db.select.side_effect = lambda: expect
        actual = instance.get_target_mylist()
        self.assertEqual(expect, actual)
        instance.mylist_db.select.assert_called_once_with()

    def test_thread_done_init(self):
        instance = EveryThreadDone(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual("Every mylist", instance.L_KIND)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
