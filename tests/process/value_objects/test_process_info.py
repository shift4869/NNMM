import sys
import unittest

import PySimpleGUI as sg
from mock import MagicMock

from NNMM.main_window import MainWindow
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.value_objects.process_info import ProcessInfo


class TestProcessInfo(unittest.TestCase):
    def test_init(self):
        process_name = "-TEST_PROCESS-"
        window = MagicMock(spec=sg.Window)
        values = MagicMock(spec=dict)
        mylist_db = MagicMock(spec=MylistDBController)
        mylist_info_db = MagicMock(spec=MylistInfoDBController)
        actual = ProcessInfo(
            process_name,
            window,
            values,
            mylist_db,
            mylist_info_db
        )
        self.assertEqual(process_name, actual.name)
        self.assertEqual(window, actual.window)
        self.assertEqual(values, actual.values)
        self.assertEqual(mylist_db, actual.mylist_db)
        self.assertEqual(mylist_info_db, actual.mylist_info_db)

        params_list = [
            (-1, window, values, mylist_db, mylist_info_db),
            (process_name, -1, values, mylist_db, mylist_info_db),
            (process_name, window, -1, mylist_db, mylist_info_db),
            (process_name, window, values, -1, mylist_info_db),
            (process_name, window, values, mylist_db, -1),
        ]
        for params in params_list:
            with self.assertRaises(ValueError):
                actual = ProcessInfo(
                    params[0],
                    params[1],
                    params[2],
                    params[3],
                    params[4]
                )

    def test_repr(self):
        process_name = "-TEST_PROCESS-"
        window = MagicMock(spec=sg.Window)
        values = MagicMock(spec=dict)
        mylist_db = MagicMock(spec=MylistDBController)
        mylist_info_db = MagicMock(spec=MylistInfoDBController)
        process_info = ProcessInfo(
            process_name,
            window,
            values,
            mylist_db,
            mylist_info_db
        )
        actual = repr(process_info)

        name_str = f"name={process_name}"
        window_str = f"window={id(window)}"
        values_str = f"values={id(values)}"
        mylist_db_str = f"mylist_db={id(mylist_db)}"
        mylist_info_db_str = f"mylist_info_db={id(mylist_info_db)}"
        expect = f"ProcessInfo({name_str}, {window_str}, {values_str}, {mylist_db_str}, {mylist_info_db_str})"
        self.assertEqual(expect, actual)

    def test_create(self):
        process_name = "-TEST_PROCESS-"
        window = MagicMock(spec=sg.Window)
        values = MagicMock(spec=dict)
        mylist_db = MagicMock(spec=MylistDBController)
        mylist_info_db = MagicMock(spec=MylistInfoDBController)

        def return_main_window(window_flag = True,
                               values_flag = True,
                               mylist_db_flag = True,
                               mylist_info_db_flag = True):
            mock_main_window = MagicMock(spec=MainWindow)
            if window_flag:
                mock_main_window.window = window
            if values_flag:
                mock_main_window.values = values
            if mylist_db_flag:
                mock_main_window.mylist_db = mylist_db
            if mylist_info_db_flag:
                mock_main_window.mylist_info_db = mylist_info_db
            return mock_main_window
        main_window = return_main_window()
        actual = ProcessInfo.create(process_name, main_window)
        expect = ProcessInfo(
            process_name,
            window,
            values,
            mylist_db,
            mylist_info_db
        )
        self.assertEqual(expect, actual)

        params_list = [
            (False, True, True, True),
            (True, False, True, True),
            (True, True, False, True),
            (True, True, True, False),
        ]
        for params in params_list:
            main_window = return_main_window(params[0], params[1], params[2], params[3])
            with self.assertRaises(ValueError):
                actual = ProcessInfo.create(process_name, main_window)

if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
