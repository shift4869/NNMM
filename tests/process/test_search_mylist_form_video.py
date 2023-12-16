import re
import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_search import ProcessMylistSearchFromVideo
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestProcessMylistSearchFromVideo(unittest.TestCase):
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

    def _make_mylist_info_db(self, mylist_url) -> list[dict]:
        NUM = 5
        res = []

        m = -1
        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        if re.search(pattern, mylist_url):
            m = int(re.search(pattern, mylist_url)[1])
        if m == -1:
            return []

        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded", "video_url", "mylist_url"]
        table_rows = [[i, f"sm{m}000000{i + 1}", f"動画タイトル{m}_{i + 1}", f"投稿者{m}", "",
                       "2022-02-01 02:30:00",
                       f"https://www.nicovideo.jp/watch/sm{m}000000{i + 1}",
                       f"https://www.nicovideo.jp/user/1000000{m}/video"] for i in range(NUM)]

        for rows in table_rows:
            d = {}
            for r, c in zip(rows, table_cols):
                d[c] = r
            res.append(d)
        return res

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.process_search.logger.info"))
            mock_popup_get_text = stack.enter_context(patch("NNMM.process.process_search.popup_get_text"))
            mock_window = MagicMock()
            mock_mylist_db = MagicMock()
            mock_mylist_info_db = MagicMock()

            instance = ProcessMylistSearchFromVideo(self.process_info)

            def pre_run(pattern, get_indexes, is_include_new, is_hit):
                mock_popup_get_text.reset_mock()
                mock_popup_get_text.side_effect = lambda message: pattern

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
                mock_mylist_db.reset_mock()
                mock_mylist_db.select.side_effect = lambda: m_list
                instance.mylist_db.reset_mock()
                instance.mylist_db = mock_mylist_db

                def _make_records(mylist_url):
                    records = self._make_mylist_info_db(mylist_url)
                    if not is_hit:
                        records = [r | {"title": "no_hit"} for r in records]
                    return records
                mock_mylist_info_db.reset_mock()
                mock_mylist_info_db.select_from_mylist_url.side_effect = _make_records
                instance.mylist_info_db.reset_mock()
                instance.mylist_info_db = mock_mylist_info_db

            def post_run(pattern, get_indexes, is_include_new, is_hit):
                self.assertEqual([
                    call("動画名検索（正規表現可）")
                ], mock_popup_get_text.mock_calls)

                if pattern is None or pattern == "":
                    instance.window.assert_not_called()
                    mock_window.assert_not_called()
                    mock_mylist_db.assert_not_called()
                    return

                index = get_indexes
                expect_mylist_info_db_calls = []
                expect_window_calls = [call.get_indexes()]
                if get_indexes >= 0:
                    expect_window_calls.append(call.get_indexes())

                m_list = self._make_mylist_db()
                if is_include_new:
                    m_list = [m | {"is_include_new": True} for m in m_list]

                def _make_records(mylist_url):
                    records = self._make_mylist_info_db(mylist_url)
                    if not is_hit:
                        records = [r | {"title": "no_hit"} for r in records]
                    return records

                NEW_MARK = "*:"
                include_new_index_list = []
                match_index_list = []
                for i, m in enumerate(m_list):
                    if m["is_include_new"]:
                        m["showname"] = NEW_MARK + m["showname"]
                        include_new_index_list.append(i)
                    mylist_url = m["url"]
                    records = _make_records(mylist_url)
                    expect_mylist_info_db_calls.append(
                        call.select_from_mylist_url(mylist_url)
                    )
                    for r in records:
                        if re.findall(pattern, r["title"]):
                            match_index_list.append(i)
                            index = i
                list_data = [m["showname"] for m in m_list]
                expect_window_calls.append(call.update(values=list_data))
                for i in include_new_index_list:
                    expect_window_calls.append(
                        call.Widget.itemconfig(i, fg="black", bg="light pink")
                    )
                for i in match_index_list:
                    expect_window_calls.append(
                        call.Widget.itemconfig(i, fg="black", bg="light goldenrod")
                    )
                expect_window_calls.append(call.Widget.see(index))
                expect_window_calls.append(call.update(set_to_index=index))
                if len(match_index_list) > 0:
                    expect_window_calls.append(
                        call.update(value=f"{len(match_index_list)}件ヒット！")
                    )
                else:
                    expect_window_calls.append(
                        call.update(value="該当なし")
                    )
                self.assertEqual(expect_window_calls, mock_window.mock_calls)

                self.assertEqual(
                    expect_mylist_info_db_calls, mock_mylist_info_db.mock_calls
                )

                self.assertEqual([
                    call.select()
                ], mock_mylist_db.mock_calls)

            Params = namedtuple("Params", ["pattern", "get_indexes", "is_include_new", "is_hit", "result"])
            params_list = [
                Params("動画タイトル1_1", 0, True, True, Result.success),
                Params("not found", 0, True, True, Result.success),
                Params("動画タイトル1_1", -1, True, True, Result.success),
                Params("動画タイトル1_1", 0, False, True, Result.success),
                Params("動画タイトル1_1", 0, True, False, Result.success),
                Params("", 0, True, True, Result.failed),
            ]
            for params in params_list:
                pre_run(params.pattern, params.get_indexes, params.is_include_new, params.is_hit)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.pattern, params.get_indexes, params.is_include_new, params.is_hit)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
