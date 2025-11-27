import re
import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QAbstractItemView, QApplication, QComboBox, QDialog, QGridLayout, QGroupBox, QHBoxLayout
from PySide6.QtWidgets import QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu, QPushButton, QTableWidget
from PySide6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.create_mylist import CreateMylist
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import MylistType, Result
from nnmm.video_info_fetcher.value_objects.mylist_url import MylistURL
from nnmm.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory


class TestCreateMylist(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.create_mylist.logger.info"))
        self.enterContext(patch("nnmm.process.create_mylist.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> CreateMylist:
        instance = CreateMylist(self.process_info)
        return instance

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

    def _get_mylist_url_type(self, mylist_url) -> MylistType:
        mylist_url = MylistURLFactory.create(mylist_url)
        return mylist_url.mylist_type

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)

    def test_popup_for_detail(self):
        mock_list = [
            self.enterContext(patch("nnmm.process.create_mylist.QDialog")),
            self.enterContext(patch("nnmm.process.create_mylist.QVBoxLayout")),
            self.enterContext(patch("nnmm.process.create_mylist.QHBoxLayout")),
            self.enterContext(patch("nnmm.process.create_mylist.QLabel")),
            self.enterContext(patch("nnmm.process.create_mylist.QPushButton")),
        ]
        mock_lineedit = self.enterContext(patch("nnmm.process.create_mylist.QLineEdit"))
        mock_lineedit.return_value.text.return_value = "<lineedit text>"
        mock_list.append(mock_lineedit)

        horizontal_line = "-" * 132
        csize = 80
        window_title = "登録情報入力"
        mylist_url_list = self._get_mylist_url_list()

        def pre_run(register_or_cancel: str) -> CreateMylist:
            instance = self._get_instance()
            for m in mock_list:
                m.reset_mock()
            self.register_or_cancel = register_or_cancel
            instance.register_or_cancel = register_or_cancel
            return instance

        def post_run_uploaded(actual: dict, instance: CreateMylist, mylist_url: MylistURL) -> None:
            result = actual["result"]
            username = actual["username"]
            mylistname = actual["mylistname"]
            showname = actual["showname"]
            is_include_new = actual["is_include_new"]

            self.assertEqual(self.register_or_cancel, result)
            self.assertTrue(hasattr(instance, "tbox_username"))
            self.assertFalse(hasattr(instance, "tbox_mylistname"))  # uploaded の場合はマイリスト名は自動でつける
            self.assertEqual("投稿動画", mylistname)
            self.assertEqual("<lineedit text>さんの投稿動画", showname)
            self.assertFalse(is_include_new)

            self.assertEqual(
                [call.setStyleSheet("QLineEdit {background-color: olive;}"), call.text()],
                instance.tbox_username.mock_calls,
            )

            expect = [
                [
                    call(),
                    call().setWindowTitle("登録情報入力"),
                    call().setLayout(mock_list[1].return_value),
                    call().exec(),
                ],
                [
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addWidget(mock_list[3].return_value),
                    call().addLayout(mock_list[2].return_value),
                ],
                [
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[4].return_value),
                    call().addWidget(mock_list[4].return_value),
                ],
                [
                    call(horizontal_line),
                    call("URL"),
                    call().setMinimumWidth(csize),
                    call("URLタイプ"),
                    call().setMinimumWidth(csize),
                    call("ユーザー名"),
                    call().setMinimumWidth(csize),
                    call(horizontal_line),
                ],
                [],
                [
                    call(mylist_url.non_query_url, readOnly=True),
                    call("uploaded", readOnly=True),
                    call(),
                    call().setStyleSheet("QLineEdit {background-color: olive;}"),
                    call().text(),
                ],
            ]
            for i, (e, m) in enumerate(zip(expect, mock_list, strict=True)):
                if i == 4:
                    continue
                self.assertEqual(e, m.mock_calls)

        def post_run_mylist(actual: dict, instance: CreateMylist, mylist_url: MylistURL) -> None:
            result = actual["result"]
            username = actual["username"]
            mylistname = actual["mylistname"]
            showname = actual["showname"]
            is_include_new = actual["is_include_new"]

            self.assertEqual(self.register_or_cancel, result)
            self.assertTrue(hasattr(instance, "tbox_username"))
            self.assertTrue(hasattr(instance, "tbox_mylistname"))
            self.assertEqual(f"「{mylistname}」-{username}さんのマイリスト", showname)
            self.assertFalse(is_include_new)

            self.assertEqual(
                [
                    call.setStyleSheet("QLineEdit {background-color: olive;}"),
                    call.setStyleSheet("QLineEdit {background-color: olive;}"),
                    call.text(),
                    call.text(),
                ],
                instance.tbox_username.mock_calls,
            )
            self.assertEqual(
                [
                    call.setStyleSheet("QLineEdit {background-color: olive;}"),
                    call.setStyleSheet("QLineEdit {background-color: olive;}"),
                    call.text(),
                    call.text(),
                ],
                instance.tbox_mylistname.mock_calls,
            )

            expect = [
                [
                    call(),
                    call().setWindowTitle("登録情報入力"),
                    call().setLayout(mock_list[1].return_value),
                    call().exec(),
                ],
                [
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addWidget(mock_list[3].return_value),
                    call().addLayout(mock_list[2].return_value),
                ],
                [
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[4].return_value),
                    call().addWidget(mock_list[4].return_value),
                    call().__bool__(),
                ],
                [
                    call(horizontal_line),
                    call("URL"),
                    call().setMinimumWidth(csize),
                    call("URLタイプ"),
                    call().setMinimumWidth(csize),
                    call("ユーザー名"),
                    call().setMinimumWidth(csize),
                    call("マイリスト名"),
                    call().setMinimumWidth(csize),
                    call(horizontal_line),
                ],
                [],
                [
                    call(mylist_url.non_query_url, readOnly=True),
                    call("mylist", readOnly=True),
                    call(),
                    call().setStyleSheet("QLineEdit {background-color: olive;}"),
                    call(),
                    call().setStyleSheet("QLineEdit {background-color: olive;}"),
                    call().text(),
                    call().text(),
                ],
            ]
            for i, (e, m) in enumerate(zip(expect, mock_list, strict=True)):
                if i == 4:
                    continue
                self.assertEqual(e, m.mock_calls)

        def post_run_series(actual: dict, instance: CreateMylist, mylist_url: MylistURL) -> None:
            result = actual["result"]
            username = actual["username"]
            mylistname = actual["mylistname"]
            showname = actual["showname"]
            is_include_new = actual["is_include_new"]

            self.assertEqual(self.register_or_cancel, result)
            self.assertTrue(hasattr(instance, "tbox_username"))
            self.assertTrue(hasattr(instance, "tbox_mylistname"))
            self.assertEqual(f"「{mylistname}」-{username}さんのシリーズ", showname)
            self.assertFalse(is_include_new)

            self.assertEqual(
                [
                    call.setStyleSheet("QLineEdit {background-color: olive;}"),
                    call.setStyleSheet("QLineEdit {background-color: olive;}"),
                    call.text(),
                    call.text(),
                ],
                instance.tbox_username.mock_calls,
            )
            self.assertEqual(
                [
                    call.setStyleSheet("QLineEdit {background-color: olive;}"),
                    call.setStyleSheet("QLineEdit {background-color: olive;}"),
                    call.text(),
                    call.text(),
                ],
                instance.tbox_mylistname.mock_calls,
            )

            expect = [
                [
                    call(),
                    call().setWindowTitle("登録情報入力"),
                    call().setLayout(mock_list[1].return_value),
                    call().exec(),
                ],
                [
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addLayout(mock_list[2].return_value),
                    call().addWidget(mock_list[3].return_value),
                    call().addLayout(mock_list[2].return_value),
                ],
                [
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[3].return_value),
                    call().addWidget(mock_list[5].return_value),
                    call(),
                    call().addWidget(mock_list[4].return_value),
                    call().addWidget(mock_list[4].return_value),
                    call().__bool__(),
                ],
                [
                    call(horizontal_line),
                    call("URL"),
                    call().setMinimumWidth(csize),
                    call("URLタイプ"),
                    call().setMinimumWidth(csize),
                    call("ユーザー名"),
                    call().setMinimumWidth(csize),
                    call("シリーズ名"),
                    call().setMinimumWidth(csize),
                    call(horizontal_line),
                ],
                [],
                [
                    call(mylist_url.non_query_url, readOnly=True),
                    call("series", readOnly=True),
                    call(),
                    call().setStyleSheet("QLineEdit {background-color: olive;}"),
                    call(),
                    call().setStyleSheet("QLineEdit {background-color: olive;}"),
                    call().text(),
                    call().text(),
                ],
            ]
            for i, (e, m) in enumerate(zip(expect, mock_list, strict=True)):
                if i == 4:
                    continue
                self.assertEqual(e, m.mock_calls)

        def post_run(actual: dict, instance: CreateMylist, mylist_url: MylistURL) -> None:
            mylist_url = MylistURLFactory.create(mylist_url)
            mylist_type = self._get_mylist_url_type(mylist_url)

            if mylist_type == MylistType.uploaded:
                post_run_uploaded(actual, instance, mylist_url)
            elif mylist_type == MylistType.mylist:
                post_run_mylist(actual, instance, mylist_url)
            elif mylist_type == MylistType.series:
                post_run_series(actual, instance, mylist_url)

        for mylist_url in mylist_url_list:
            mylist_type = self._get_mylist_url_type(mylist_url)
            instance = pre_run("register")
            actual = instance.popup_for_detail(mylist_type, mylist_url, window_title)
            post_run(actual, instance, mylist_url)

            instance = pre_run("cancel")
            actual = instance.popup_for_detail(mylist_type, mylist_url, window_title)
            post_run(actual, instance, mylist_url)

        with self.assertRaises(ValueError):
            mock_mylist = MagicMock()
            mock_mylist.value = "invalid mylist_type"
            mock_mylist.return_value = "invalid mylist_type"
            actual = instance.popup_for_detail(mock_mylist, mylist_url_list[0], window_title)

        with self.assertRaises(ValueError):
            mock_mylist = MagicMock()
            mock_mylist.value = "invalid mylist_type"
            self.first = True

            def f(o):
                result = self.first
                self.first = False
                return result

            mock_mylist.__eq__.side_effect = f
            actual = instance.popup_for_detail(mock_mylist, mylist_url_list[0], window_title)

    def test_create_component(self):
        mock_btn = self.enterContext(patch("nnmm.process.create_mylist.QPushButton"))
        instance = self._get_instance()
        actual = instance.create_component()
        self.assertEqual(mock_btn.return_value, actual)
        mock_btn.return_value.clicked.connect.assert_called_once()

    def test_callback(self):
        mock_popup_get_text = self.enterContext(patch("nnmm.process.create_mylist.popup_get_text"))
        mock_popup = self.enterContext(patch("nnmm.process.create_mylist.popup"))
        mock_get_config = self.enterContext(patch("nnmm.process.create_mylist.process_config.ConfigBase.get_config"))
        mock_get_now_datetime = self.enterContext(patch("nnmm.process.create_mylist.get_now_datetime"))

        Params = namedtuple(
            "Params",
            ["kind_mylist_url", "is_empty_select_from_url", "kind_auto_reload", "kind_popup_for_detail", "result"],
        )

        def pre_run(params: Params) -> CreateMylist:
            instance = self._get_instance()
            instance.set_upper_textbox = MagicMock()
            instance.get_upper_textbox = MagicMock()
            instance.set_bottom_textbox = MagicMock()
            instance.update_mylist_pane = MagicMock()
            instance.update_table_pane = MagicMock()

            mylist_url = self._get_mylist_url_list()[0]
            mock_popup_get_text.reset_mock()
            if params.kind_mylist_url == "valid_mylist_url":
                mock_popup_get_text.return_value = mylist_url
            elif params.kind_mylist_url == "invalid_mylist_url":
                mock_popup_get_text.return_value = "invalid_mylist_url"
            else:  # "empty_mylist_url"
                mock_popup_get_text.return_value = ""

            mock_popup.reset_mock()

            instance.mylist_db.reset_mock()
            if params.is_empty_select_from_url:
                instance.mylist_db.select_from_url.return_value = []
            else:
                instance.mylist_db.select_from_url.return_value = ["prev_mylist detected"]

            mock_get_config.reset_mock()
            if params.kind_auto_reload == "valid_auto_reload":
                rt = mock_get_config.return_value
                rt.__getitem__.return_value.get.return_value = "20分毎"
            elif params.kind_auto_reload == "valid_default":
                rt = mock_get_config.return_value
                rt.__getitem__.return_value.get.return_value = "(使用しない)"
            else:  # "invalid"
                rt = mock_get_config.return_value
                rt.__getitem__.return_value.get.return_value = "invalid"

            instance.popup_for_detail = MagicMock()
            if params.kind_popup_for_detail == "register":
                showname, mylistname, username = self._get_mylist_info(mylist_url)
                is_include_new = False
                detail_dict = {
                    "result": "register",
                    "username": username,
                    "mylistname": mylistname,
                    "showname": showname,
                    "is_include_new": is_include_new,
                }
                instance.popup_for_detail.return_value = detail_dict
            elif params.kind_popup_for_detail == "invalid_register":
                is_include_new = False
                detail_dict = {
                    "result": "register",
                    "username": "",
                    "mylistname": "",
                    "showname": "",
                    "is_include_new": is_include_new,
                }
                instance.popup_for_detail.return_value = detail_dict

            mock_get_now_datetime.reset_mock()
            mock_get_now_datetime.return_value = "now_datetime"

            instance.mylist_db.select.return_value = [{"id": 1}]
            return instance

        def post_run(actual: Result, instance: CreateMylist, params: Params) -> None:
            self.assertEqual(params.result, actual)
            mylist_url = self._get_mylist_url_list()[0]
            if params.kind_mylist_url == "valid_mylist_url":
                sample_url_list = [
                    "https://www.nicovideo.jp/user/*******/video",
                    "https://www.nicovideo.jp/user/*******/mylist/********",
                    "https://www.nicovideo.jp/user/*******/series/********",
                ]
                sample_url_str = "\n".join(sample_url_list)
                message = "追加するマイリストのURLを入力\n" + sample_url_str
                mock_popup_get_text.assert_called_once_with(message, title="追加マイリストURL")

                mylist_url = MylistURLFactory.create(mylist_url)
                non_query_url = mylist_url.non_query_url
                mylist_type = mylist_url.mylist_type
            elif params.kind_mylist_url == "invalid_mylist_url":
                mock_popup.assert_called_once_with("入力されたURLには対応していません\n新規追加処理を終了します")
                instance.mylist_db.select_from_url.assert_not_called()
                instance.set_bottom_textbox.assert_not_called()
                instance.popup_for_detail.assert_not_called()
                mock_get_now_datetime.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.get_upper_textbox.return_value.to_str.assert_not_called()
                instance.update_table_pane.assert_not_called()
                return
            else:  # "empty_mylist_url"
                mock_popup.assert_not_called()
                instance.mylist_db.select_from_url.assert_not_called()
                instance.set_bottom_textbox.assert_not_called()
                instance.popup_for_detail.assert_not_called()
                mock_get_now_datetime.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.get_upper_textbox.return_value.to_str.assert_not_called()
                instance.update_table_pane.assert_not_called()
                return

            if params.is_empty_select_from_url:
                pass
            else:
                mock_popup.assert_called_once_with("既存マイリスト一覧に含まれています\n新規追加処理を終了します")
                instance.set_bottom_textbox.assert_not_called()
                instance.popup_for_detail.assert_not_called()
                mock_get_now_datetime.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.get_upper_textbox.return_value.to_str.assert_not_called()
                instance.update_table_pane.assert_not_called()
                return

            instance.set_bottom_textbox.assert_any_call("ロード中")

            check_interval = ""
            if params.kind_auto_reload == "valid_auto_reload":
                self.assertEqual(
                    [call(), call().__getitem__("general"), call().__getitem__().get("auto_reload", "")],
                    mock_get_config.mock_calls,
                )
                rt = mock_get_config.return_value
                i_str = rt.__getitem__.return_value.get.return_value
                pattern = r"^([0-9]+)分毎$"
                check_interval = re.findall(pattern, i_str)[0] + "分"
            elif params.kind_auto_reload == "valid_default":
                check_interval = "15分"
            else:  # "invalid"
                instance.popup_for_detail.assert_not_called()
                mock_get_now_datetime.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.get_upper_textbox.return_value.to_str.assert_not_called()
                instance.update_table_pane.assert_not_called()
                return

            check_failed_count = 0

            if params.kind_popup_for_detail == "register":
                showname, mylistname, username = self._get_mylist_info(non_query_url)
                is_include_new = False
            elif params.kind_popup_for_detail == "invalid_register":
                mock_popup.assert_called_once_with("入力されたマイリスト情報が不正です\n新規追加処理を終了します")
                mock_get_now_datetime.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.get_upper_textbox.return_value.to_str.assert_not_called()
                instance.update_table_pane.assert_not_called()
                return
            else:
                mock_get_now_datetime.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.get_upper_textbox.return_value.to_str.assert_not_called()
                instance.update_table_pane.assert_not_called()
                return

            mock_get_now_datetime.assert_called_once_with()
            mock_popup.assert_not_called()

            dst = "now_datetime"
            self.assertEqual(
                [
                    call.select_from_url(non_query_url),
                    call.select(),
                    call.upsert(
                        2,
                        username,
                        mylistname,
                        mylist_type.value,
                        showname,
                        non_query_url,
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

            instance.set_upper_textbox.assert_called_once_with(non_query_url)
            instance.set_bottom_textbox.assert_any_call("マイリスト追加完了")
            instance.update_mylist_pane.assert_called_once_with()
            instance.get_upper_textbox.return_value.to_str.assert_called_once_with()
            rt = instance.get_upper_textbox.return_value.to_str.return_value
            instance.update_table_pane.assert_called_once_with(rt)

        params_list = [
            Params("valid_mylist_url", True, "valid_auto_reload", "register", Result.success),
            Params("valid_mylist_url", True, "valid_default", "register", Result.success),
            Params("valid_mylist_url", True, "valid_auto_reload", "invalid_register", Result.failed),
            Params("valid_mylist_url", True, "valid_auto_reload", "cancel", Result.failed),
            Params("valid_mylist_url", True, "invalid", "register", Result.failed),
            Params("valid_mylist_url", False, "valid_auto_reload", "register", Result.failed),
            Params("invalid_mylist_url", True, "valid_auto_reload", "register", Result.failed),
            Params("empty_mylist_url", True, "valid_auto_reload", "register", Result.failed),
        ]

        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)

        return
        mockli = self.enterContext(patch("nnmm.process.create_mylist.logger.info"))
        mockle = self.enterContext(patch("nnmm.process.create_mylist.logger.error"))
        mockpu = self.enterContext(patch("nnmm.process.create_mylist.sg.popup"))
        mock_get_config = self.enterContext(patch("nnmm.process.create_mylist.process_config.ConfigBase.get_config"))
        mock_get_now_datetime = self.enterContext(patch("nnmm.process.create_mylist.get_now_datetime"))
        mock_popup_get_text = self.enterContext(patch("nnmm.process.create_mylist.popup_get_text"))
        mock_window = self.enterContext(patch("nnmm.process.create_mylist.QDialog"))
        mock_make_layout = self.enterContext(patch("nnmm.process.create_mylist.CreateMylist.make_layout"))
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


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
    unittest.main(warnings="ignore")
    unittest.main(warnings="ignore")
    unittest.main(warnings="ignore")
