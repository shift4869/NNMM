import sys
import unittest
from typing import Callable

from mock import MagicMock, call, patch
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QListWidgetItem

import nnmm.main_window
from nnmm.main_window import MainWindow
from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process import config, copy_mylist_url, copy_video_url, create_mylist, delete_mylist, move_down, move_up
from nnmm.process import not_watched, popup, search, show_mylist_info_all, video_play, video_play_with_focus_back
from nnmm.process import watched, watched_all_mylist, watched_mylist
from nnmm.process.base import ProcessBase
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
        self, use_create_layout: bool = False, use_update_mylist_pane: bool = False, use_init_config: bool = False
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
        if not use_update_mylist_pane:
            self.mock_list.append(self.enterContext(patch("nnmm.main_window.MainWindow.update_mylist_pane")))
        if not use_init_config:
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
        # 正常系
        instance = self._get_instance()

        self.assertIsInstance(instance, MainWindow)
        self.assertTrue(hasattr(instance, "config"))
        self.assertTrue(hasattr(instance, "db_fullpath"))
        self.assertTrue(hasattr(instance, "mylist_db"))
        self.assertTrue(hasattr(instance, "mylist_info_db"))
        self.assertTrue(hasattr(instance, "time"))

        for mock_item in self.mock_list:
            mock_item.assert_called()

        # 異常系: アイコンパスが不正な場合はデフォルトを使用する
        prev_path = nnmm.main_window.ICON_PATH
        nnmm.main_window.ICON_PATH = "not exist path"
        instance = MainWindow()  # 2重のenterCntextを防ぐために _get_instance は呼ばずに普通に作る

        self.assertIsInstance(instance, MainWindow)
        self.assertTrue(hasattr(instance, "config"))
        self.assertTrue(hasattr(instance, "db_fullpath"))
        self.assertTrue(hasattr(instance, "mylist_db"))
        self.assertTrue(hasattr(instance, "mylist_info_db"))
        self.assertTrue(hasattr(instance, "time"))

        nnmm.main_window.ICON_PATH = prev_path

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

    def test_component_helper(self):
        """コンポーネント用のヘルパ関数をテストする"""
        instance = self._get_instance()
        mock = MagicMock()
        actual = instance.component_helper("テスト", mock)
        expect = mock(ProcessInfo.create("テスト", instance)).create_component()

        self.assertEqual(expect, actual)

    def test_process_helper(self):
        """プロセス作成用のヘルパ関数をテストする"""
        mock_callback_helper = self.enterContext(patch("nnmm.main_window.MainWindow.callback_helper"))
        instance = self._get_instance()
        name = "テスト"
        process_base_class = "テスト用クラス"

        actual = instance.process_helper(name, process_base_class)
        expect = {
            "name": "テスト",
            "func": mock_callback_helper.return_value,
        }
        self.assertEqual(expect, actual)

        actual = instance.process_helper("---", None)
        expect = {
            "name": None,
            "func": None,
        }
        self.assertEqual(expect, actual)

    def test_create_mylist_tab_layout(self):
        """マイリストタブのレイアウトをテストする"""
        mock_list = [
            self.enterContext(patch("nnmm.main_window.QGroupBox")),
            self.enterContext(patch("nnmm.main_window.QVBoxLayout")),
            self.enterContext(patch("nnmm.main_window.QHBoxLayout")),
            self.enterContext(patch("nnmm.main_window.MainWindow.component_helper")),
            self.enterContext(patch("nnmm.main_window.QListWidget")),
            self.enterContext(patch("nnmm.main_window.MainWindow.list_context_menu")),
            self.enterContext(patch("nnmm.main_window.MainWindow.callback_helper")),
            self.enterContext(patch("nnmm.main_window.QLineEdit")),
            self.enterContext(patch("nnmm.main_window.QTableWidget")),
            self.enterContext(patch("nnmm.main_window.MainWindow.table_context_menu")),
            self.enterContext(patch("nnmm.main_window.QGridLayout")),
        ]

        WINDOW_WIDTH = 1200
        WINDOW_HEIGHT = 850
        instance = self._get_instance()
        actual = instance.create_mylist_tab_layout(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.assertEqual(mock_list[0].return_value, actual)
        self.assertTrue(hasattr(instance, "list_widget"))
        self.assertTrue(hasattr(instance, "oneline_log"))
        self.assertTrue(hasattr(instance, "table_widget"))
        self.assertTrue(hasattr(instance, "tbox_mylist_url"))

        expect = [
            [
                call.setMinimumWidth(WINDOW_WIDTH * 1 / 4),
                call.setMinimumHeight(WINDOW_HEIGHT),
                call.setStyleSheet("""
            QListWidget {
              background-color: #121213;
            }
            QListWidget::item:disabled:hover,
            QListWidget::item:hover:!selected,
            QListWidget::item:hover:!active{
              background: none;
            }"""),
                call.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu),
                call.customContextMenuRequested.connect(mock_list[5]),
                call.doubleClicked.connect(mock_list[6].return_value),
            ],
            [],
            [
                call.setMinimumWidth(WINDOW_WIDTH * 3 / 4),
                call.setMinimumHeight(WINDOW_HEIGHT),
                call.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection),
                call.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows),
                call.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers),
                call.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu),
                call.customContextMenuRequested.connect(mock_list[9]),
            ],
            [],
        ]
        actual = [
            instance.list_widget.mock_calls,
            instance.oneline_log.mock_calls,
            instance.table_widget.mock_calls,
            instance.tbox_mylist_url.mock_calls,
        ]
        for e, a in zip(expect, actual, strict=True):
            self.assertEqual(e, a)

    def test_list_context_menu(self):
        """マイリストタブのコンテキストメニューをテストする"""
        instance = self._get_instance()
        instance.list_widget = MagicMock()
        pos = 100

        mock_qmenu = self.enterContext(patch("nnmm.main_window.QMenu"))
        mock_process_helper = self.enterContext(patch("nnmm.main_window.MainWindow.process_helper"))

        def process_helper(name, process):
            if name == "---":
                return {
                    "name": None,
                    "func": None,
                }
            return {
                "name": name,
                "func": f"{name}_{repr(process)}",
            }

        mock_process_helper.side_effect = process_helper

        actual = instance.list_context_menu(pos)
        self.assertEqual(None, actual)

        process_list = [
            instance.process_helper("---", None),
            instance.process_helper("全動画表示", show_mylist_info_all.ShowMylistInfoAll),
            instance.process_helper("マイリストURLをクリップボードにコピー", copy_mylist_url.CopyMylistUrl),
            instance.process_helper("---", None),
            instance.process_helper("視聴済にする（選択）", watched_mylist.WatchedMylist),
            instance.process_helper("視聴済にする（全て）", watched_all_mylist.WatchedAllMylist),
            instance.process_helper("---", None),
            instance.process_helper("上に移動", move_up.MoveUp),
            instance.process_helper("下に移動", move_down.MoveDown),
            instance.process_helper("---", None),
            instance.process_helper("マイリスト追加", create_mylist.CreateMylist),
            instance.process_helper("マイリスト削除", delete_mylist.DeleteMylist),
            instance.process_helper("---", None),
            instance.process_helper("検索（マイリスト名）", search.MylistSearch),
            instance.process_helper("検索（動画名）", search.MylistSearchFromVideo),
            instance.process_helper("検索（URL）", search.MylistSearchFromMylistURL),
            instance.process_helper("強調表示を解除", search.MylistSearchClear),
            instance.process_helper("---", None),
            instance.process_helper("情報表示", popup.PopupMylistWindow),
        ]

        expect = []
        for process in process_list:
            if not process["func"]:
                expect.append(call.addSeparator())
            else:
                expect.append(call.addAction(process["name"]))
                expect.append(call.addAction().triggered.connect(process["func"]))
        expect.append(call.exec(instance.list_widget.mapToGlobal(pos)))

        for e, a in zip(expect, mock_qmenu.return_value.mock_calls, strict=True):
            self.assertEqual(e, a)

    def test_table_context_menu(self):
        """テーブルタブのコンテキストメニューをテストする"""
        instance = self._get_instance()
        instance.table_widget = MagicMock()
        pos = 100

        mock_qmenu = self.enterContext(patch("nnmm.main_window.QMenu"))
        mock_process_helper = self.enterContext(patch("nnmm.main_window.MainWindow.process_helper"))

        def process_helper(name, process):
            if name == "---":
                return {
                    "name": None,
                    "func": None,
                }
            return {
                "name": name,
                "func": f"{name}_{repr(process)}",
            }

        mock_process_helper.side_effect = process_helper

        actual = instance.table_context_menu(pos)
        self.assertEqual(None, actual)

        process_list = [
            instance.process_helper("---", None),
            instance.process_helper("ブラウザで開く", video_play.VideoPlay),
            instance.process_helper(
                "ブラウザで開く（フォーカスを戻す）", video_play_with_focus_back.VideoPlayWithFocusBack
            ),
            instance.process_helper("動画URLをクリップボードにコピー", copy_video_url.CopyVideoUrl),
            instance.process_helper("---", None),
            instance.process_helper("視聴済にする", watched.Watched),
            instance.process_helper("未視聴にする", not_watched.NotWatched),
            instance.process_helper("---", None),
            instance.process_helper("検索（動画名）", search.VideoSearch),
            instance.process_helper("強調表示を解除", search.VideoSearchClear),
            instance.process_helper("---", None),
            instance.process_helper("情報表示", popup.PopupVideoWindow),
        ]

        expect = []
        for process in process_list:
            if not process["func"]:
                expect.append(call.addSeparator())
            else:
                expect.append(call.addAction(process["name"]))
                expect.append(call.addAction().triggered.connect(process["func"]))
        expect.append(call.exec(instance.table_widget.mapToGlobal(pos)))

        for e, a in zip(expect, mock_qmenu.return_value.mock_calls, strict=True):
            self.assertEqual(e, a)

    def test_create_config_tab_layout(self):
        """設定タブのレイアウトをテストする（create_config_tab_layout）"""
        mock_list = [
            self.enterContext(patch("nnmm.main_window.QGroupBox")),
            self.enterContext(patch("nnmm.main_window.QVBoxLayout")),
            self.enterContext(patch("nnmm.main_window.QLabel")),
            self.enterContext(patch("nnmm.main_window.QHBoxLayout")),
            self.enterContext(patch("nnmm.main_window.QLineEdit")),
            self.enterContext(patch("nnmm.main_window.MainWindow.component_helper")),
            self.enterContext(patch("nnmm.main_window.QComboBox")),
        ]

        WINDOW_WIDTH = 1200
        WINDOW_HEIGHT = 850
        instance = self._get_instance()
        actual = instance.create_config_tab_layout(WINDOW_WIDTH, WINDOW_HEIGHT)

        # 返り値はグループボックスのインスタンス（モックの return_value）
        self.assertEqual(mock_list[0].return_value, actual)

        # インスタンスに主要なウィジェット属性が設定されていること
        self.assertTrue(hasattr(instance, "tbox_browser_path"))
        self.assertTrue(hasattr(instance, "cbox"))
        self.assertTrue(hasattr(instance, "tbox_rss_save_path"))
        self.assertTrue(hasattr(instance, "tbox_db_path"))

        # component_helper は 6 回呼ばれる（各種ボタン生成）
        self.assertEqual(6, mock_list[5].call_count)

        # QVBoxLayout は group (QGroupBox) を引数に作成されている
        mock_list[1].assert_called_with(mock_list[0].return_value)

        vbox = mock_list[1].return_value

        # vbox に対して addStretch が呼ばれていること
        self.assertTrue(any(c[0] == "addStretch" for c in vbox.mock_calls))

        # 最後に追加されるボタン（component_helper の戻り値）が
        # 右寄せで vbox.addWidget に渡されていることを確認する
        expected_call = call.addWidget(mock_list[5].return_value, alignment=Qt.AlignmentFlag.AlignRight)
        self.assertTrue(any(c == expected_call for c in vbox.mock_calls))

    def test_update_mylist_pane(self):
        """マイリスト表示更新（update_mylist_pane）のテスト"""
        # create_layout はデフォルトでモックされるようにしてインスタンス作成
        # update_mylist_pane は実際のメソッドをテストするので True を渡す
        instance = self._get_instance(use_update_mylist_pane=True)

        # list_widget をモックに差し替えて呼び出しを検証可能にする
        instance.list_widget = MagicMock()

        # DB の返却値を用意（2 件目を新着扱いにする）
        m1 = self._get_mylist_dict(1)
        m2 = self._get_mylist_dict(2)
        m2["is_include_new"] = True
        instance.mylist_db.select.return_value = [m1, m2]

        # 実行
        res = instance.update_mylist_pane()

        # 結果と呼ばれたメソッドを検証
        self.assertEqual(Result.success, res)
        instance.list_widget.clear.assert_called_once()

        # addItem が 2 回呼ばれていること
        add_calls = instance.list_widget.addItem.call_args_list
        self.assertEqual(2, len(add_calls))

        # 1件目は文字列（通常アイテム）
        self.assertEqual(m1["showname"], add_calls[0][0][0])

        # 2件目は QListWidgetItem（新着アイテム、先頭に NEW_MARK が付く）
        item_arg = add_calls[1][0][0]
        self.assertIsInstance(item_arg, QListWidgetItem)
        self.assertEqual(m2["showname"], item_arg.text())

    def test_init_config(self):
        """設定初期化処理のテスト（init_config）"""
        mock_callback_helper = self.enterContext(patch("nnmm.main_window.MainWindow.callback_helper"))

        instance = self._get_instance(use_init_config=True)
        actual = instance.init_config()
        self.assertEqual(Result.success, actual)

        mock_callback_helper.assert_called_with("設定ロード", config.ConfigLoad)
        mock_callback_helper.return_value.assert_called()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
