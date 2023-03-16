# coding: utf-8
"""MainWindow のテスト
"""
import sys
import unittest
from contextlib import ExitStack
from logging import WARNING, getLogger
from pathlib import Path

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM import ConfigMain, PopupWindowMain, Timer
from NNMM.MainWindow import MainWindow
from NNMM.Process import ProcessBase, ProcessCreateMylist, ProcessDeleteMylist, ProcessDownload, ProcessMoveDown, ProcessMoveUp, ProcessNotWatched, ProcessSearch, ProcessShowMylistInfo, ProcessShowMylistInfoAll, ProcessUpdateAllMylistInfo
from NNMM.Process import ProcessUpdateMylistInfo, ProcessUpdatePartialMylistInfo, ProcessVideoPlay, ProcessWatched, ProcessWatchedAllMylist, ProcessWatchedMylist

logger = getLogger("NNMM.MainWindow")
logger.setLevel(WARNING)
TEST_DB_PATH = ":memory:"


# テスト用具体化ProcessBase
class ConcreteProcessBase(ProcessBase.ProcessBase):
    def __init__(self) -> None:
        super().__init__(True, False, "テスト用具体化処理")

    def run(self, mw: "MainWindow") -> int:
        return 0


# テスト用具体化ProcessBase(エラー想定)
class ConcreteErrorProcessBase(ProcessBase.ProcessBase):
    def __init__(self) -> None:
        super().__init__(True, False, "テスト用具体化処理")

    def run(self, mw: "MainWindow") -> int:
        raise Exception


class TestWindowMain(unittest.TestCase):
    def test_MainWindowInit(self):
        """WindowMainの初期化後の状態をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockwd = stack.enter_context(patch("NNMM.MainWindow.sg.Window"))
            mockcps = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.set_config"))
            mockmdbc = stack.enter_context(patch("NNMM.MainWindow.MylistDBController"))
            mockmidbc = stack.enter_context(patch("NNMM.MainWindow.MylistInfoDBController"))
            mockmmwl = stack.enter_context(patch("NNMM.MainWindow.MainWindow.make_layout"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mockump = stack.enter_context(patch("NNMM.MainWindow.update_mylist_pane"))

            mockmmwl.return_value = [["dummy layout"]]

            expect_config = {"db": {"save_path": TEST_DB_PATH}}
            mockcps.side_effect = lambda: expect_config

            r_mock = MagicMock()
            b_mock = MagicMock()
            type(b_mock).bind = lambda s, b, k: f"{b}_{k}"
            u_mock = MagicMock()
            type(u_mock).update = lambda s, values: values
            expect_window_dict = {
                "-LIST-": b_mock,
                "-TABLE-": u_mock,
            }
            r_mock.__getitem__.side_effect = expect_window_dict.__getitem__
            r_mock.__iter__.side_effect = expect_window_dict.__iter__
            r_mock.__contains__.side_effect = expect_window_dict.__contains__
            type(r_mock).write_event_value = lambda s, k, v: f"{k}_{v}"

            def r_mock_window(title, layout, icon, size, finalize, resizable):
                return r_mock
            mockwd.side_effect = r_mock_window

            # インスタンス生成->__init__実行
            mw = MainWindow()

            # インスタンス生成後状態確認
            # config
            mockcps.assert_called_once()
            self.assertEqual(expect_config, mw.config)
            self.assertEqual(TEST_DB_PATH, str(Path(mw.db_fullpath)))

            # cal[{n回目の呼び出し}][args=0]
            # cal[{n回目の呼び出し}][kwargs=1]
            mdbccal = mockmdbc.call_args_list
            self.assertEqual(len(mdbccal), 1)
            self.assertEqual({"db_fullpath": TEST_DB_PATH}, mdbccal[0][1])
            self.assertEqual(mockmdbc(), mw.mylist_db)
            mockmdbc.reset_mock()

            midbccal = mockmidbc.call_args_list
            self.assertEqual(len(midbccal), 1)
            self.assertEqual({"db_fullpath": TEST_DB_PATH}, midbccal[0][1])
            self.assertEqual(mockmidbc(), mw.mylist_info_db)
            mockmidbc.reset_mock()

            mockmmwl.assert_called_once()

            ICON_PATH = "./image/icon.png"
            icon_binary = None
            with Path(ICON_PATH).open("rb") as fin:
                icon_binary = fin.read()
            expect = [
                call("NNMM", mockmmwl.return_value, icon=icon_binary, size=(1330, 900), finalize=True, resizable=True)
            ]
            self.assertEqual(expect, mockwd.mock_calls)
            self.assertEqual(r_mock, mw.window)
            mockwd.reset_mock()

            lcfccal = mocklcfc.call_args_list
            self.assertEqual(len(lcfccal), 1)
            self.assertEqual(("./log/logging.ini", ), lcfccal[0][0])
            self.assertEqual({"disable_existing_loggers": False}, lcfccal[0][1])
            mocklcfc.reset_mock()

            umscal = mockump.call_args_list
            self.assertEqual(len(umscal), 1)
            self.assertEqual((r_mock, mockmdbc()), umscal[0][0])
            mockump.reset_mock()

            # イベントと処理の辞書
            # 新機能を追加したらここにも追加する
            expect_process_dict = {
                "ブラウザで開く::-TR-": ProcessVideoPlay.ProcessVideoPlay,
                "視聴済にする::-TR-": ProcessWatched.ProcessWatched,
                "未視聴にする::-TR-": ProcessNotWatched.ProcessNotWatched,
                "検索（動画名）::-TR-": ProcessSearch.ProcessVideoSearch,
                "強調表示を解除::-TR-": ProcessSearch.ProcessVideoSearchClear,
                "情報表示::-TR-": PopupWindowMain.PopupVideoWindow,
                "動画ダウンロード::-TR-": ProcessDownload.ProcessDownload,
                "全動画表示::-MR-": ProcessShowMylistInfoAll.ProcessShowMylistInfoAll,
                "視聴済にする（選択）::-MR-": ProcessWatchedMylist.ProcessWatchedMylist,
                "視聴済にする（全て）::-MR-": ProcessWatchedAllMylist.ProcessWatchedAllMylist,
                "上に移動::-MR-": ProcessMoveUp.ProcessMoveUp,
                "下に移動::-MR-": ProcessMoveDown.ProcessMoveDown,
                "マイリスト追加::-MR-": ProcessCreateMylist.ProcessCreateMylist,
                "マイリスト削除::-MR-": ProcessDeleteMylist.ProcessDeleteMylist,
                "検索（マイリスト名）::-MR-": ProcessSearch.ProcessMylistSearch,
                "検索（動画名）::-MR-": ProcessSearch.ProcessMylistSearchFromVideo,
                "強調表示を解除::-MR-": ProcessSearch.ProcessMylistSearchClear,
                "情報表示::-MR-": PopupWindowMain.PopupMylistWindow,
                "-LIST-+DOUBLE CLICK+": ProcessShowMylistInfo.ProcessShowMylistInfo,
                "-CREATE-": ProcessCreateMylist.ProcessCreateMylist,
                "-CREATE_THREAD_DONE-": ProcessCreateMylist.ProcessCreateMylistThreadDone,
                "-DELETE-": ProcessDeleteMylist.ProcessDeleteMylist,
                "-DOWNLOAD-": ProcessDownload.ProcessDownload,
                "-DOWNLOAD_THREAD_DONE-": ProcessDownload.ProcessDownloadThreadDone,
                "-UPDATE-": ProcessUpdateMylistInfo.ProcessUpdateMylistInfo,
                "-UPDATE_THREAD_DONE-": ProcessUpdateMylistInfo.ProcessUpdateMylistInfoThreadDone,
                "-ALL_UPDATE-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo,
                "-ALL_UPDATE_THREAD_DONE-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadDone,
                "-PARTIAL_UPDATE-": ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfo,
                "-PARTIAL_UPDATE_THREAD_DONE-": ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfoThreadDone,
                "-C_CONFIG_SAVE-": ConfigMain.ProcessConfigSave,
                "-C_MYLIST_SAVE-": ConfigMain.ProcessMylistSaveCSV,
                "-C_MYLIST_LOAD-": ConfigMain.ProcessMylistLoadCSV,
                "-TIMER_SET-": Timer.ProcessTimer,
            }
            self.assertEqual(expect_process_dict, mw.process_dict)
        pass

    def test_make_layout(self):
        """WindowMainのレイアウトをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            # mockwd = stack.enter_context(patch("NNMM.MainWindow.sg.Window"))
            mockcps = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.set_config"))
            mockcpg = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.get_config"))
            mockmdbc = stack.enter_context(patch("NNMM.MainWindow.MylistDBController"))
            mockmidbc = stack.enter_context(patch("NNMM.MainWindow.MylistInfoDBController"))
            # mockmmwl = stack.enter_context(patch("NNMM.MainWindow.MainWindow.make_layout"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mockump = stack.enter_context(patch("NNMM.MainWindow.update_mylist_pane"))
            mockcmgcl = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.make_layout"))

            # sg.Outputだけは標準エラー等に干渉するためdummyに置き換える
            mockop = stack.enter_context(patch("NNMM.MainWindow.sg.Output"))
            mockop.side_effect = lambda size, echo_stdout_stderr: sg.Text("dummy")

            # configレイアウトのdummy
            def DummyCFLayout():
                cf_layout = [[
                    sg.Frame("Config", [
                        [sg.Text("dummy layout")]
                    ], size=(1370, 100))
                ]]
                return cf_layout
            mockcmgcl.side_effect = DummyCFLayout

            # インスタンス生成
            mw = None
            with ExitStack() as stack2:
                mockwd = stack2.enter_context(patch("NNMM.MainWindow.sg.Window"))
                mockmmwl = stack2.enter_context(patch("NNMM.MainWindow.MainWindow.make_layout"))
                mw = MainWindow()

            # レイアウト予測値生成
            def make_layout():
                # 左ペイン
                listbox_right_click_menu = [
                    "-LISTBOX_RIGHT_CLICK_MENU-", [
                        "! ",
                        "---",
                        "全動画表示::-MR-",
                        "---",
                        "視聴済にする（選択）::-MR-",
                        "視聴済にする（全て）::-MR-",
                        "---",
                        "上に移動::-MR-",
                        "下に移動::-MR-",
                        "---",
                        "マイリスト追加::-MR-",
                        "マイリスト削除::-MR-",
                        "---",
                        "検索（マイリスト名）::-MR-",
                        "検索（動画名）::-MR-",
                        "強調表示を解除::-MR-",
                        "---",
                        "情報表示::-MR-",
                    ]
                ]
                l_pane = [
                    [sg.Listbox([], key="-LIST-", enable_events=False, size=(40, 44), auto_size_text=True, right_click_menu=listbox_right_click_menu)],
                    [sg.Button(" インターバル更新 ", key="-PARTIAL_UPDATE-"), sg.Button(" すべて更新 ", key="-ALL_UPDATE-")],
                    [sg.Button("  +  ", key="-CREATE-"), sg.Button("  -  ", key="-DELETE-"), sg.Input("", key="-INPUT2-", size=(24, 10))],
                ]

                # 右ペイン
                table_cols_name = ["No.", "   動画ID   ", "                動画名                ", "   投稿者   ", "  状況  ", "     投稿日時      ", "     登録日時      ", "動画URL", "所属マイリストURL"]
                cols_width = [20, 20, 20, 20, 80, 100, 100, 0, 0]
                def_data = [["", "", "", "", "", "", "", "", ""]]
                table_right_click_menu = [
                    "-TABLE_RIGHT_CLICK_MENU-", [
                        "! ",
                        "---",
                        "ブラウザで開く::-TR-",
                        "---",
                        "視聴済にする::-TR-",
                        "未視聴にする::-TR-",
                        "---",
                        "検索（動画名）::-TR-",
                        "強調表示を解除::-TR-",
                        "---",
                        "情報表示::-TR-",
                        "---",
                        "!動画ダウンロード::-TR-",
                    ]
                ]
                table_style = {
                    "values": def_data,
                    "headings": table_cols_name,
                    "max_col_width": 600,
                    "def_col_width": cols_width,
                    "num_rows": 2400,
                    "auto_size_columns": True,
                    "bind_return_key": True,
                    "justification": "left",
                    "key": "-TABLE-",
                    "right_click_menu": table_right_click_menu,
                }
                t = sg.Table(**table_style)
                r_pane = [
                    [sg.Input("", key="-INPUT1-", size=(120, 100)), sg.Button("更新", key="-UPDATE-"), sg.Button("終了", key="-EXIT-")],
                    [sg.Column([[t]], expand_x=True)],
                ]

                # ウィンドウのレイアウト
                mf_layout = [[
                    sg.Frame("Main", [
                        [sg.Column(l_pane, expand_x=True), sg.Column(r_pane, expand_x=True, element_justification="right")]
                    ], size=(1370, 1000))
                ]]
                cf_layout = DummyCFLayout()
                lf_layout = [[
                    sg.Frame("ログ", [
                        [sg.Column([[sg.Output(size=(1080, 100), echo_stdout_stderr=True)]])]
                    ], size=(1370, 1000))
                ]]
                layout = [[
                    sg.TabGroup([[
                        sg.Tab("マイリスト", mf_layout),
                        sg.Tab("設定", cf_layout),
                        sg.Tab("ログ", lf_layout)
                    ]], key="-TAB_CHANGED-", enable_events=True)
                ]]
                return layout

            # 実行
            actual = mw.make_layout()
            expect = make_layout()

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

            # 作成したレイアウトを比較
            actual = check_layout(expect, actual)
            self.assertEqual(0, actual)
        pass

    def test_run(self):
        """WindowMainのメインベントループをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch.object(logger, "info"))
            mockle = stack.enter_context(patch.object(logger, "error"))
            mockwd = stack.enter_context(patch("NNMM.MainWindow.sg.Window"))
            mockcps = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.set_config"))
            mockcpg = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.get_config"))
            mockmdbc = stack.enter_context(patch("NNMM.MainWindow.MylistDBController"))
            mockmidbc = stack.enter_context(patch("NNMM.MainWindow.MylistInfoDBController"))
            mockmmwl = stack.enter_context(patch("NNMM.MainWindow.MainWindow.make_layout"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mockump = stack.enter_context(patch("NNMM.MainWindow.update_mylist_pane"))
            mockcmgcl = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.make_layout"))
            mockcmpcl = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigLoad"))

            def r_mock_window(title, layout, icon, size, finalize, resizable):
                r_mock = MagicMock()
                v_mock = MagicMock()
                v_mock.side_effect = [
                    ("-DO_TEST-", "do something"),
                    ("-TAB_CHANGED-", {"-TAB_CHANGED-": "設定"}),
                    ("-TAB_CHANGED-", {"-TAB_CHANGED-": "ログ"}),
                    ("-NONE_TEST-", "none"),
                    ("-ERROR_TEST-", "error"),
                    ("-EXIT-", "exit"),
                ]
                type(r_mock).read = v_mock
                type(r_mock).close = lambda s: 0
                return r_mock
            mockwd.side_effect = r_mock_window

            # 実行
            mw = MainWindow()
            mw.process_dict["-DO_TEST-"] = ConcreteProcessBase
            mw.process_dict["-NONE_TEST-"] = lambda: None
            mw.process_dict["-ERROR_TEST-"] = ConcreteErrorProcessBase
            actual = mw.run()
            self.assertEqual(0, actual)

            ICON_PATH = "./image/icon.png"
            icon_binary = None
            with Path(ICON_PATH).open("rb") as fin:
                icon_binary = fin.read()
            mockwd.assert_called_once_with("NNMM", mockmmwl.return_value, icon=icon_binary, size=(1330, 900), finalize=True, resizable=True)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
