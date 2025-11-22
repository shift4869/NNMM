import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.move_up import MoveUp
from nnmm.process.value_objects.mylist_row import MylistRow, SelectedMylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestMoveUp(unittest.TestCase):
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
            mockli = self.enterContext(patch("nnmm.process.move_up.logger.info"))
            mockle = self.enterContext(patch("nnmm.process.move_up.logger.error"))
            mock_update_mylist_pane = self.enterContext(patch("nnmm.process.move_up.ProcessBase.update_mylist_pane"))
            mock_selected_mylist_row = self.enterContext(
                patch("nnmm.process.move_up.ProcessBase.get_selected_mylist_row")
            )
            mock_selected_mylist_row_index = self.enterContext(
                patch("nnmm.process.move_up.ProcessBase.get_selected_mylist_row_index")
            )
            mock_all_mylist_row = self.enterContext(patch("nnmm.process.move_up.ProcessBase.get_all_mylist_row"))

            instance = MoveUp(self.process_info)

            def pre_run(s_src_index, s_max_index, s_src_v, s_dst_v):
                mock_selected_mylist_row.reset_mock()
                if s_src_v == "":

                    def f():
                        return None

                    mock_selected_mylist_row.side_effect = f
                else:

                    def f():
                        return SelectedMylistRow.create(s_src_v)

                    mock_selected_mylist_row.side_effect = f

                mock_selected_mylist_row_index.reset_mock()
                mock_selected_mylist_row_index.side_effect = lambda: s_src_index

                if s_src_v != "":
                    s_dst_index = s_src_index - 1
                    list_data = {
                        s_src_index: MylistRow.create(s_src_v),
                        s_dst_index: MylistRow.create(s_dst_v),
                    }
                    mock_all_mylist_row.reset_mock()
                    mock_all_mylist_row.side_effect = lambda: list_data

                instance.mylist_db.reset_mock()

                def return_record(showname):
                    if showname in s_src_v:
                        return [{"id": s_src_index}]
                    if showname in s_dst_v:
                        return [{"id": s_dst_index}]

                instance.mylist_db.select_from_showname.side_effect = return_record
                instance.mylist_db.swap_id.reset_mock()
                mock_update_mylist_pane.reset_mock()
                instance.window.reset_mock()

            def post_run(s_src_index, s_max_index, s_src_v, s_dst_v):
                if s_src_v == "":
                    self.assertEqual(
                        [
                            call(),
                        ],
                        mock_selected_mylist_row.mock_calls,
                    )
                    mock_selected_mylist_row_index.assert_not_called()
                    instance.mylist_db.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    return
                else:
                    self.assertEqual(
                        [
                            call(),
                        ],
                        mock_selected_mylist_row.mock_calls,
                    )

                if s_src_index == 0:
                    instance.mylist_db.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    return

                s_dst_index = s_src_index - 1
                self.assertEqual(
                    [
                        call.__getitem__("-LIST-"),
                        call.__getitem__().update(set_to_index=s_dst_index),
                    ],
                    instance.window.mock_calls,
                )

                if s_src_v.startswith("*:"):
                    s_src_v = s_src_v[2:]
                if s_dst_v.startswith("*:"):
                    s_dst_v = s_dst_v[2:]
                self.assertEqual(
                    [
                        call.select_from_showname(s_src_v),
                        call.select_from_showname(s_dst_v),
                        call.swap_id(s_src_index, s_dst_index),
                    ],
                    instance.mylist_db.mock_calls,
                )

                mock_update_mylist_pane.assert_called_once_with()

            showname_1 = "投稿者1さんの投稿動画"
            showname_2 = "投稿者2さんの投稿動画"
            params_list = [
                (1, 1, showname_1, showname_2, Result.success),
                (1, 1, "*:" + showname_1, showname_2, Result.success),
                (1, 1, showname_1, "*:" + showname_2, Result.success),
                (1, 1, "*:" + showname_1, "*:" + showname_2, Result.success),
                (0, 1, showname_1, showname_2, Result.failed),
                (1, 1, "", showname_2, Result.failed),
            ]
            for params in params_list:
                pre_run(params[0], params[1], params[2], params[3])
                actual = instance.run()
                expect = params[-1]
                self.assertIs(expect, actual)
                post_run(params[0], params[1], params[2], params[3])
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
