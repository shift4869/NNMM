import sys
import unittest
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.move_up import MoveUp
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestMoveUp(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.move_up.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.move_up.logger.error"))
            mock_update_mylist_pane = stack.enter_context(patch("NNMM.process.move_up.ProcessBase.update_mylist_pane"))
            mock_window = MagicMock()

            instance = MoveUp(self.process_info)
            def pre_run(s_src_index, s_max_index, s_src_v, s_dst_v):
                instance.values.reset_mock()
                if s_src_v == "":
                    instance.values.__getitem__.side_effect = lambda key: []
                else:
                    instance.values.__getitem__.side_effect = lambda key: [s_src_v]

                instance.window.reset_mock()
                mock_window.reset_mock()
                if s_src_index == -1:
                    s_src_index = s_max_index
                    mock_window.get_indexes.side_effect = lambda: 0
                else:
                    mock_window.get_indexes.side_effect = lambda: [s_src_index]
                s_dst_index = s_src_index - 1
                list_data = {
                    s_src_index: s_src_v,
                    s_dst_index: s_dst_v,
                }
                mock_window.Values = list_data
                instance.window.__getitem__.side_effect = lambda key: mock_window

                instance.mylist_db.reset_mock()
                def return_record(showname):
                    if showname in s_src_v:
                        return [{"id": s_src_index}]
                    if showname in s_dst_v:
                        return [{"id": s_dst_index}]

                instance.mylist_db.select_from_showname.side_effect = return_record
                instance.mylist_db.swap_id.reset_mock()
                mock_update_mylist_pane.reset_mock()

            def post_run(s_src_index, s_max_index, s_src_v, s_dst_v):
                if s_src_v == "":
                    self.assertEqual([
                        call("-LIST-"),
                    ], instance.values.__getitem__.mock_calls)
                    mock_window.assert_not_called()
                    instance.mylist_db.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    return
                else:
                    self.assertEqual([
                        call("-LIST-"),
                        call("-LIST-"),
                    ], instance.values.__getitem__.mock_calls)

                if s_src_index == 0:
                    mock_window.assert_not_called()
                    instance.mylist_db.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    return

                if s_src_index == -1:
                    s_src_index = s_max_index
                    s_dst_index = s_src_index - 1
                    self.assertEqual([
                        call.get_indexes(),
                        call.update(set_to_index=s_dst_index),
                    ], mock_window.mock_calls)
                else:
                    s_dst_index = s_src_index - 1
                    self.assertEqual([
                        call.get_indexes(),
                        call.get_indexes(),
                        call.update(set_to_index=s_dst_index),
                    ], mock_window.mock_calls)

                if s_src_v.startswith("*:"):
                    s_src_v = s_src_v[2:]
                if s_dst_v.startswith("*:"):
                    s_dst_v = s_dst_v[2:]
                self.assertEqual([
                    call.select_from_showname(s_src_v),
                    call.select_from_showname(s_dst_v),
                    call.swap_id(s_src_index, s_dst_index),
                ], instance.mylist_db.mock_calls)

                mock_update_mylist_pane.assert_called_once_with()

            params_list = [
                (1, 1, "showname_1", "showname_2", Result.success),
                (1, 1, "*:showname_1", "showname_2", Result.success),
                (1, 1, "showname_1", "*:showname_2", Result.success),
                (1, 1, "*:showname_1", "*:showname_2", Result.success),
                (0, 1, "showname_1", "showname_2", Result.failed),
                (1, 1, "", "showname_2", Result.failed),
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
