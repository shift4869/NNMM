import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.popup import PopupMylistWindow, PopupMylistWindowSave
from NNMM.process.value_objects.mylist_row import SelectedMylistRow
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestPopupMylistWindow(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_record(self, s_check_interval, s_is_include_new) -> dict:
        return {
            "id": 0,
            "username": "username_1",
            "mylistname": "mylistname_1",
            "type": "uploaded",
            "showname": "showname_1",
            "url": "url_1",
            "created_at": "2023-12-13 12:34:56",
            "updated_at": "2023-12-13 12:34:56",
            "checked_at": "2023-12-13 12:34:56",
            "check_interval": s_check_interval,
            "check_failed_count": 0,
            "is_include_new": s_is_include_new,
        }

    def _make_expect_window_layout(self, record, window_title) -> list[list[sg.Frame]]:
        horizontal_line = "-" * 132
        csize = (20, 1)
        tsize = (50, 1)
        thsize = (5, 1)

        r = record
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

        cf = [
            [sg.Text(horizontal_line)],
            [
                sg.Text("ID", size=csize, visible=False),
                sg.Input(f"{id_index}", key="-ID_INDEX-", visible=False, readonly=True, size=tsize),
            ],
            [sg.Text("ユーザー名", size=csize), sg.Input(f"{username}", key="-USERNAME-", readonly=True, size=tsize)],
            [
                sg.Text("マイリスト名", size=csize),
                sg.Input(f"{mylistname}", key="-MYLISTNAME-", readonly=True, size=tsize),
            ],
            [sg.Text("種別", size=csize), sg.Input(f"{typename}", key="-TYPE-", readonly=True, size=tsize)],
            [sg.Text("表示名", size=csize), sg.Input(f"{showname}", key="-SHOWNAME-", readonly=True, size=tsize)],
            [sg.Text("URL", size=csize), sg.Input(f"{url}", key="-URL-", readonly=True, size=tsize)],
            [
                sg.Text("作成日時", size=csize),
                sg.Input(f"{created_at}", key="-CREATED_AT-", readonly=True, size=tsize),
            ],
            [
                sg.Text("更新日時", size=csize),
                sg.Input(f"{updated_at}", key="-UPDATED_AT-", readonly=True, size=tsize),
            ],
            [
                sg.Text("更新確認日時", size=csize),
                sg.Input(f"{checked_at}", key="-CHECKED_AT-", readonly=True, size=tsize),
            ],
            [
                sg.Text("更新確認インターバル", size=csize),
                sg.InputCombo(
                    [i for i in range(1, 60)],
                    default_value=check_interval_num,
                    key="-CHECK_INTERVAL_NUM-",
                    background_color="light goldenrod",
                    size=thsize,
                ),
                sg.InputCombo(
                    unit_list,
                    default_value=check_interval_unit,
                    key="-CHECK_INTERVAL_UNIT-",
                    background_color="light goldenrod",
                    size=thsize,
                ),
            ],
            [
                sg.Text("更新確認失敗カウント", size=csize),
                sg.Input(f"{check_failed_count}", key="-CHECK_FAILED_COUNT-", readonly=True, size=tsize),
            ],
            [
                sg.Text("未視聴フラグ", size=csize),
                sg.Input(f"{is_include_new}", key="-IS_INCLUDE_NEW-", readonly=True, size=tsize),
            ],
            [sg.Text(horizontal_line)],
            [sg.Text("")],
            [sg.Text("")],
            [sg.Column([[sg.Button("保存", key="-SAVE-"), sg.Button("閉じる", key="-EXIT-")]], justification="right")],
        ]
        layout = [[sg.Frame(window_title, cf)]]
        return layout

    def _assert_layout(self, e, a) -> None:
        # typeチェック
        self.assertEqual(type(e), type(a))
        # イテラブルなら再起
        if hasattr(e, "__iter__") and hasattr(a, "__iter__"):
            self.assertEqual(len(e), len(a))
            for e1, a1 in zip(e, a):
                self._assert_layout(e1, a1)
        # Rows属性を持つなら再起
        if hasattr(e, "Rows") and hasattr(a, "Rows"):
            for e2, a2 in zip(e.Rows, a.Rows):
                self._assert_layout(e2, a2)
        # 要素チェック
        if hasattr(a, "RightClickMenu") and a.RightClickMenu:
            self.assertEqual(e.RightClickMenu, a.RightClickMenu)
        if hasattr(a, "ColumnHeadings") and a.ColumnHeadings:
            self.assertEqual(e.ColumnHeadings, a.ColumnHeadings)
        if hasattr(a, "ButtonText") and a.ButtonText:
            self.assertEqual(e.ButtonText, a.ButtonText)
        if hasattr(a, "DisplayText") and a.DisplayText:
            self.assertEqual(e.DisplayText, a.DisplayText)
        if hasattr(a, "Key") and a.Key:
            self.assertEqual(e.Key, a.Key)
        return

    def test_init(self):
        with ExitStack() as stack:
            mock_logger_error = stack.enter_context(patch("NNMM.process.popup.logger.error"))
            mock_selected_mylist_row = stack.enter_context(
                patch("NNMM.process.popup.ProcessBase.get_selected_mylist_row")
            )

            instance = PopupMylistWindow(self.process_info)

            def pre_run(s_value, s_record):
                instance.record = None
                instance.title = None
                instance.size = None
                instance.process_dict = None

                mock_selected_mylist_row.reset_mock()
                if s_value:

                    def f():
                        return SelectedMylistRow.create(s_value)

                    mock_selected_mylist_row.side_effect = f
                else:

                    def f():
                        return None

                    mock_selected_mylist_row.side_effect = f

                instance.mylist_db.reset_mock()
                instance.mylist_db.select_from_showname.side_effect = lambda showname: s_record

            def post_run(s_value, s_record):
                self.assertEqual([call()], mock_selected_mylist_row.mock_calls)
                if s_value and len(s_value) > 0:
                    pass
                else:
                    instance.mylist_db.assert_not_called()
                    self.assertIsNone(instance.record)
                    self.assertIsNone(instance.title)
                    self.assertIsNone(instance.size)
                    self.assertIsNone(instance.process_dict)
                    return

                NEW_MARK = "*:"
                if s_value[:2] == NEW_MARK:
                    s_value = s_value[2:]

                self.assertEqual([call.select_from_showname(s_value)], instance.mylist_db.mock_calls)
                if s_record and len(s_record) == 1:
                    s_record = s_record[0]
                else:
                    self.assertIsNone(instance.record)
                    self.assertIsNone(instance.title)
                    self.assertIsNone(instance.size)
                    self.assertIsNone(instance.process_dict)
                    return

                self.assertEqual(s_record, instance.record)
                self.assertEqual("マイリスト情報", instance.title)
                self.assertEqual((580, 490), instance.size)
                self.assertEqual(
                    {
                        "-SAVE-": PopupMylistWindowSave,
                    },
                    instance.process_dict,
                )

            Params = namedtuple("Params", ["value", "record", "result"])
            showname_1 = "投稿者1さんの投稿動画"
            params_list = [
                Params(showname_1, ["record_1"], Result.success),
                Params("*:" + showname_1, ["record_1"], Result.success),
                Params(None, ["record_1"], Result.failed),
                Params(showname_1, None, Result.failed),
            ]
            for params in params_list:
                pre_run(params.value, params.record)
                actual = instance.init()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.value, params.record)

    def test_make_window_layout(self):
        instance = PopupMylistWindow(self.process_info)

        def pre_run(has_record_flag, valid_record_flag, s_check_interval, s_is_include_new):
            instance.record = None
            instance.title = "マイリスト情報"
            instance.size = (580, 450)
            instance.process_dict = {
                "-SAVE-": PopupMylistWindowSave,
            }

            if not has_record_flag:
                return

            if not valid_record_flag:
                instance.record = {"invalid_key": "invalid_value"}
                return

            instance.record = self._make_record(s_check_interval, s_is_include_new)

        Params = namedtuple(
            "Params", ["has_record_flag", "valid_record_flag", "s_check_interval", "s_is_include_new", "result_func"]
        )
        params_list = [
            Params(True, True, "15分", True, self._make_expect_window_layout),
            Params(True, True, "15分", False, self._make_expect_window_layout),
            Params(False, True, "15分", True, None),
            Params(True, False, "15分", True, None),
            Params(True, True, "invalid分", True, None),
            Params(True, True, "-1分", True, None),
            Params(True, True, "15", True, None),
        ]
        for params in params_list:
            pre_run(params.has_record_flag, params.valid_record_flag, params.s_check_interval, params.s_is_include_new)
            actual = instance.make_window_layout()
            record = self._make_record(params.s_check_interval, params.s_is_include_new)
            if callable(params.result_func):
                expect = params.result_func(record, instance.title)
                self._assert_layout(expect, actual)
            else:
                self.assertIs(None, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
