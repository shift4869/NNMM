import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack
from copy import deepcopy

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.value_objects.mylist_row import SelectedMylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.watched_mylist import WatchedMylist
from nnmm.util import Result


class TestWatchedMylist(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_db(self, num: int = 5) -> list[dict]:
        res = []
        col = [
            "id",
            "username",
            "mylistname",
            "type",
            "showname",
            "url",
            "created_at",
            "updated_at",
            "checked_at",
            "check_interval",
            "is_include_new",
        ]
        rows = [
            [
                i,
                f"投稿者{i + 1}",
                "投稿動画",
                "uploaded",
                f"投稿者{i + 1}さんの投稿動画",
                f"https://www.nicovideo.jp/user/1000000{i + 1}/video",
                "2022-02-01 02:30:00",
                "2022-02-01 02:30:00",
                "2022-02-01 02:30:00",
                "15分",
                i % 2 == 0,
            ]
            for i in range(num)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("nnmm.process.watched_mylist.logger.info"))
            mockle = stack.enter_context(patch("nnmm.process.watched_mylist.logger.error"))
            mock_selected_mylist_row = stack.enter_context(
                patch("nnmm.process.watched_mylist.ProcessBase.get_selected_mylist_row")
            )
            mock_update_mylist_pane = stack.enter_context(
                patch("nnmm.process.watched_mylist.ProcessBase.update_mylist_pane")
            )
            mock_update_table_pane = stack.enter_context(
                patch("nnmm.process.watched_mylist.ProcessBase.update_table_pane")
            )

            instance = WatchedMylist(self.process_info)

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]

            def pre_run(s_values, is_include_new):
                mock_selected_mylist_row.reset_mock()
                if s_values:

                    def f():
                        return SelectedMylistRow.create(s_values)

                    mock_selected_mylist_row.side_effect = f
                else:

                    def f():
                        return None

                    mock_selected_mylist_row.side_effect = f

                s_m_list = deepcopy(m_list)
                s_m_list[0]["is_include_new"] = is_include_new
                instance.mylist_db.reset_mock()
                instance.mylist_db.select_from_showname.side_effect = lambda showname: s_m_list

                instance.mylist_info_db.reset_mock()
                mock_update_mylist_pane.reset_mock()
                mock_update_table_pane.reset_mock()

            def post_run(s_values, is_include_new):
                self.assertEqual([call()], mock_selected_mylist_row.mock_calls)
                if not s_values:
                    instance.mylist_db.assert_not_called()
                    instance.mylist_info_db.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    mock_update_table_pane.assert_not_called()
                    return

                NEW_MARK = "*:"
                if s_values[:2] == NEW_MARK:
                    s_values = s_values[2:]
                if is_include_new:
                    self.assertEqual(
                        [call.select_from_showname(s_values), call.update_include_flag(mylist_url, False)],
                        instance.mylist_db.mock_calls,
                    )
                else:
                    self.assertEqual([call.select_from_showname(s_values)], instance.mylist_db.mock_calls)
                    instance.mylist_info_db.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    mock_update_table_pane.assert_not_called()
                    return

                self.assertEqual([call.update_status_in_mylist(mylist_url, "")], instance.mylist_info_db.mock_calls)

                mock_update_mylist_pane.assert_called_once_with()
                mock_update_table_pane.assert_called_once_with("")

            Params = namedtuple("Params", ["s_values", "is_include_new", "result"])
            showname_1 = "投稿者1さんの投稿動画"
            params_list = [
                Params(showname_1, True, Result.success),
                Params("*:" + showname_1, True, Result.success),
                Params(showname_1, False, Result.failed),
                Params("", True, Result.failed),
            ]
            for params in params_list:
                pre_run(*params[:-1])
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(*params[:-1])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
