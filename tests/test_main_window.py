import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from typing import Callable

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.main_window import MainWindow
from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process import config, copy_mylist_url, copy_video_url, create_mylist, delete_mylist, move_down, move_up
from nnmm.process import not_watched, popup, search, show_mylist_info, show_mylist_info_all, timer, video_play
from nnmm.process import video_play_with_focus_back, watched, watched_all_mylist, watched_mylist
from nnmm.process.base import ProcessBase
from nnmm.process.update_mylist import every, partial, single
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

TEST_DB_PATH = ":memory:"
CSV_PATH = "./tests/cache/result.csv"


# テスト用具体化ProcessBase
class ConcreteProcessBase(ProcessBase):
    def __init__(self, info: ProcessInfo) -> None:
        super().__init__(info)

    def run(self) -> Result:
        return Result.success


# テスト用具体化ProcessBase(エラー想定)
class ConcreteErrorProcessBase(ProcessBase):
    def __init__(self, info: ProcessInfo) -> None:
        super().__init__(info)

    def run(self) -> Result:
        raise Exception


class TestWindowMain(unittest.TestCase):
    def _get_instance(
        self, use_create_layout: bool = False, update_mylist_pane: bool = False, init_config: bool = False
    ):
        self.mock_list = [
            self.enterContext(patch("nnmm.main_window.logger.info")),
            self.enterContext(patch("nnmm.main_window.QDialog.__init__")),
            self.enterContext(patch("nnmm.main_window.MylistDBController", spec=MylistDBController)),
            self.enterContext(patch("nnmm.main_window.MylistInfoDBController", spec=MylistInfoDBController)),
            self.enterContext(patch("nnmm.main_window.QIcon")),
            self.enterContext(patch("nnmm.main_window.MainWindow.setWindowIcon")),
            self.enterContext(patch("nnmm.main_window.MainWindow.setWindowTitle")),
            self.enterContext(patch("nnmm.main_window.MainWindow.setLayout")),
            self.enterContext(patch("nnmm.main_window.MainWindow.setGeometry")),
            self.enterContext(patch("nnmm.main_window.asyncio.set_event_loop_policy")),
            self.enterContext(patch("nnmm.main_window.asyncio.WindowsSelectorEventLoopPolicy")),
            self.enterContext(patch("nnmm.main_window.timer.Timer")),
            self.enterContext(patch("nnmm.main_window.MainWindow.activateWindow")),
        ]
        mock_config = self.enterContext(patch("nnmm.main_window.config.ConfigBase.set_config"))
        mock_config.side_effect = lambda: {"db": {"save_path": "./tests/cache"}}
        self.mock_list.append(mock_config)

        if not use_create_layout:
            self.mock_list.append(self.enterContext(patch("nnmm.main_window.MainWindow.create_layout")))
        if not update_mylist_pane:
            self.mock_list.append(self.enterContext(patch("nnmm.main_window.MainWindow.update_mylist_pane")))
        if not init_config:
            self.mock_list.append(self.enterContext(patch("nnmm.main_window.MainWindow.init_config")))
        mw = MainWindow()
        return mw

    def _get_mylist_dict(self, index: int = 1) -> dict:
        return {
            "id": index,
            "username": f"username_{index}",
            "mylistname": f"mylistname_{index}",
            "type": f"uploaded",
            "showname": f"showname_{index}",
            "url": f"url_{index}",
            "created_at": "2023-12-21 12:34:56",
            "updated_at": "2023-12-21 12:34:56",
            "checked_at": "2023-12-21 12:34:56",
            "check_interval": "15分",
            "is_include_new": index % 2 == 0,
        }

    def test_init(self):
        """WindowMainの初期化後の状態をテストする"""
        instance = self._get_instance()

        self.assertIsInstance(instance, MainWindow)
        self.assertTrue(hasattr(instance, "config"))
        self.assertTrue(hasattr(instance, "db_fullpath"))
        self.assertTrue(hasattr(instance, "mylist_db"))
        self.assertTrue(hasattr(instance, "mylist_info_db"))
        self.assertTrue(hasattr(instance, "time"))

        for mock_item in self.mock_list:
            mock_item.assert_called()

    def test_create_layout(self):
        """MainWindowのレイアウト作成呼び出しをテストする"""
        mock_list = [
            self.enterContext(patch("nnmm.main_window.QVBoxLayout")),
            self.enterContext(patch("nnmm.main_window.QTabWidget")),
            self.enterContext(patch("nnmm.main_window.MainWindow.create_mylist_tab_layout")),
            self.enterContext(patch("nnmm.main_window.MainWindow.create_config_tab_layout")),
            self.enterContext(patch("nnmm.main_window.QTextEdit")),
        ]
        instance = self._get_instance(use_create_layout=True)

        self.assertTrue(hasattr(instance, "textarea"))

        expect_calls_list = [
            [call(), call().addWidget(mock_list[1].return_value)],
            [
                call(),
                call().addTab(mock_list[2].return_value, "マイリスト"),
                call().addTab(mock_list[3].return_value, "設定"),
                call().addTab(mock_list[4].return_value, "ログ"),
            ],
            [call(1200, 850)],
            [call(1200, 850)],
            [call(), call().setMinimumHeight(300)],
        ]

        for expect_calls, mock_item in zip(expect_calls_list, mock_list):
            self.assertEqual(expect_calls, mock_item.mock_calls)
            mock_item.assert_called()

    def test_callback_helper(self):
        """callback用のヘルパ関数をテストする"""
        instance = self._get_instance()
        mock = MagicMock()
        actual = instance.callback_helper("テスト", mock)
        expect = mock(ProcessInfo.create("テスト", instance)).callback()

        self.assertIsInstance(actual, Callable)
        self.assertIsInstance(actual(), Callable)
        self.assertEqual(expect, actual())

    @unittest.skip("")
    def test_update_mylist_pane(self):
        mw = self._get_instance()
        mw.window = MagicMock()
        mw.mylist_db = MagicMock()

        def pre_run(is_include_new):
            mw.window.reset_mock()
            mw.mylist_db.reset_mock()
            if is_include_new:
                m_list = [self._get_mylist_dict(2)]
                mw.mylist_db.select.side_effect = lambda: m_list
            else:
                m_list = [self._get_mylist_dict(1)]
                mw.mylist_db.select.side_effect = lambda: m_list

        def post_run(is_include_new):
            self.assertEqual([call.select()], mw.mylist_db.mock_calls)

            NEW_MARK = "*:"
            m_list = []
            if is_include_new:
                m_list = [self._get_mylist_dict(2)]
            else:
                m_list = [self._get_mylist_dict(1)]

            index = 0
            include_new_index_list = []
            for i, m in enumerate(m_list):
                if m["is_include_new"]:
                    m["showname"] = NEW_MARK + m["showname"]
                    include_new_index_list.append(i)
            list_data = [m["showname"] for m in m_list]

            expect_window_calls = [call.__getitem__("-LIST-"), call.__getitem__().update(values=list_data)]
            for i in include_new_index_list:
                expect_window_calls.extend([
                    call.__getitem__("-LIST-"),
                    call.__getitem__().Widget.itemconfig(i, fg="black", bg="light pink"),
                ])
            expect_window_calls.extend([
                call.__getitem__("-LIST-"),
                call.__getitem__().Widget.see(index),
                call.__getitem__("-LIST-"),
                call.__getitem__().update(set_to_index=index),
            ])
            self.assertEqual(expect_window_calls, mw.window.mock_calls)

        params_list = [True, False]
        for params in params_list:
            pre_run(params)
            actual = mw.update_mylist_pane()
            expect = Result.success
            self.assertEqual(expect, actual)
            post_run(params)

    @unittest.skip("")
    def test_run(self):
        """WindowMainのメインベントループをテストする"""
        mock_config_load = self.enterContext(patch("nnmm.main_window.config.ConfigLoad"))
        mock_logger = self.enterContext(patch("nnmm.main_window.logger.error"))

        mw = self._get_instance()
        mw.window.read.side_effect = [
            ("-DO_TEST-", {"do": "do something"}),
            ("-TAB_CHANGED-", {"-TAB_CHANGED-": "設定"}),
            ("-TAB_CHANGED-", {"-TAB_CHANGED-": "ログ"}),
            ("-NONE_TEST-", {"none": "none"}),
            ("-ERROR_TEST-", {"error": "error"}),
            ("-EXIT-", "exit"),
        ]

        mw.dict["-DO_TEST-"] = ConcreteProcessBase
        mw.dict["-NONE_TEST-"] = lambda info: None
        mw.dict["-ERROR_TEST-"] = ConcreteErrorProcessBase
        actual = mw.run()
        self.assertIs(Result.success, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
