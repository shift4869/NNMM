import re
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.create_mylist import CreateMylist, CreateMylistThreadDone
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import MylistType, Result
from nnmm.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory


class TestCreateMylist(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
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
            "https://www.nicovideo.jp/user/11111111/series/00000011",
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
            mylist_url_info[5]: ("「マイリスト1」-投稿者1さんのシリーズ", "マイリスト1", "投稿者1"),
        }
        res = mylist_info.get(mylist_url, ("", "", ""))
        return res

    @unittest.skip("")
    def test_CreateMylist_init(self):
        instance = CreateMylist(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)

    @unittest.skip("")
    def test_CreateMylist_make_layout(self):
        instance = CreateMylist(self.process_info)

        def make_layout(s_mylist_type, s_mylist_url, s_window_title):
            horizontal_line = "-" * 132
            csize = (20, 1)
            tsize = (50, 1)
            cf = []
            if s_mylist_type == MylistType.uploaded:
                cf = [
                    [sg.Text(horizontal_line)],
                    [sg.Text("URL", size=csize), sg.Input(s_mylist_url, key="-URL-", readonly=True, size=tsize)],
                    [
                        sg.Text("URLタイプ", size=csize),
                        sg.Input(s_mylist_type.value, key="-URL_TYPE-", readonly=True, size=tsize),
                    ],
                    [
                        sg.Text("ユーザー名", size=csize),
                        sg.Input("", key="-USERNAME-", background_color="light goldenrod", size=tsize),
                    ],
                    [sg.Text(horizontal_line)],
                    [sg.Button("登録", key="-REGISTER-"), sg.Button("キャンセル", key="-CANCEL-")],
                ]
            elif s_mylist_type == MylistType.mylist:
                cf = [
                    [sg.Text(horizontal_line)],
                    [sg.Text("URL", size=csize), sg.Input(s_mylist_url, key="-URL-", readonly=True, size=tsize)],
                    [
                        sg.Text("URLタイプ", size=csize),
                        sg.Input(s_mylist_type.value, key="-URL_TYPE-", readonly=True, size=tsize),
                    ],
                    [
                        sg.Text("ユーザー名", size=csize),
                        sg.Input("", key="-USERNAME-", background_color="light goldenrod", size=tsize),
                    ],
                    [
                        sg.Text("マイリスト名", size=csize),
                        sg.Input("", key="-MYLISTNAME-", background_color="light goldenrod", size=tsize),
                    ],
                    [sg.Text(horizontal_line)],
                    [sg.Button("登録", key="-REGISTER-"), sg.Button("キャンセル", key="-CANCEL-")],
                ]
            elif s_mylist_type == MylistType.series:
                cf = [
                    [sg.Text(horizontal_line)],
                    [sg.Text("URL", size=csize), sg.Input(mylist_url, key="-URL-", readonly=True, size=tsize)],
                    [
                        sg.Text("URLタイプ", size=csize),
                        sg.Input(s_mylist_type.value, key="-URL_TYPE-", readonly=True, size=tsize),
                    ],
                    [
                        sg.Text("ユーザー名", size=csize),
                        sg.Input("", key="-USERNAME-", background_color="light goldenrod", size=tsize),
                    ],
                    [
                        sg.Text("シリーズ名", size=csize),
                        sg.Input("", key="-SERIESNAME-", background_color="light goldenrod", size=tsize),
                    ],
                    [sg.Text(horizontal_line)],
                    [sg.Button("登録", key="-REGISTER-"), sg.Button("キャンセル", key="-CANCEL-")],
                ]
            layout = [[sg.Frame(s_window_title, cf)]]
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
            (MylistType.uploaded, mylist_url, window_title),
            (MylistType.mylist, mylist_url, window_title),
            (MylistType.series, mylist_url, window_title),
            (None, mylist_url, window_title),
        ]
        for params in params_list:
            actual = instance.popup_for_detail(params[0], params[1], params[2])
            expect = make_layout(params[0], params[1], params[2])
            self.assertEqual(0, check_layout(expect, actual))

    @unittest.skip("")
    def test_CreateMylist_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("nnmm.process.create_mylist.logger.info"))
            mockle = stack.enter_context(patch("nnmm.process.create_mylist.logger.error"))
            mockpu = stack.enter_context(patch("nnmm.process.create_mylist.sg.popup"))
            mock_get_config = stack.enter_context(
                patch("nnmm.process.create_mylist.process_config.ConfigBase.get_config")
            )
            mock_get_now_datetime = stack.enter_context(patch("nnmm.process.create_mylist.get_now_datetime"))
            mock_popup_get_text = stack.enter_context(patch("nnmm.process.create_mylist.popup_get_text"))
            mock_window = stack.enter_context(patch("nnmm.process.create_mylist.QDialog"))
            mock_make_layout = stack.enter_context(patch("nnmm.process.create_mylist.CreateMylist.make_layout"))
            mock_select_from_url = MagicMock()
            instance = CreateMylist(self.process_info)

            mock_make_layout.return_value = "make_layout_response"
            mock_get_now_datetime.return_value = "mock_get_now_datetime_response"

            def pre_run(
                s_mylist_url,
                s_prev_mylist,
                get_config_value,
                s_username,
                s_mylistname,
                window_button_value,
            ):
                mock_popup_get_text.reset_mock()
                mock_popup_get_text.return_value = s_mylist_url

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
                    "-SERIESNAME-": s_mylistname,
                }
                mock_read.read = lambda: (window_button_value, values)
                mock_window.return_value = mock_read

            def post_run(
                s_mylist_url,
                s_prev_mylist,
                get_config_value,
                s_username,
                s_mylistname,
                window_button_value,
            ):
                sample_url_list = [
                    "https://www.nicovideo.jp/user/*******/video",
                    "https://www.nicovideo.jp/user/*******/mylist/********",
                    "https://www.nicovideo.jp/user/*******/series/********",
                ]
                sample_url_str = "\n".join(sample_url_list)
                message = "追加するマイリストのURLを入力\n" + sample_url_str
                mock_popup_get_text.assert_called_once_with(message, title="追加URL")

                if s_mylist_url == "":
                    mock_select_from_url.assert_not_called()
                    mock_get_config.assert_not_called()
                    mock_window.assert_not_called()
                    return

                if s_mylist_url == "invalid":
                    mock_select_from_url.assert_not_called()
                    mock_get_config.assert_not_called()
                    mock_window.assert_not_called()
                    return

                mylist_url = MylistURLFactory.create(s_mylist_url)
                non_query_url = mylist_url.non_query_url
                mylist_type = mylist_url.mylist_type
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

                self.assertEqual(
                    [
                        call(title="登録情報入力", layout="make_layout_response", auto_size_text=True, finalize=True),
                        call().__getitem__("-USERNAME-"),
                        call().__getitem__().set_focus(True),
                        call().close(),
                    ],
                    mock_window.mock_calls,
                )

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
                check_failed_count = 0
                is_include_new = False
                if mylist_type == MylistType.uploaded:
                    username = s_username
                    mylistname = "投稿動画"
                    showname = f"{username}さんの投稿動画"
                    is_include_new = False
                elif mylist_type == MylistType.mylist:
                    username = s_username
                    mylistname = s_mylistname
                    showname = f"「{mylistname}」-{username}さんのマイリスト"
                    is_include_new = False
                elif mylist_type == MylistType.series:
                    username = s_username
                    mylistname = s_mylistname
                    showname = f"「{mylistname}」-{username}さんのシリーズ"
                    is_include_new = False
                self.assertEqual(
                    [
                        call.select_from_url(s_mylist_url),
                        call.select(),
                        call.upsert(
                            id_index,
                            username,
                            mylistname,
                            mylist_type.value,
                            showname,
                            s_mylist_url,
                            dst,
                            dst,
                            dst,
                            check_interval,
                            check_failed_count,
                            is_include_new,
                        ),
                    ],
                    instance.mylist_db.mock_calls,
                )

            mylist_url_list = self._get_mylist_url_list()
            for mylist_url in mylist_url_list:
                prev_mylist = []
                mylist_info = self._get_mylist_info(mylist_url)
                username = mylist_info[2]
                mylistname = mylist_info[1]
                params_list = [
                    (
                        mylist_url,
                        prev_mylist,
                        "(使用しない)",
                        username,
                        mylistname,
                        "-REGISTER-",
                        Result.success,
                    ),
                    (mylist_url, prev_mylist, "10分毎", username, mylistname, "-REGISTER-", Result.success),
                    ("", prev_mylist, "(使用しない)", username, mylistname, "-REGISTER-", Result.failed),
                    (
                        "invalid",
                        prev_mylist,
                        "(使用しない)",
                        username,
                        mylistname,
                        "-REGISTER-",
                        Result.failed,
                    ),
                    (
                        mylist_url,
                        ["prev_mylist_exist"],
                        "(使用しない)",
                        username,
                        mylistname,
                        "-REGISTER-",
                        Result.failed,
                    ),
                    (mylist_url, prev_mylist, "invalid", username, mylistname, "-REGISTER-", Result.failed),
                    (mylist_url, prev_mylist, "(使用しない)", "", mylistname, "-REGISTER-", Result.failed),
                    (
                        mylist_url,
                        prev_mylist,
                        "(使用しない)",
                        username,
                        mylistname,
                        "invalid",
                        Result.failed,
                    ),
                ]
                for params in params_list:
                    pre_run(params[0], params[1], params[2], params[3], params[4], params[5])
                    actual = instance.run()
                    expect = params[-1]
                    self.assertIs(expect, actual)
                    post_run(params[0], params[1], params[2], params[3], params[4], params[5])
        pass

    @unittest.skip("")
    def test_CreateMylistThreadDone_init(self):
        instance = CreateMylistThreadDone(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)

    @unittest.skip("")
    def test_CreateMylistThreadDone_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("nnmm.process.create_mylist.logger.info"))
            mock_update_mylist_pane = stack.enter_context(
                patch("nnmm.process.create_mylist.ProcessBase.update_mylist_pane")
            )
            mock_update_table_pane = stack.enter_context(
                patch("nnmm.process.create_mylist.ProcessBase.update_table_pane")
            )
            mock_get_upper_textbox = stack.enter_context(
                patch("nnmm.process.create_mylist.ProcessBase.get_upper_textbox")
            )

            instance = CreateMylistThreadDone(self.process_info)

            actual = instance.run()
            self.assertIs(Result.success, actual)

            mock_update_mylist_pane.assert_called_once_with()
            mock_update_mylist_pane.reset_mock()

            mock_update_table_pane.assert_called_once_with(mock_get_upper_textbox().to_str())
            mock_update_table_pane.reset_mock()
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
