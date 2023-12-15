import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_show_mylist_info import ProcessShowMylistInfo
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestProcessShowMylistInfo(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_db(self) -> list[dict]:
        NUM = 5
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i + 1}", "投稿動画", "uploaded", f"投稿者{i + 1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i + 1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", True if i % 2 == 0 else False] for i in range(NUM)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.process_show_mylist_info.logger.info"))
            mock_update_table_pane = stack.enter_context(patch("NNMM.process.process_show_mylist_info.update_table_pane"))

            instance = ProcessShowMylistInfo(self.process_info)

            def pre_run(is_include_new):
                m_list = self._make_mylist_db()
                s_showname = m_list[0]["showname"]
                if is_include_new:
                    NEW_MARK = "*:"
                    s_showname = NEW_MARK + s_showname
                instance.values.reset_mock()
                instance.values.__getitem__.side_effect = lambda key: [s_showname]
                instance.mylist_db.reset_mock()
                instance.mylist_db.select_from_showname.side_effect = lambda showname: [m_list[0]]
                instance.window.reset_mock()
                mock_update_table_pane.reset_mock()

            def post_run(is_include_new):
                self.assertEqual([
                    call.__getitem__("-LIST-")
                ], instance.values.mock_calls)

                m_list = self._make_mylist_db()
                s_showname = m_list[0]["showname"]
                self.assertEqual([
                    call.select_from_showname(s_showname)
                ], instance.mylist_db.mock_calls)

                mylist_url = m_list[0]["url"]
                self.assertEqual([
                    call.__getitem__("-INPUT1-"),
                    call.__getitem__().update(value=mylist_url)
                ], instance.window.mock_calls)

                self.assertEqual([
                    call(instance.window, instance.mylist_db, instance.mylist_info_db, mylist_url)
                ], mock_update_table_pane.mock_calls)

            Params = namedtuple("Params", ["is_include_new", "result"])
            params_list = [
                Params(True, Result.success),
                Params(False, Result.success),
            ]
            for params in params_list:
                pre_run(params.is_include_new)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.is_include_new)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
