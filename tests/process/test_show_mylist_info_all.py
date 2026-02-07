import sys
import unittest
from collections import namedtuple

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.show_mylist_info_all import ShowMylistInfoAll
from nnmm.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestShowMylistInfoAll(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.show_mylist_info_all.logger.info"))
        self.enterContext(patch("nnmm.process.show_mylist_info_all.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> ShowMylistInfoAll:
        instance = ShowMylistInfoAll(self.process_info)
        return instance

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

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)

    def test_component(self):
        instance = self._get_instance()
        actual = instance.create_component()
        self.assertIsNone(actual)

    def test_callback(self) -> Result:
        Params = namedtuple(
            "Params",
            [
                "kind_get_selected_mylist_row_index",
                "kind_video_info_list",
                "result",
            ],
        )

        def pre_run(params: Params) -> ShowMylistInfoAll:
            instance = self._get_instance()
            instance.get_selected_mylist_row_index = MagicMock()
            instance.set_upper_textbox = MagicMock()
            instance.set_all_table_row = MagicMock()
            instance.mylist_info_db = MagicMock()
            instance.window.list_widget = MagicMock()
            instance.window.table_widget = MagicMock()

            if params.kind_get_selected_mylist_row_index == "valid":
                instance.get_selected_mylist_row_index.return_value = SelectedMylistRowIndex(0)
            else:  # "invalid"
                instance.get_selected_mylist_row_index.return_value = None

            mylist_info = self._make_mylist_info_db()
            if params.kind_get_selected_mylist_row_index == "valid":
                instance.mylist_info_db.select.return_value = mylist_info
            else:  # "empty"
                instance.mylist_info_db.select.return_value = []

            return instance

        def post_run(actual: Result, instance: ShowMylistInfoAll, params: Params) -> None:
            self.assertEqual(params.result, actual)

            instance.get_selected_mylist_row_index.assert_called_once_with()

            instance.mylist_info_db.select.assert_called_once_with()
            instance.set_upper_textbox.assert_called_once_with("", False)
            instance.window.list_widget.setCurrentRow.assert_called_once_with(0)
            instance.set_all_table_row.assert_called()

            if params.kind_get_selected_mylist_row_index == "valid":
                instance.window.table_widget.selectRow.assert_called_once_with(0)
            else:  # "empty"
                instance.window.table_widget.selectRow.assert_not_called()

        params_list = [
            Params("valid", "valid", Result.success),
            Params("valid", "empty", Result.success),
            Params("invalid", "valid", Result.success),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
