import re
import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_search import ProcessMylistSearchFromMylistURL
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestProcessMylistSearchFromMylistURL(unittest.TestCase):
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
                 "15分", False] for i in range(NUM)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.process_search.logger.info"))
            mock_popup_get_text = stack.enter_context(patch("NNMM.process.process_search.popup_get_text"))
            mock_window = MagicMock()
            mock_mylist_db = MagicMock()

            instance = ProcessMylistSearchFromMylistURL(self.process_info)

            def pre_run(search_mylist_url, get_indexes, is_include_new, is_hit):
                mock_popup_get_text.reset_mock()
                mock_popup_get_text.side_effect = lambda message: search_mylist_url

                mock_window.reset_mock()
                if get_indexes >= 0:
                    mock_window.get_indexes.side_effect = lambda: [get_indexes]
                else:
                    mock_window.get_indexes.side_effect = lambda: []
                instance.window.reset_mock()
                instance.window.__getitem__.side_effect = lambda key: mock_window

                m_list = self._make_mylist_db()
                if is_include_new:
                    m_list = [m | {"is_include_new": True} for m in m_list]
                if not is_hit:
                    m_list = [m | {"url": "no_hit"} for m in m_list]
                mock_mylist_db.reset_mock()
                mock_mylist_db.select.side_effect = lambda: m_list
                instance.mylist_db.reset_mock()
                instance.mylist_db = mock_mylist_db

            def post_run(search_mylist_url, get_indexes, is_include_new, is_hit):
                self.assertEqual([
                    call("マイリストURL入力（完全一致）")
                ], mock_popup_get_text.mock_calls)

                if search_mylist_url is None or search_mylist_url == "":
                    instance.window.assert_not_called()
                    mock_window.assert_not_called()
                    mock_mylist_db.assert_not_called()
                    return

                index = get_indexes
                expect_calls = [call.get_indexes()]
                if get_indexes >= 0:
                    expect_calls.append(call.get_indexes())

                m_list = self._make_mylist_db()
                if is_include_new:
                    m_list = [m | {"is_include_new": True} for m in m_list]
                if not is_hit:
                    m_list = [m | {"url": "no_hit"} for m in m_list]
                NEW_MARK = "*:"
                include_new_index_list = []
                match_index_list = []
                for i, m in enumerate(m_list):
                    if m["is_include_new"]:
                        m["showname"] = NEW_MARK + m["showname"]
                        include_new_index_list.append(i)
                    if search_mylist_url == m["url"]:
                        match_index_list.append(i)
                        index = i
                list_data = [m["showname"] for m in m_list]
                expect_calls.append(call.update(values=list_data))
                for i in include_new_index_list:
                    expect_calls.append(
                        call.Widget.itemconfig(i, fg="black", bg="light pink")
                    )
                for i in match_index_list:
                    expect_calls.append(
                        call.Widget.itemconfig(i, fg="black", bg="light goldenrod")
                    )
                expect_calls.append(call.Widget.see(index))
                expect_calls.append(call.update(set_to_index=index))
                if len(match_index_list) > 0:
                    expect_calls.append(
                        call.update(value=f"{len(match_index_list)}件ヒット！")
                    )
                else:
                    expect_calls.append(
                        call.update(value="該当なし")
                    )
                self.assertEqual(expect_calls, mock_window.mock_calls)

                self.assertEqual([
                    call.select()
                ], mock_mylist_db.mock_calls)

            search_mylist_url = "https://www.nicovideo.jp/user/10000001/video"
            Params = namedtuple("Params", ["search_mylist_url", "get_indexes", "is_include_new", "is_hit", "result"])
            params_list = [
                Params(search_mylist_url, 0, True, True, Result.success),
                Params("not found", 0, True, True, Result.success),
                Params(search_mylist_url, -1, True, True, Result.success),
                Params(search_mylist_url, 0, False, True, Result.success),
                Params(search_mylist_url, 0, True, False, Result.success),
                Params("", 0, True, True, Result.failed),
            ]
            for params in params_list:
                pre_run(params.search_mylist_url, params.get_indexes, params.is_include_new, params.is_hit)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.search_mylist_url, params.get_indexes, params.is_include_new, params.is_hit)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
