import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog, QVBoxLayout

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.popup import PopupMylistWindow
from nnmm.process.value_objects.mylist_row import MylistRow, SelectedMylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestPopupMylistWindow(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.popup.logger.info"))
        self.enterContext(patch("nnmm.process.popup.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_record(self, s_check_interval: str = "15分", s_is_include_new: bool = False) -> dict:
        return {
            "id": 0,
            "username": "username_1",
            "mylistname": "mylistname_1",
            "type": "uploaded",
            "showname": "showname_1",
            "url": "url_1",
            "created_at": "2025-11-21 12:34:56",
            "updated_at": "2025-11-22 12:34:56",
            "checked_at": "2025-11-23 12:34:56",
            "check_interval": s_check_interval,
            "check_failed_count": 0,
            "is_include_new": s_is_include_new,
        }

    def _make_valid_components(self, record: dict):
        """update_mylist_info に必要なキーを満たすコンポーネント辞書を返す"""
        for key, value in record.items():
            record[key] = str(value)

        unit_list = ["分", "時間", "日", "週間", "ヶ月"]
        check_interval = record["check_interval"]
        check_interval_num = -1
        check_interval_unit = ""
        t = str(check_interval)
        for u in unit_list:
            t = t.replace(u, "")

        check_interval_num = str(int(t))
        check_interval_unit = str(check_interval).replace(str(t), "")

        return {
            "ID": MagicMock(text=MagicMock(return_value=record["id"])),
            "ユーザー名": MagicMock(text=MagicMock(return_value=record["username"])),
            "マイリスト名": MagicMock(text=MagicMock(return_value=record["mylistname"])),
            "種別": MagicMock(text=MagicMock(return_value=record["type"])),
            "表示名": MagicMock(text=MagicMock(return_value=record["showname"])),
            "URL": MagicMock(text=MagicMock(return_value=record["url"])),
            "作成日時": MagicMock(text=MagicMock(return_value=record["created_at"])),
            "更新日時": MagicMock(text=MagicMock(return_value=record["updated_at"])),
            "更新確認日時": MagicMock(text=MagicMock(return_value=record["checked_at"])),
            "更新確認インターバル": {
                "num": MagicMock(currentText=MagicMock(return_value=check_interval_num)),
                "unit": MagicMock(currentText=MagicMock(return_value=check_interval_unit)),
            },
            "更新確認失敗カウント": MagicMock(text=MagicMock(return_value=record["check_failed_count"])),
            "未視聴フラグ": MagicMock(text=MagicMock(return_value=record["is_include_new"])),
        }

    def _check_layout(self, mock_component_dict: dict, instance: PopupMylistWindow) -> None:
        horizontal_line = "-" * 100
        csize = 120
        mock_vbox = mock_component_dict["vbox"]
        mock_label = mock_component_dict["label"]
        mock_lineedit = mock_component_dict["lineedit"]
        mock_hbox = mock_component_dict["hbox"]
        mock_combo = mock_component_dict["combo"]
        mock_btn = mock_component_dict["btn"]

        mock_vbox_rt = mock_vbox.return_value
        mock_label_rt = mock_label.return_value
        mock_lineedit_rt = mock_lineedit.return_value
        mock_hbox_rt = mock_hbox.return_value
        mock_combo_rt = mock_combo.return_value
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
                call().addLayout(mock_hbox_rt),
                call().addLayout(mock_hbox_rt),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_label_rt),
                call().addLayout(mock_hbox_rt),
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
                call().addWidget(mock_combo_rt),
                call().addWidget(mock_combo_rt),
                call().addStretch(1),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call().addWidget(mock_btn_rt),
                call(),
                call().addWidget(mock_label_rt),
                call().addWidget(mock_lineedit_rt),
                call(),
                call().addStretch(0),
                call().addWidget(mock_btn_rt),
                call().addWidget(mock_btn_rt),
            ],
            mock_hbox.mock_calls,
        )

        self.assertEqual(
            [
                call(horizontal_line),
                call("ID"),
                call().setMinimumWidth(csize),
                call("ユーザー名"),
                call().setMinimumWidth(csize),
                call("マイリスト名"),
                call().setMinimumWidth(csize),
                call("種別"),
                call().setMinimumWidth(csize),
                call("表示名"),
                call().setMinimumWidth(csize),
                call("URL"),
                call().setMinimumWidth(csize),
                call("作成日時"),
                call().setMinimumWidth(csize),
                call("更新日時"),
                call().setMinimumWidth(csize),
                call("更新確認日時"),
                call().setMinimumWidth(csize),
                call("更新確認インターバル"),
                call().setMinimumWidth(csize),
                call("更新確認失敗カウント"),
                call().setMinimumWidth(csize),
                call("未視聴フラグ"),
                call().setMinimumWidth(csize),
                call(horizontal_line),
                call(" "),
            ],
            mock_label.mock_calls,
        )

        r = instance.record
        id_index = r["id"]
        username = r["username"]
        mylistname = r["mylistname"]
        typename = r["type"]
        showname = r["showname"]
        url = r["url"]
        created_at = r["created_at"]
        updated_at = r["updated_at"]
        checked_at = r["checked_at"]
        check_failed_count = r["check_failed_count"]
        is_include_new = "True" if r["is_include_new"] else "False"

        unit_list = ["分", "時間", "日", "週間", "ヶ月"]
        check_interval = r["check_interval"]
        check_interval_num = -1
        check_interval_unit = ""
        t = str(check_interval)
        for u in unit_list:
            t = t.replace(u, "")
        check_interval_num = int(t)
        check_interval_unit = str(check_interval).replace(str(t), "")

        self.assertEqual(
            [
                call(str(id_index), readOnly=True),
                call(str(username), readOnly=True),
                call(str(mylistname), readOnly=True),
                call(str(typename), readOnly=True),
                call(str(showname), readOnly=True),
                call(str(url), readOnly=True),
                call(str(created_at), readOnly=True),
                call(str(updated_at), readOnly=True),
                call(str(checked_at), readOnly=True),
                call(str(check_failed_count)),
                call().setStyleSheet("QLineEdit {background-color: olive;}"),
                call(str(is_include_new), readOnly=True),
            ],
            mock_lineedit.mock_calls,
        )

        self.assertEqual(
            [
                call(),
                call().addItems([str(i) for i in range(1, 60)]),
                call().setCurrentText(str(check_interval_num)),
                call().setStyleSheet("QComboBox {background-color: olive;}"),
                call(),
                call().addItems(unit_list),
                call().setCurrentText(check_interval_unit),
                call().setStyleSheet("QComboBox {background-color: olive;}"),
            ],
            mock_combo.mock_calls,
        )

        btn_check_list = [
            call("リセット") in mock_btn.mock_calls,
            call("保存して閉じる") in mock_btn.mock_calls,
            call("保存しないで閉じる") in mock_btn.mock_calls,
        ]
        self.assertTrue(all(btn_check_list))
        self.assertEqual(len(btn_check_list), mock_btn_rt.clicked.connect.call_count)

        self.assertEqual(
            [
                "ID",
                "ユーザー名",
                "マイリスト名",
                "種別",
                "表示名",
                "URL",
                "作成日時",
                "更新日時",
                "更新確認日時",
                "更新確認インターバル",
                "更新確認失敗カウント",
                "未視聴フラグ",
            ],
            list(instance.component.keys()),
        )
        self.assertEqual(
            ["num", "unit"],
            list(instance.component["更新確認インターバル"].keys()),
        )
        self.assertEqual(mock_lineedit_rt, instance.component["ID"])
        self.assertEqual(mock_lineedit_rt, instance.component["ユーザー名"])
        self.assertEqual(mock_lineedit_rt, instance.component["マイリスト名"])
        self.assertEqual(mock_lineedit_rt, instance.component["種別"])
        self.assertEqual(mock_lineedit_rt, instance.component["表示名"])
        self.assertEqual(mock_lineedit_rt, instance.component["URL"])
        self.assertEqual(mock_lineedit_rt, instance.component["作成日時"])
        self.assertEqual(mock_lineedit_rt, instance.component["更新日時"])
        self.assertEqual(mock_lineedit_rt, instance.component["更新確認日時"])
        self.assertEqual({"num": mock_combo_rt, "unit": mock_combo_rt}, instance.component["更新確認インターバル"])
        self.assertEqual(mock_lineedit_rt, instance.component["更新確認失敗カウント"])
        self.assertEqual(mock_lineedit_rt, instance.component["未視聴フラグ"])

    def test_init(self):
        showname = "testさんの投稿動画"
        Params = namedtuple("Params", ["kind_selected_mylist_row", "kind_select_from_showname", "result"])

        def pre_run(params: Params) -> PopupMylistWindow:
            instance = PopupMylistWindow(self.process_info)
            instance.get_selected_mylist_row = MagicMock()
            if params.kind_selected_mylist_row == "valid":
                instance.get_selected_mylist_row.return_value = SelectedMylistRow.create(showname)
            elif params.kind_selected_mylist_row == "valid_new":
                instance.get_selected_mylist_row.return_value = SelectedMylistRow.create(MylistRow.NEW_MARK + showname)
            else:
                instance.get_selected_mylist_row.return_value = None

            instance.mylist_db.select_from_showname = MagicMock()
            if params.kind_select_from_showname == "valid":
                instance.mylist_db.select_from_showname.return_value = [self._make_record()]
            else:
                instance.mylist_db.select_from_showname.return_value = None
            return instance

        def post_run(actual, instance: PopupMylistWindow, params: Params) -> None:
            self.assertEqual(params.result, actual)
            instance.get_selected_mylist_row.assert_called_once_with()
            if params.kind_selected_mylist_row not in ["valid", "valid_new"]:
                return

            instance.mylist_db.select_from_showname.assert_called_once_with(showname)
            if params.kind_select_from_showname != "valid":
                return

            expect = instance.mylist_db.select_from_showname.return_value
            self.assertEqual(expect[0], instance.record)
            self.assertEqual(expect[0]["url"], instance.url)
            self.assertEqual("マイリスト情報", instance.title)

        params_list = [
            Params("valid", "valid", Result.success),
            Params("valid_new", "valid", Result.success),
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
        mock_combo = self.enterContext(patch("nnmm.process.popup.QComboBox"))
        mock_btn = self.enterContext(patch("nnmm.process.popup.QPushButton"))
        Params = namedtuple("Params", ["kind_record", "check_interval"])

        def pre_run(params: Params) -> PopupMylistWindow:
            instance = PopupMylistWindow(self.process_info)
            if params.kind_record == "valid_record":
                instance.record = self._make_record(s_check_interval=params.check_interval)
            elif params.kind_record == "invalid_record":
                instance.record = {"id": 0}  # 欠損 record
            else:  # "no_record_attribute"
                instance.record = None

            mock_vbox.reset_mock()
            mock_label.reset_mock()
            mock_lineedit.reset_mock()
            mock_hbox.reset_mock()
            mock_combo.reset_mock()
            mock_btn.reset_mock()
            return instance

        def post_run(actual, instance: PopupMylistWindow, params: Params) -> None:
            def check_with_return_none():
                self.assertIsNone(actual)
                mock_vbox.assert_not_called()
                mock_label.assert_not_called()
                mock_lineedit.assert_not_called()
                mock_hbox.assert_not_called()
                mock_combo.assert_not_called()
                mock_btn.assert_not_called()

            if params.kind_record != "valid_record":
                check_with_return_none()
                return None

            # インターバル文字列をパース
            unit_list = ["分", "時間", "日", "週間", "ヶ月"]
            check_interval = params.check_interval
            check_interval_num = -1
            check_interval_unit = ""
            t = str(check_interval)
            for u in unit_list:
                t = t.replace(u, "")

            try:
                check_interval_num = int(t)
                check_interval_unit = str(check_interval).replace(str(t), "")
            except ValueError:
                check_with_return_none()  # キャスト失敗エラー
                return None

            if check_interval_num <= 0:
                check_with_return_none()  # 負の数ならエラー([1-59]の範囲想定)
                return None

            if check_interval_unit not in unit_list:
                check_with_return_none()  # 想定外の単位ならエラー
                return None

            # レイアウト系コンポーネント呼び出し確認
            self._check_layout(
                {
                    "vbox": mock_vbox,
                    "label": mock_label,
                    "lineedit": mock_lineedit,
                    "hbox": mock_hbox,
                    "combo": mock_combo,
                    "btn": mock_btn,
                },
                instance,
            )

            mock_vbox_rt = mock_vbox.return_value
            self.assertIsInstance(actual, QVBoxLayout)
            self.assertEqual(mock_vbox_rt, actual)

        params_list = [
            Params("valid_record", "15分"),  # Success想定
            Params("invalid_record", "15分"),  # Failed想定
            Params("no_record_attribute", "15分"),  # Failed想定
            Params("valid_record", "0分"),  # Failed想定
            Params("valid_record", "1分"),  # Success想定
            Params("valid_record", "59分"),  # Success想定
            Params("valid_record", "60分"),  # Success想定(一応59分までだが60以上が入ってきても許容する)
            Params("valid_record", "-1分"),  # Failed想定
            Params("valid_record", "15分時間日週間ヶ月"),  # invalid unit, Failed想定
            Params("valid_record", "15 cast failed"),  # cast failed, Failed想定
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.create_window_layout()
            post_run(actual, instance, params)

    def test_update_mylist_info(self):
        instance = PopupMylistWindow(self.process_info)
        instance.popup_window = MagicMock()

        # 正常系
        record = self._make_record()
        instance.component = self._make_valid_components(record)

        actual = instance.update_mylist_info()

        self.assertEqual(Result.success, actual)
        self.assertEqual(
            [
                call.upsert(
                    record["id"],
                    record["username"],
                    record["mylistname"],
                    record["type"],
                    record["showname"],
                    record["url"],
                    record["created_at"],
                    record["updated_at"],
                    record["checked_at"],
                    record["check_interval"],
                    record["check_failed_count"],
                    record["is_include_new"] == "True",
                )
            ],
            instance.mylist_db.mock_calls,
        )
        instance.popup_window.close.assert_called_once()

        instance.mylist_db.reset_mock()
        instance.popup_window.reset_mock()

        # 異常系: インターバル文字列が不正
        record = self._make_record()
        record["check_interval"] = "-1分"
        instance.component = self._make_valid_components(record)

        actual = instance.update_mylist_info()

        self.assertEqual(Result.failed, actual)
        instance.mylist_db.assert_not_called()
        instance.popup_window.close.assert_called_once()

        instance.mylist_db.reset_mock()
        instance.popup_window.reset_mock()

        # 異常系: componentが必要なキーを持っていない
        record = self._make_record()
        instance.component = self._make_valid_components(record)
        del instance.component["ID"]

        actual = instance.update_mylist_info()

        self.assertEqual(Result.failed, actual)
        instance.mylist_db.assert_not_called()
        instance.popup_window.close.assert_called_once()

        instance.mylist_db.reset_mock()
        instance.popup_window.reset_mock()

        # 異常系: component属性が無い
        del instance.component

        actual = instance.update_mylist_info()

        self.assertEqual(Result.failed, actual)
        instance.mylist_db.assert_not_called()
        instance.popup_window.close.assert_called_once()

        instance.mylist_db.reset_mock()
        instance.popup_window.reset_mock()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
    unittest.main(warnings="ignore")
