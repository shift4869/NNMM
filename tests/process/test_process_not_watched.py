import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack
from copy import deepcopy

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_not_watched import ProcessNotWatched
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestProcessNotWatched(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.process_not_watched.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.process_not_watched.logger.error"))
            mock_update_table_pane = stack.enter_context(patch("NNMM.process.process_not_watched.update_table_pane"))
            mock_update_mylist_pane = stack.enter_context(patch("NNMM.process.process_not_watched.update_mylist_pane"))
            mock_update_status = MagicMock()
            mock_window = MagicMock()

            def_data = [[
                "1", 
                "sm12346578", 
                "title_1", 
                "username_1", 
                "", 
                "2023-12-13 07:25:00",
                "2023-12-13 07:25:00",
                "https://www.nicovideo.jp/watch/sm12346578",
                "https://www.nicovideo.jp/user/11111111/video"
            ]]
            instance = ProcessNotWatched(self.process_info)
            def pre_run(s_value, s_update_status):
                s_def_data = deepcopy(def_data)
                mock_window.reset_mock()
                instance.window.reset_mock()
                mock_window.Values = s_def_data
                instance.window.__getitem__.side_effect = lambda key: mock_window

                instance.values.reset_mock()
                if s_value == -1:
                    instance.values.__getitem__.side_effect = lambda key: []
                else:
                    values_dict = {
                        "-TABLE-": [s_value],
                        "-INPUT1-": s_def_data[0][8],
                    }
                    instance.values.__getitem__.side_effect = lambda key: values_dict[key]

                mock_update_status.reset_mock()
                instance.mylist_info_db.reset_mock()
                mock_update_status.side_effect = lambda video_id, mylist_url, status: s_update_status
                instance.mylist_info_db.update_status = mock_update_status
                mock_update_table_pane.reset_mock()
                mock_update_mylist_pane.reset_mock()

            def post_run(s_value, s_update_status):
                if s_value == -1:
                    self.assertEqual([
                        call("-TABLE-"),
                    ], instance.values.__getitem__.mock_calls)
                    self.assertEqual([
                        call("-TABLE-"),
                    ], instance.window.__getitem__.mock_calls)
                    mock_update_status.assert_not_called()
                    mock_update_table_pane.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    return
                else:
                    self.assertEqual([
                        call("-TABLE-"),
                        call("-TABLE-"),
                        call("-TABLE-"),
                        call("-INPUT1-"),
                    ], instance.values.__getitem__.mock_calls)

                s_def_data = deepcopy(def_data)
                s_def_data[s_value][4] = "未視聴"
                self.assertEqual([
                    call.update(values=s_def_data),
                    call.update(select_rows=[s_value])
                ], mock_window.mock_calls)

                self.assertEqual([
                    call(s_def_data[s_value][1], s_def_data[s_value][8], "未視聴")
                ], mock_update_status.mock_calls)

                mylist_url = s_def_data[0][8]
                self.assertEqual([
                    call(
                        instance.window,
                        instance.mylist_db,
                        instance.mylist_info_db,
                        mylist_url
                    )
                ], mock_update_table_pane.mock_calls)

                self.assertEqual([
                    call(instance.window, instance.mylist_db)
                ], mock_update_mylist_pane.mock_calls)

            Params = namedtuple("Params", ["value", "update_status", "result"])
            params_list = [
                Params(0, 0, Result.success),
                Params(0, 1, Result.success),
                Params(-1, 0, Result.failed),
            ]
            for params in params_list:
                pre_run(params.value, params.update_status)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.value, params.update_status)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
