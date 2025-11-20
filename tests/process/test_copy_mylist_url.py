import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.copy_mylist_url import CopyMylistUrl
from nnmm.process.value_objects.mylist_row import SelectedMylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestCopyMylistUrl(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch("nnmm.process.copy_mylist_url.logger"))
            mock_pyperclip = stack.enter_context(patch("nnmm.process.copy_mylist_url.pyperclip"))
            mock_selected_mylist_row = stack.enter_context(
                patch("nnmm.process.copy_mylist_url.ProcessBase.get_selected_mylist_row")
            )
            instance = CopyMylistUrl(self.process_info)

            def pre_run(s_values):
                mock_selected_mylist_row.reset_mock()
                if s_values == "":

                    def f():
                        return None

                    mock_selected_mylist_row.side_effect = f
                else:

                    def f():
                        return SelectedMylistRow.create(s_values)

                    mock_selected_mylist_row.side_effect = f

                instance.mylist_db.reset_mock()

                def return_record(showname):
                    return [{"url": "dummy_mylist_url"}]

                instance.mylist_db.select_from_showname.side_effect = return_record
                instance.window.reset_mock()
                mock_pyperclip.reset_mock()

            def post_run(s_values):
                if s_values == "":
                    self.assertEqual(
                        [
                            call(),
                        ],
                        mock_selected_mylist_row.mock_calls,
                    )
                    instance.mylist_db.assert_not_called()
                    mock_pyperclip.assert_not_called()
                    instance.window.assert_not_called()
                    return
                else:
                    self.assertEqual(
                        [
                            call(),
                        ],
                        mock_selected_mylist_row.mock_calls,
                    )

                if s_values.startswith("*:"):
                    s_values = s_values[2:]
                self.assertEqual(
                    [
                        call.select_from_showname(s_values),
                    ],
                    instance.mylist_db.mock_calls,
                )
                self.assertEqual(
                    [
                        call.copy("dummy_mylist_url"),
                    ],
                    mock_pyperclip.mock_calls,
                )
                self.assertEqual(
                    [
                        call.__getitem__("-INPUT2-"),
                        call.__getitem__().update(value=f"マイリストURLコピー成功！"),
                    ],
                    instance.window.mock_calls,
                )

            showname_1 = "投稿者1さんの投稿動画"
            Params = namedtuple("Params", ["s_values", "result"])
            params_list = [
                Params(showname_1, Result.success),
                Params("*:" + showname_1, Result.success),
                Params("", Result.failed),
            ]
            for params in params_list:
                pre_run(params.s_values)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.s_values)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
