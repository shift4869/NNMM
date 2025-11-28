import re
import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

import nnmm.process.search
from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.search import VideoSearch
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row_index_list import TableRowIndexList
from nnmm.process.value_objects.table_row_list import TableRowList
from nnmm.util import Result


class TestVideoSearch(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.search.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> VideoSearch:
        instance = VideoSearch(self.process_info)
        return instance

    def _make_mylist_db(self) -> list[dict]:
        NUM = 5
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
                "2025-11-28 12:34:56",
                "2025-11-28 12:34:56",
                "2025-11-28 12:34:56",
                "15分",
                True if i % 2 == 0 else False,
            ]
            for i in range(NUM)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_mylist_info_db(self, mylist_url) -> list[dict]:
        NUM = 5
        res = []

        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        m = int(re.search(pattern, mylist_url)[1])

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
            "created_at",
        ]
        table_rows = [
            [
                i,
                f"sm{m}000000{i + 1}",
                f"動画タイトル{m}_{i + 1}",
                f"投稿者{m}",
                "",
                "2025-11-01 02:30:00",
                "2025-11-02 02:30:00",
                f"https://www.nicovideo.jp/watch/sm{m}000000{i + 1}",
                f"https://www.nicovideo.jp/user/1000000{m}/video",
                "2025-11-03 02:30:00",
            ]
            for i in range(NUM)
        ]

        for rows in table_rows:
            d = {}
            for r, c in zip(rows, table_cols):
                d[c] = r
            res.append(d)
        return res

    def _make_table_row(self, mylist_url) -> list[list[str]]:
        records = []
        video_info_list = self._make_mylist_info_db(mylist_url)
        for video_info in video_info_list:
            record = video_info
            record["no"] = record["no"] + 1  # 1ベース
            del record["created_at"]
            records.append(list(record.values()))
        return records

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)

    def test_create_component(self):
        instance = self._get_instance()
        self.assertIsNone(instance.create_component())

    def test_callback(self):
        mock_popup_get_text = self.enterContext(patch("nnmm.process.search.popup_get_text"))
        mock_qtable_widget_item = self.enterContext(patch("nnmm.process.search.QTableWidgetItem"))
        self.enterContext(patch("nnmm.process.search.time"))

        Params = namedtuple("Params", ["pattern", "kind_all_table_row", "is_hit", "result"])

        def pre_run(params: Params) -> VideoSearch:
            instance = VideoSearch(self.process_info)
            mock_popup_get_text.reset_mock()
            mock_popup_get_text.side_effect = lambda message: params.pattern

            instance.get_all_table_row = MagicMock()
            if params.kind_all_table_row == "valid":
                mylist_url = self._make_mylist_db()[0]["url"]
                records = self._make_table_row(mylist_url)
                if not params.is_hit:
                    for record in records:
                        record[2] = "no_hit"
                instance.get_all_table_row.return_value = TableRowList.create(records)
            elif params.kind_all_table_row == "invalid_col":
                mock_row = MagicMock()
                mock_row.to_row.return_value = []
                instance.get_all_table_row.return_value = [mock_row]
            else:  # "invalid_row"
                instance.get_all_table_row.return_value = []

            instance.window = MagicMock()

            mock_qtable_widget_item.reset_mock()
            instance.set_bottom_textbox = MagicMock()
            return instance

        def post_run(actual: Result, instance: VideoSearch, params: Params) -> None:
            self.assertEqual(params.result, actual)
            self.assertEqual([call("動画名検索（正規表現可）")], mock_popup_get_text.mock_calls)

            if params.pattern is None or params.pattern == "":
                instance.get_all_table_row.assert_not_called()
                instance.window.assert_not_called()
                mock_qtable_widget_item.assert_not_called()
                instance.set_bottom_textbox.assert_not_called()
                return

            instance.get_all_table_row.assert_called_once_with()

            if params.kind_all_table_row != "valid":
                instance.window.assert_not_called()
                mock_qtable_widget_item.assert_not_called()
                instance.set_bottom_textbox.assert_called_once_with("該当なし")
                return

            mylist_url = self._make_mylist_db()[0]["url"]
            records = self._make_table_row(mylist_url)
            if not params.is_hit:
                for record in records:
                    record[2] = "no_hit"
            table_row_list = TableRowList.create(records)

            n = len(table_row_list)
            m = len(table_row_list[0].to_row())
            table_cols_name = [
                "No.",
                "動画ID",
                "動画名",
                "投稿者",
                "状況",
                "投稿日時",
                "登録日時",
                "動画URL",
                "所属マイリストURL",
            ]
            table_widget_calls = [
                call.table_widget.clearContents(),
                call.table_widget.setRowCount(0),
                call.table_widget.setColumnCount(0),
                call.table_widget.setRowCount(n),
                call.table_widget.setColumnCount(m),
                call.table_widget.setHorizontalHeaderLabels(table_cols_name),
                call.table_widget.verticalHeader(),
                call.table_widget.verticalHeader().hide(),
            ]
            cols_width = [35, 100, 350, 100, 60, 120, 120, 30, 30]
            for i, section_size in enumerate(cols_width):
                table_widget_calls.append(call.table_widget.horizontalHeader())
                table_widget_calls.append(
                    call.table_widget.horizontalHeader().setSectionResizeMode(
                        i, nnmm.process.search.QHeaderView.ResizeMode.Interactive
                    )
                )
                table_widget_calls.append(call.table_widget.horizontalHeader())
                table_widget_calls.append(call.table_widget.horizontalHeader().resizeSection(i, section_size))

            table_item_calls = []

            match_index_list = []
            for i, table_row in enumerate(table_row_list):
                if is_hit := re.findall(params.pattern, table_row.title.name):
                    match_index_list.append(i)
                row = table_row.to_row()
                for j, text in enumerate(row):
                    if is_hit:
                        table_item_calls.append(call(text))
                        table_item_calls.append(call().setBackground(nnmm.process.search.MATCHED_MYLIST_COLOR))
                        table_widget_calls.append(
                            call.table_widget.setItem(i, j, mock_qtable_widget_item.return_value)
                        )
                    else:
                        table_item_calls.append(call(text))
                        table_widget_calls.append(
                            call.table_widget.setItem(i, j, mock_qtable_widget_item.return_value)
                        )

            if len(match_index_list) > 0:
                table_widget_calls.append(call.table_widget.selectRow(match_index_list[-1]))
                instance.set_bottom_textbox.assert_called_once_with(f"{len(match_index_list)}件ヒット！")
            else:
                instance.set_bottom_textbox.assert_called_once_with("該当なし")

            self.assertEqual(table_widget_calls, instance.window.mock_calls)
            self.assertEqual(table_item_calls, mock_qtable_widget_item.mock_calls)

        params_list = [
            Params("動画タイトル1_1", "valid", True, Result.success),
            Params("動画タイトル1_1", "valid", False, Result.success),
            Params("not found", "valid", True, Result.success),
            Params("動画タイトル1_1", "invalid_col", True, Result.failed),
            Params("動画タイトル1_1", "invalid_row", True, Result.failed),
            Params("", "valid", True, Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
