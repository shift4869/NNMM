import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.show_mylist_info_all import ShowMylistInfoAll
from nnmm.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row_list import TableRowList
from nnmm.util import Result


class TestShowMylistInfoAll(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_info_db(self) -> list[dict]:
        NUM = 5
        res = []
        table_cols = [
            "no",
            "video_id",
            "title",
            "username",
            "status",
            "uploaded_at",
            "registered_at",
            "video_url",
            "mylist_url",
        ]
        n = 0
        for k in range(NUM):
            table_rows = [
                [
                    n,
                    f"sm{k + 1}000000{i + 1}",
                    f"動画タイトル{k + 1}_{i + 1}",
                    f"投稿者{k + 1}",
                    "",
                    f"2022-02-01 0{k + 1}:00:0{i + 1}",
                    f"2022-02-01 0{k + 1}:01:0{i + 1}",
                    f"https://www.nicovideo.jp/watch/sm{k + 1}000000{i + 1}",
                    f"https://www.nicovideo.jp/user/1000000{k + 1}/video",
                ]
                for i in range(NUM)
            ]
            n = n + 1

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return res

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mockli = self.enterContext(patch("nnmm.process.show_mylist_info_all.logger.info"))
            mock_selected_mylist_row_index = self.enterContext(
                patch("nnmm.process.show_mylist_info_all.ProcessBase.get_selected_mylist_row_index")
            )

            instance = ShowMylistInfoAll(self.process_info)

            def pre_run(s_index, not_empty_records):
                mock_selected_mylist_row_index.reset_mock()
                if s_index >= 0:

                    def f():
                        return SelectedMylistRowIndex(s_index)

                    mock_selected_mylist_row_index.side_effect = f
                else:
                    mock_selected_mylist_row_index.side_effect = lambda: None

                video_info_list = self._make_mylist_info_db()
                instance.mylist_info_db.reset_mock()
                if not_empty_records:
                    instance.mylist_info_db.select.side_effect = lambda: video_info_list
                else:
                    instance.mylist_info_db.select.side_effect = lambda: []
                instance.window.reset_mock()

            def post_run(s_index, not_empty_records):
                expect_window_call = []
                index = 0
                if s_index >= 0:
                    index = s_index

                expect_window_call.extend([
                    call.__getitem__("-INPUT1-"),
                    call.__getitem__().update(value=""),
                    call.__getitem__("-LIST-"),
                    call.__getitem__().update(set_to_index=index),
                ])
                if not_empty_records:
                    NUM = 100
                    video_info_list = self._make_mylist_info_db()
                    records = sorted(video_info_list, key=lambda x: int(x["video_id"][2:]), reverse=True)[0:NUM]
                    table_row_list = []
                    for i, r in enumerate(records):
                        a = [
                            i + 1,
                            r["video_id"],
                            r["title"],
                            r["username"],
                            r["status"],
                            r["uploaded_at"],
                            r["registered_at"],
                            r["video_url"],
                            r["mylist_url"],
                        ]
                        table_row_list.append(a)
                    def_data = TableRowList.create(table_row_list)
                    expect_window_call.extend([
                        call.__getitem__("-TABLE-"),
                        call.__getitem__().update(values=def_data.to_table_data()),
                        call.__getitem__("-TABLE-"),
                        call.__getitem__().update(select_rows=[0]),
                    ])
                else:
                    def_data = TableRowList.create([])
                    expect_window_call.extend([
                        call.__getitem__("-TABLE-"),
                        call.__getitem__().update(values=def_data.to_table_data()),
                    ])
                expect_window_call.extend([
                    call.__getitem__("-TABLE-"),
                    call.__getitem__().update(row_colors=[(0, "", "")]),
                ])
                self.assertEqual(expect_window_call, instance.window.mock_calls)

                self.assertEqual([call.select()], instance.mylist_info_db.mock_calls)

            Params = namedtuple("Params", ["index", "not_empty_records", "result"])
            params_list = [
                Params(0, True, Result.success),
                Params(1, True, Result.success),
                Params(-1, True, Result.success),
                Params(0, False, Result.success),
            ]
            for params in params_list:
                pre_run(params.index, params.not_empty_records)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.index, params.not_empty_records)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
