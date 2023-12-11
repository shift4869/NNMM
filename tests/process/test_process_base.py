import sys
import unittest

import PySimpleGUI as sg
from mock import MagicMock

from NNMM.main_window import MainWindow
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo


class ConcreteProcessBase(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> None:
        return


class TestProcessBase(unittest.TestCase):
    def test_init(self):
        process_name = "-TEST_PROCESS-"
        main_window = MagicMock(spec=MainWindow)
        main_window.window = MagicMock(spec=sg.Window)
        main_window.values = MagicMock(spec=dict)
        main_window.mylist_db = MagicMock(spec=MylistDBController)
        main_window.mylist_info_db = MagicMock(spec=MylistInfoDBController)
        process_info = ProcessInfo.create(process_name, main_window)
        process_base = ConcreteProcessBase(process_info)

        self.assertEqual(process_name, process_base.name)
        self.assertEqual(process_info, process_base.process_info)
        self.assertEqual(process_info.window, process_base.window)
        self.assertEqual(process_info.values, process_base.values)
        self.assertEqual(process_info.mylist_db, process_base.mylist_db)
        self.assertEqual(process_info.mylist_info_db, process_base.mylist_info_db)

        with self.assertRaises(ValueError):
            process_base = ConcreteProcessBase("invalid_process_info")

    def test_run(self):
        process_name = "-TEST_PROCESS-"
        main_window = MagicMock(spec=MainWindow)
        main_window.window = MagicMock(spec=sg.Window)
        main_window.values = MagicMock(spec=dict)
        main_window.mylist_db = MagicMock(spec=MylistDBController)
        main_window.mylist_info_db = MagicMock(spec=MylistInfoDBController)
        process_info = ProcessInfo.create(process_name, main_window)
        process_base = ConcreteProcessBase(process_info)

        actual = process_base.run()
        self.assertEqual(None, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
