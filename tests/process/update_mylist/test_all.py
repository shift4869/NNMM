import sys
import unittest

import PySimpleGUI as sg
from mock import MagicMock

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.all import ProcessUpdateAllMylistInfo, ProcessUpdateAllMylistInfoThreadDone
from NNMM.process.value_objects.process_info import ProcessInfo


class TestProcessUpdateAllMylistInfo(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = ProcessUpdateAllMylistInfo(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(ProcessUpdateAllMylistInfoThreadDone, instance.post_process)
        self.assertEqual("All mylist", instance.L_KIND)
        self.assertEqual("-ALL_UPDATE_THREAD_DONE-", instance.E_DONE)

    def test_get_target_mylist(self):
        instance = ProcessUpdateAllMylistInfo(self.process_info)

        expect = "mylist_record"
        instance.mylist_db.select.side_effect = lambda: expect
        actual = instance.get_target_mylist()
        self.assertEqual(expect, actual)
        instance.mylist_db.select.assert_called_once_with()

    def test_thread_done_init(self):
        instance = ProcessUpdateAllMylistInfoThreadDone(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual("All mylist", instance.L_KIND)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
