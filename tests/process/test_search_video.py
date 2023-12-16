import re
import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_search import ProcessVideoSearch
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestProcessVideoSearch(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_info_db(self, mylist_url) -> list[list[dict]]:
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

            instance = ProcessVideoSearch(self.process_info)

            def pre_run(pattern, values, is_hit):
                mock_popup_get_text.reset_mock()
                mock_popup_get_text.side_effect = lambda message: pattern

                instance.values.reset_mock()
                if values:
                    instance.values.__getitem__.side_effect = lambda key: [values]
                else:
                    instance.values.__getitem__.side_effect = lambda key: []

                mylist_url = "https://www.nicovideo.jp/user/10000001/video"
                records = self._make_mylist_info_db(mylist_url)
                if not is_hit:
                    records = [r | {"title": "no_hit"} for r in records]
                records = [list(r.values()) for r in records]

                mock_window.reset_mock()
                mock_window.Values = records
                instance.window.reset_mock()
                instance.window.__getitem__.side_effect = lambda key: mock_window

            def post_run(pattern, values, is_hit):
                self.assertEqual([
                    call("動画名検索（正規表現可）")
                ], mock_popup_get_text.mock_calls)

                if pattern is None or pattern == "":
                    instance.values.assert_not_called()
                    instance.window.assert_not_called()
                    mock_window.assert_not_called()
                    return

                index = values
                expect_window_calls = []

                mylist_url = "https://www.nicovideo.jp/user/10000001/video"
                records = self._make_mylist_info_db(mylist_url)
                if not is_hit:
                    records = [r | {"title": "no_hit"} for r in records]
                records = [list(r.values()) for r in records]

                match_index_list = []
                for i, r in enumerate(records):
                    if re.findall(pattern, r[2]):
                        match_index_list.append(i)
                        index = i
                row_colors_data = [(i, "black", "light goldenrod") for i in match_index_list]
                expect_window_calls.append(call.update(row_colors=row_colors_data))

                expect_window_calls.append(call.Widget.see(index + 1))
                if match_index_list:
                    expect_window_calls.append(
                        call.update(select_rows=match_index_list)
                    )
                else:
                    expect_window_calls.append(
                        call.update(select_rows=[index])
                    )

                if len(match_index_list) > 0:
                    expect_window_calls.append(
                        call.update(value=f"{len(match_index_list)}件ヒット！")
                    )
                else:
                    expect_window_calls.append(
                        call.update(value="該当なし")
                    )
                self.assertEqual(expect_window_calls, mock_window.mock_calls)

            Params = namedtuple("Params", ("pattern", "values", "is_hit", "result"))
            params_list = [
                Params("動画タイトル1_1", 1, True, Result.success),
                Params("not found", 1, True, Result.success),
                Params("動画タイトル1_1", 0, True, Result.success),
                Params("動画タイトル1_1", 1, False, Result.success),
                Params("動画タイトル1_1", 1, True, Result.success),
                Params("", 1, True, Result.failed),
            ]
            for params in params_list:
                pre_run(params.pattern, params.values, params.is_hit)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.pattern, params.values, params.is_hit)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
