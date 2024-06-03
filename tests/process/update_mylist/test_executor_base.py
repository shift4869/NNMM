import sys
import unittest

import PySimpleGUI as sg
from mock import MagicMock

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.executor_base import ExecutorBase
from nnmm.process.update_mylist.value_objects.payload_list import PayloadList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result
from nnmm.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


class ConcreteExecutorBase(ExecutorBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def execute(self) -> PayloadList:
        return []

    def execute_worker(self, *argv) -> FetchedVideoInfo | Result:
        return []


class TestExecutorBase(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = ConcreteExecutorBase(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(self.process_info.window, instance.window)
        self.assertEqual(self.process_info.values, instance.values)
        self.assertEqual(self.process_info.mylist_db, instance.mylist_db)
        self.assertEqual(self.process_info.mylist_info_db, instance.mylist_info_db)

        self.assertIsNotNone(instance.lock)
        self.assertEqual(0, instance.done_count)

        with self.assertRaises(ValueError):
            instance = ConcreteExecutorBase("invalid")

    def test_execute(self):
        instance = ConcreteExecutorBase(self.process_info)
        actual = instance.execute()
        self.assertEqual([], actual)

    def test_execute_worker(self):
        instance = ConcreteExecutorBase(self.process_info)
        actual = instance.execute_worker()
        self.assertEqual([], actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
