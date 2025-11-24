import re
import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.popup import PopupVideoWindow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from nnmm.process.value_objects.table_row_list import SelectedTableRowList
from nnmm.util import Result


class TestPopupVideoWindow(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.popup.logger.info"))
        self.enterContext(patch("nnmm.process.popup.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_info_db(self, mylist_url) -> list[list[dict]]:
        # mylist_info_db から select した返り値を模倣する
        # 内部で扱う形式の list[list[dict(str, Any)]] を返す
        NUM = 5
        res = []

        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        m = int(re.search(pattern, mylist_url)[1])

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
            "作成日時",
        ]
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

    def _make_table_row_list(self) -> list[list[str]]:
        # テーブルウィジェットの選択行を模倣する
        NUM = 5
        m = 1
        table_row_list = [
            [
                i + 1,  # 行番号は1ベース
                f"sm{m}000000{i + 1}",
                f"動画タイトル{m}_{i + 1}",
                f"投稿者{m}",
                "",
                "2025-11-01 02:30:00",
                "2025-11-02 02:30:00",
                f"https://www.nicovideo.jp/watch/sm{m}000000{i + 1}",
                f"https://www.nicovideo.jp/user/1000000{m}/video",
                # "2025-11-03 02:30:00",
            ]
            for i in range(NUM)
        ]
        return table_row_list

    def _check_layout(self, mock_component_dict: dict, instance: PopupVideoWindow) -> None:
        horizontal_line = "-" * 100
        csize = 100
        mock_vbox = mock_component_dict["vbox"]
        mock_label = mock_component_dict["label"]
        mock_lineedit = mock_component_dict["lineedit"]
        mock_hbox = mock_component_dict["hbox"]
        mock_btn = mock_component_dict["btn"]

        mock_vbox_rt = mock_vbox.return_value
        mock_label_rt = mock_label.return_value
        mock_lineedit_rt = mock_lineedit.return_value
        mock_hbox_rt = mock_hbox.return_value
        mock_btn_rt = mock_btn.return_value

        self.assertEqual(
            [
                call(),
                call().addWidget(mock_label_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_btn_rt, alignment=Qt.AlignmentFlag.AlignRight),
            ],
            mock_vbox.mock_calls,
        )

        self.assertEqual(
            [
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
            ],
            mock_hbox.mock_calls,
        )

        self.assertEqual(
            [
                call(horizontal_line),
                call("ID"),
                call().setMinimumWidth(csize),
                call("動画ID"),
                call().setMinimumWidth(csize),
                call("動画名"),
                call().setMinimumWidth(csize),
                call("投稿者"),
                call().setMinimumWidth(csize),
                call("状況"),
                call().setMinimumWidth(csize),
                call("投稿日時"),
                call().setMinimumWidth(csize),
                call("登録日時"),
                call().setMinimumWidth(csize),
                call("動画URL"),
                call().setMinimumWidth(csize),
                call("所属マイリストURL"),
                call().setMinimumWidth(csize),
                call("作成日時"),
                call().setMinimumWidth(csize),
                call(horizontal_line),
                call(" "),
            ],
            mock_label.mock_calls,
        )

        r = instance.record
        id_index = r["id"]
        video_id = r["video_id"]
        title = r["title"]
        username = r["username"]
        status = r["status"]
        uploaded_at = r["uploaded_at"]
        registered_at = r["registered_at"]
        video_url = r["video_url"]
        mylist_url = r["mylist_url"]
        created_at = r["created_at"]

        self.assertEqual(
            [
                call(str(id_index), readOnly=True),
                call(video_id, readOnly=True),
                call(title, readOnly=True),
                call(username, readOnly=True),
                call(status, readOnly=True),
                call(uploaded_at, readOnly=True),
                call(registered_at, readOnly=True),
                call(video_url, readOnly=True),
                call(mylist_url, readOnly=True),
                call(created_at, readOnly=True),
            ],
            mock_lineedit.mock_calls,
        )

    def test_init(self):
        selected_table_row = 2
        mylist_url = f"https://www.nicovideo.jp/user/1000000{selected_table_row}/video"
        Params = namedtuple("Params", ["kind_selected_table_row", "kind_select_from_showname", "result"])

        def pre_run(params: Params) -> PopupVideoWindow:
            instance = PopupVideoWindow(self.process_info)
            instance.get_selected_table_row_index_list = MagicMock()
            instance.get_selected_table_row_list = MagicMock()
            if params.kind_selected_table_row == "valid":
                instance.get_selected_table_row_index_list.return_value = SelectedTableRowIndexList.create([
                    selected_table_row
                ])
                instance.get_selected_table_row_list.return_value = SelectedTableRowList.create(
                    self._make_table_row_list()
                )
            else:
                instance.get_selected_table_row_index_list.return_value = None
                instance.get_selected_table_row_list.return_value = None

            instance.mylist_info_db.select_from_id_url = MagicMock()
            if params.kind_select_from_showname == "valid":
                instance.mylist_info_db.select_from_id_url.return_value = [
                    self._make_mylist_info_db(mylist_url)[selected_table_row]
                ]
            else:
                instance.mylist_info_db.select_from_id_url.return_value = []
            return instance

        def post_run(actual, instance: PopupVideoWindow, params: Params) -> None:
            self.assertEqual(params.result, actual)
            instance.get_selected_table_row_index_list.assert_called_once_with()
            if params.kind_selected_table_row not in ["valid", "valid_new"]:
                return

            selected_table_row = SelectedTableRowList.create(self._make_table_row_list())[0]
            video_id = selected_table_row.video_id.id
            mylist_url = selected_table_row.mylist_url.non_query_url
            instance.mylist_info_db.select_from_id_url.assert_called_once_with(video_id, mylist_url)
            if params.kind_select_from_showname != "valid":
                return

            expect = instance.mylist_info_db.select_from_id_url.return_value
            self.assertEqual(expect[0], instance.record)
            self.assertEqual(expect[0]["video_url"], instance.url)
            self.assertEqual("動画情報", instance.title)

        params_list = [
            Params("valid", "valid", Result.success),
            Params("invalid", "valid", Result.failed),
            Params("valid", "invalid", Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.init()
            post_run(actual, instance, params)

    def test_create_window_layout(self):
        mock_vbox = self.enterContext(patch("nnmm.process.popup.QVBoxLayout", spec=QVBoxLayout))
        mock_label = self.enterContext(patch("nnmm.process.popup.QLabel"))
        mock_lineedit = self.enterContext(patch("nnmm.process.popup.QLineEdit"))
        mock_hbox = self.enterContext(patch("nnmm.process.popup.QHBoxLayout"))
        mock_btn = self.enterContext(patch("nnmm.process.popup.QPushButton"))

        mylist_url = f"https://www.nicovideo.jp/user/10000001/video"
        selected_row = self._make_mylist_info_db(mylist_url)[0]
        selected_row["id"] = selected_row["no"]
        Params = namedtuple("Params", ["kind_record"])

        def pre_run(params: Params) -> PopupVideoWindow:
            instance = PopupVideoWindow(self.process_info)
            if params.kind_record == "valid_record":
                instance.record = selected_row
            elif params.kind_record == "invalid_record":
                instance.record = {"id": 0}  # 欠損 record
            else:  # "no_record_attribute"
                instance.record = None

            mock_vbox.reset_mock()
            mock_label.reset_mock()
            mock_lineedit.reset_mock()
            mock_hbox.reset_mock()
            mock_btn.reset_mock()
            return instance

        def post_run(actual, instance: PopupVideoWindow, params: Params) -> None:
            def check_with_return_none():
                self.assertIsNone(actual)
                mock_vbox.assert_not_called()
                mock_label.assert_not_called()
                mock_lineedit.assert_not_called()
                mock_hbox.assert_not_called()
                mock_btn.assert_not_called()

            if params.kind_record != "valid_record":
                check_with_return_none()
                return None

            # レイアウト系コンポーネント呼び出し確認
            self._check_layout(
                {
                    "vbox": mock_vbox,
                    "label": mock_label,
                    "lineedit": mock_lineedit,
                    "hbox": mock_hbox,
                    "btn": mock_btn,
                },
                instance,
            )

            mock_vbox_rt = mock_vbox.return_value
            self.assertIsInstance(actual, QVBoxLayout)
            self.assertEqual(mock_vbox_rt, actual)

        params_list = [
            Params("valid_record"),  # Success想定
            Params("invalid_record"),  # Failed想定
            Params("no_record_attribute"),  # Failed想定
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.create_window_layout()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
    unittest.main(warnings="ignore")
