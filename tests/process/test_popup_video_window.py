import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack
from copy import deepcopy

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_popup import PopupVideoWindow
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestPopupVideoWindow(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_record(self) -> dict:
        return {
            "id": 0,
            "video_id": "sm12346578",
            "title": "title_1",
            "username": "username_1",
            "status": "mylistname_1",
            "uploaded_at": "2023-12-13 12:34:56",
            "registered_at": "2023-12-13 12:34:56",
            "video_url": "video_url_1",
            "mylist_url": "mylist_url_1",
            "created_at": "2023-12-13 12:34:56",
        }

    def _make_expect_window_layout(self, record, window_title) -> list[list[sg.Frame]]:
        horizontal_line = "-" * 132
        csize = (20, 1)
        tsize = (50, 1)

        r = record
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

        cf = [
            [sg.Text(horizontal_line)],
            [sg.Text("ID", size=csize, visible=False), sg.Input(f"{id_index}", key="-ID_INDEX-", visible=False, readonly=True, size=tsize)],
            [sg.Text("動画ID", size=csize), sg.Input(f"{video_id}", key="-USERNAME-", readonly=True, size=tsize)],
            [sg.Text("動画名", size=csize), sg.Input(f"{title}", key="-MYLISTNAME-", readonly=True, size=tsize)],
            [sg.Text("投稿者", size=csize), sg.Input(f"{username}", key="-TYPE-", readonly=True, size=tsize)],
            [sg.Text("状況", size=csize), sg.Input(f"{status}", key="-SHOWNAME-", readonly=True, size=tsize)],
            [sg.Text("投稿日時", size=csize), sg.Input(f"{uploaded_at}", key="-URL-", readonly=True, size=tsize)],
            [sg.Text("登録日時", size=csize), sg.Input(f"{registered_at}", key="-URL-", readonly=True, size=tsize)],
            [sg.Text("動画URL", size=csize), sg.Input(f"{video_url}", key="-CREATED_AT-", readonly=True, size=tsize)],
            [sg.Text("マイリストURL", size=csize), sg.Input(f"{mylist_url}", key="-UPDATED_AT-", readonly=True, size=tsize)],
            [sg.Text("作成日時", size=csize), sg.Input(f"{created_at}", key="-CHECKED_AT-", readonly=True, size=tsize)],
            [sg.Text(horizontal_line)],
            [sg.Text("")],
            [sg.Column([[sg.Button("閉じる", key="-EXIT-")]], justification="right")],
        ]
        layout = [[
            sg.Frame(window_title, cf)
        ]]
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
            mock_logger_info = stack.enter_context(patch("NNMM.process.process_popup.logger.info"))
            mock_logger_error = stack.enter_context(patch("NNMM.process.process_popup.logger.error"))
            mock_values = MagicMock()
            mock_window = MagicMock()
            mock_mylist_info_db = MagicMock()

            def_data = [[
                "1", 
                "sm12346578", 
                "title_1", 
                "username_1", 
                "", 
                "2023-12-13 07:25:00",
                "2023-12-13 07:25:00",
                "https://www.nicovideo.jp/watch/sm12346578",
                "https://www.nicovideo.jp/user/11111111/video"
            ]]
            instance = PopupVideoWindow(self.process_info)

            def pre_run(s_values, s_records):
                instance.record = None
                instance.title = None
                instance.size = None

                mock_values.reset_mock()
                if s_values == -1:
                    mock_values.__getitem__.side_effect = lambda key: []
                else:
                    mock_values.__getitem__.side_effect = lambda key: [s_values]
                instance.values = mock_values

                s_def_data = deepcopy(def_data)
                mock_window.reset_mock()
                mock_window.Values = s_def_data
                instance.window.reset_mock()
                instance.window.__getitem__.side_effect = lambda key: mock_window

                mock_mylist_info_db.reset_mock()
                if s_records:
                    mock_mylist_info_db.select_from_id_url.side_effect = lambda video_id, mylist_url: [s_records]
                else:
                    mock_mylist_info_db.select_from_id_url.side_effect = lambda video_id, mylist_url: []
                instance.mylist_info_db = mock_mylist_info_db

            def post_run(s_values, s_records):
                if s_values != -1:
                    self.assertEqual([
                        call.__getitem__("-TABLE-"),
                        call.__getitem__("-TABLE-"),
                    ], mock_values.mock_calls)
                else:
                    self.assertEqual([
                        call.__getitem__("-TABLE-")
                    ], mock_values.mock_calls)
                    instance.window.assert_not_called()
                    mock_mylist_info_db.assert_not_called()
                    self.assertIsNone(instance.record)
                    self.assertIsNone(instance.title)
                    self.assertIsNone(instance.size)
                    return

                s_def_data = deepcopy(def_data)
                self.assertEqual([
                    call.__getitem__("-TABLE-")
                ], instance.window.mock_calls)

                video_id = s_def_data[0][1]
                mylist_url = s_def_data[0][8]
                self.assertEqual([
                    call.select_from_id_url(video_id, mylist_url)
                ], mock_mylist_info_db.mock_calls)

                if s_records:
                    self.assertEqual(s_records, instance.record)
                    self.assertEqual("動画情報", instance.title)
                    self.assertEqual((580, 400), instance.size)
                else:
                    self.assertIsNone(instance.record)
                    self.assertIsNone(instance.title)
                    self.assertIsNone(instance.size)

            Params = namedtuple("Params", ["value", "record", "result"])
            params_list = [
                Params(0, ["record_1"], Result.success),
                Params(-1, ["record_1"], Result.failed),
                Params(0, [], Result.failed),
            ]
            for params in params_list:
                pre_run(params.value, params.record)
                actual = instance.init()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.value, params.record)

    def test_make_window_layout(self):
        instance = PopupVideoWindow(self.process_info)

        def pre_run(has_record_flag, valid_record_flag):
            instance.record = None
            instance.title = "動画情報"
            instance.size = (580, 400)

            if not has_record_flag:
                return

            if not valid_record_flag:
                instance.record = {"invalid_key": "invalid_value"}
                return

            instance.record = self._make_record()

        Params = namedtuple("Params", ["has_record_flag", "valid_record_flag", "result_func"])
        params_list = [
            Params(True, True, self._make_expect_window_layout),
            Params(False, True, None),
            Params(True, False, None),
        ]
        for params in params_list:
            pre_run(params.has_record_flag, params.valid_record_flag)
            actual = instance.make_window_layout()
            record = self._make_record()
            if callable(params.result_func):
                expect = params.result_func(record, instance.title)
                self._assert_layout(expect, actual)
            else:
                self.assertIs(None, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
