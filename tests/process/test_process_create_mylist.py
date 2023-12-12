import re
import sys
import unittest
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_create_mylist import ProcessCreateMylist, ProcessCreateMylistThreadDone
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, get_mylist_type


class TestProcessCreateMylist(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_mylist_url_list(self) -> list[str]:
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def _get_mylist_info(self, mylist_url: str) -> tuple[str, str, str]:
        mylist_url_info = self._get_mylist_url_list()
        mylist_info = {
            mylist_url_info[0]: ("投稿者1さんの投稿動画-ニコニコ動画", "投稿動画", "投稿者1"),
            mylist_url_info[1]: ("投稿者2さんの投稿動画-ニコニコ動画", "投稿動画", "投稿者2"),
            mylist_url_info[2]: ("「マイリスト1」-投稿者1さんのマイリスト", "マイリスト1", "投稿者1"),
            mylist_url_info[3]: ("「マイリスト2」-投稿者1さんのマイリスト", "マイリスト2", "投稿者1"),
            mylist_url_info[4]: ("「マイリスト3」-投稿者3さんのマイリスト", "マイリスト3", "投稿者3"),
        }
        res = mylist_info.get(mylist_url, ("", "", ""))
        return res

    def test_ProcessCreateMylist_init(self):
        instance = ProcessCreateMylist(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)

    def test_ProcessCreateMylist_make_layout(self):
        instance = ProcessCreateMylist(self.process_info)
        def make_layout(s_url_type, s_mylist_url, s_window_title):
            horizontal_line = "-" * 132
            csize = (20, 1)
            tsize = (50, 1)
            cf = []
            if s_url_type == "uploaded":
                cf = [
                    [sg.Text(horizontal_line)],
                    [sg.Text("URL", size=csize), sg.Input(s_mylist_url, key="-URL-", readonly=True, size=tsize)],
                    [sg.Text("URLタイプ", size=csize), sg.Input(s_url_type, key="-URL_TYPE-", readonly=True, size=tsize)],
                    [sg.Text("ユーザー名", size=csize), sg.Input("", key="-USERNAME-", background_color="light goldenrod", size=tsize)],
                    [sg.Text(horizontal_line)],
                    [sg.Button("登録", key="-REGISTER-"), sg.Button("キャンセル", key="-CANCEL-")],
                ]
            elif s_url_type == "mylist":
                cf = [
                    [sg.Text(horizontal_line)],
                    [sg.Text("URL", size=csize), sg.Input(s_mylist_url, key="-URL-", readonly=True, size=tsize)],
                    [sg.Text("URLタイプ", size=csize), sg.Input(s_url_type, key="-URL_TYPE-", readonly=True, size=tsize)],
                    [sg.Text("ユーザー名", size=csize), sg.Input("", key="-USERNAME-", background_color="light goldenrod", size=tsize)],
                    [sg.Text("マイリスト名", size=csize), sg.Input("", key="-MYLISTNAME-", background_color="light goldenrod", size=tsize)],
                    [sg.Text(horizontal_line)],
                    [sg.Button("登録", key="-REGISTER-"), sg.Button("キャンセル", key="-CANCEL-")],
                ]
            layout = [[
                sg.Frame(s_window_title, cf)
            ]]
            return layout

        def check_layout(e, a):
            """sgオブジェクトは別IDで生成されるため、各要素を比較する
                self.assertEqual(expect, actual)
            """
            # typeチェック
            self.assertEqual(type(e), type(a))
            # イテラブルなら再起
            if hasattr(e, "__iter__") and hasattr(a, "__iter__"):
                self.assertEqual(len(e), len(a))
                for e1, a1 in zip(e, a):
                    check_layout(e1, a1)
            # Rows属性を持つなら再起
            if hasattr(e, "Rows") and hasattr(a, "Rows"):
                for e2, a2 in zip(e.Rows, a.Rows):
                    check_layout(e2, a2)
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
            return 0
        window_title = "登録情報入力"
        mylist_url = self._get_mylist_url_list()[0]
        params_list = [
            ("uploaded", mylist_url, window_title),
            ("mylist", mylist_url, window_title),
        ]
        for params in params_list:
            actual = instance.make_layout(params[0], params[1], params[2])
            expect = make_layout(params[0], params[1], params[2])
            self.assertEqual(0, check_layout(expect, actual))

    def test_ProcessCreateMylist_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.process_create_mylist.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.process_create_mylist.logger.error"))
            mockpu = stack.enter_context(patch("NNMM.process.process_create_mylist.sg.popup"))
            mock_get_config = stack.enter_context(patch("NNMM.process.process_create_mylist.process_config.ProcessConfigBase.get_config"))
            mock_get_mylist_type = stack.enter_context(patch("NNMM.process.process_create_mylist.get_mylist_type"))
            mock_get_now_datetime = stack.enter_context(patch("NNMM.process.process_create_mylist.get_now_datetime"))
            mock_popup_get_text = stack.enter_context(patch("NNMM.process.process_create_mylist.popup_get_text"))
            mock_window = stack.enter_context(patch("NNMM.process.process_create_mylist.sg.Window"))
            mock_make_layout = stack.enter_context(patch("NNMM.process.process_create_mylist.ProcessCreateMylist.make_layout"))
            mock_select_from_url = MagicMock()
            instance = ProcessCreateMylist(self.process_info)

            mock_make_layout.return_value = "make_layout_response"
            mock_get_now_datetime.return_value = "mock_get_now_datetime_response"
            def pre_run(s_mylist_url,s_url_type, s_prev_mylist,
                        get_config_value, s_username, s_mylistname, window_button_value):
                mock_popup_get_text.reset_mock()
                mock_popup_get_text.return_value = s_mylist_url

                mock_get_mylist_type.reset_mock()
                if s_url_type in ["uploaded", "mylist"]:
                    mock_get_mylist_type.side_effect = get_mylist_type
                else:
                    mock_get_mylist_type.side_effect = lambda mylist_url: ""

                mock_select_from_url.reset_mock()
                mock_select_from_url.side_effect = lambda mylist_url: s_prev_mylist
                instance.mylist_db.reset_mock()
                instance.mylist_db.select_from_url = mock_select_from_url
                instance.mylist_db.select.side_effect = lambda: [{"id": "0"}]

                mock_get_config.reset_mock()
                mock_get_config.return_value = {"general": {"auto_reload": get_config_value}}

                mock_window.reset_mock()
                mock_read = MagicMock()
                values = {
                    "-USERNAME-": s_username,
                    "-MYLISTNAME-": s_mylistname,
                }
                mock_read.read = lambda :(window_button_value, values)
                mock_window.return_value = mock_read

            def post_run(s_mylist_url, s_url_type, s_prev_mylist,
                         get_config_value, s_username, s_mylistname, window_button_value):
                sample_url1 = "https://www.nicovideo.jp/user/*******/video"
                sample_url2 = "https://www.nicovideo.jp/user/*******/mylist/********"
                message = f"追加する マイリスト/ 投稿動画一覧 のURLを入力\n{sample_url1}\n{sample_url2}"
                mock_popup_get_text.assert_called_once_with(message, title="追加URL")

                if s_mylist_url == "":
                    mock_get_mylist_type.assert_not_called()
                    mock_select_from_url.assert_not_called()
                    mock_get_config.assert_not_called()
                    mock_window.assert_not_called()
                    return

                mock_get_mylist_type.assert_called_once_with(s_mylist_url)
                if s_url_type == "":
                    mock_select_from_url.assert_not_called()
                    mock_get_config.assert_not_called()
                    mock_window.assert_not_called()
                    return

                mock_select_from_url.assert_called_once_with(s_mylist_url)
                if s_prev_mylist:
                    mock_get_config.assert_not_called()
                    mock_window.assert_not_called()
                    return

                mock_get_config.assert_called_once_with()
                if get_config_value == "invalid":
                    mock_window.assert_not_called()
                    return

                if window_button_value == "invalid":
                    return

                if s_username == "" or s_mylistname == "":
                    return

                self.assertEqual([
                    call(title="登録情報入力", layout="make_layout_response", auto_size_text=True, finalize=True),
                    call().__getitem__("-USERNAME-"),
                    call().__getitem__().set_focus(True),
                    call().close()
                ], mock_window.mock_calls)

                check_interval = ""
                i_str = get_config_value
                if i_str == "(使用しない)" or i_str == "":
                    check_interval = "15分"  # デフォルトは15分
                else:
                    pattern = r"^([0-9]+)分毎$"
                    check_interval = re.findall(pattern, i_str)[0] + "分"
                dst = "mock_get_now_datetime_response"
                id_index = 1
                username = ""
                mylistname = ""
                showname = ""
                is_include_new = False
                if url_type == "uploaded":
                    username = s_username
                    mylistname = "投稿動画"
                    showname = f"{username}さんの投稿動画"
                    is_include_new = False
                elif url_type == "mylist":
                    username = s_username
                    mylistname = s_mylistname
                    showname = f"「{mylistname}」-{username}さんのマイリスト"
                    is_include_new = False
                self.assertEqual([
                    call.select_from_url(s_mylist_url),
                    call.select(),
                    call.upsert(id_index, username, mylistname, url_type, showname, mylist_url,
                                dst, dst, dst, check_interval, is_include_new)
                ], instance.mylist_db.mock_calls)

            mylist_url_list = self._get_mylist_url_list()
            for mylist_url in mylist_url_list:
                url_type = get_mylist_type(mylist_url)
                prev_mylist = []
                mylist_info = self._get_mylist_info(mylist_url)
                username = mylist_info[2]
                mylistname = mylist_info[1]
                params_list = [
                    (mylist_url, url_type, prev_mylist, "(使用しない)", username, mylistname, "-REGISTER-", Result.success),
                    (mylist_url, url_type, prev_mylist, "10分毎", username, mylistname, "-REGISTER-", Result.success),
                    ("", url_type, prev_mylist, "(使用しない)", username, mylistname, "-REGISTER-", Result.failed),
                    (mylist_url, "", prev_mylist, "(使用しない)", username, mylistname, "-REGISTER-", Result.failed),
                    (mylist_url, url_type, ["prev_mylist_exist"], "(使用しない)", username, mylistname, "-REGISTER-", Result.failed),
                    (mylist_url, url_type, prev_mylist, "invalid", username, mylistname, "-REGISTER-", Result.failed),
                    (mylist_url, url_type, prev_mylist, "(使用しない)", "", mylistname, "-REGISTER-", Result.failed),
                    # (mylist_url, url_type, prev_mylist, "(使用しない)", username, "", "-REGISTER-", Result.failed),
                    (mylist_url, url_type, prev_mylist, "(使用しない)", username, mylistname, "invalid", Result.failed),
                ]
                for params in params_list:
                    pre_run(params[0], params[1], params[2], params[3], params[4], params[5], params[6])
                    actual = instance.run()
                    expect = params[-1]
                    self.assertIs(expect, actual)
                    post_run(params[0], params[1], params[2], params[3], params[4], params[5], params[6])
        pass

    def test_ProcessCreateMylistThreadDone_init(self):
        instance = ProcessCreateMylistThreadDone(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)

    def test_ProcessCreateMylistThreadDone_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.process_create_mylist.logger.info"))
            mock_update_mylist_pane = stack.enter_context(patch("NNMM.process.process_create_mylist.update_mylist_pane"))
            mock_update_table_pane = stack.enter_context(patch("NNMM.process.process_create_mylist.update_table_pane"))

            instance = ProcessCreateMylistThreadDone(self.process_info)

            actual = instance.run()
            self.assertIsNone(actual)

            mock_update_mylist_pane.assert_called_once_with(instance.window, instance.mylist_db)
            mock_update_mylist_pane.reset_mock()

            mock_update_table_pane.assert_called_once_with(
                instance.window, instance.mylist_db, instance.mylist_info_db, instance.values["-INPUT1-"]
            )
            mock_update_table_pane.reset_mock()
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
