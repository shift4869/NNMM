# coding: utf-8
"""MainWindow のテスト
"""

import copy
import sys
import unittest
from contextlib import ExitStack
from logging import INFO, getLogger
from mock import MagicMock, patch, mock_open
from pathlib import Path

import PySimpleGUI as sg

from NNMM.MainWindow import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import *

TEST_DB_PATH = "./test/test.db"


class TestWindowMain(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_MainWindowInit(self):
        """WindowMainの初期化後の状態をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.MainWindow.logger.info"))
            mockwd = stack.enter_context(patch("NNMM.MainWindow.sg.Window"))
            mockcps = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.SetConfig"))
            mockcpg = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig"))
            mockmdbc = stack.enter_context(patch("NNMM.MainWindow.MylistDBController"))
            mockmidbc = stack.enter_context(patch("NNMM.MainWindow.MylistInfoDBController"))
            mockmmwl = stack.enter_context(patch("NNMM.MainWindow.MainWindow.MakeMainWindowLayout"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mockums = stack.enter_context(patch("NNMM.MainWindow.UpdateMylistShow"))

            mockmmwl.return_value = [["dummy layout"]]

            expect_config = {"db": {"save_path": TEST_DB_PATH}}
            mockcpg.side_effect = lambda: expect_config

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

            def r_mock_window(title, layout, size, finalize, resizable):
                return r_mock
            mockwd.side_effect = r_mock_window

            # インスタンス生成->__init__実行
            mw = MainWindow()

            # インスタンス生成後状態確認
            # config
            test_db_path = str(Path(TEST_DB_PATH))
            mockcps.assert_called_once()
            mockcpg.assert_called_once()
            self.assertEqual(expect_config, mw.config)
            self.assertEqual(test_db_path, str(Path(mw.db_fullpath)))

            # cal[{n回目の呼び出し}][args=0]
            # cal[{n回目の呼び出し}][kwargs=1]
            mdbccal = mockmdbc.call_args_list
            self.assertEqual(len(mdbccal), 1)
            self.assertEqual({"db_fullpath": test_db_path}, mdbccal[0][1])
            self.assertEqual(mockmdbc(), mw.mylist_db)
            mockmdbc.reset_mock()

            midbccal = mockmidbc.call_args_list
            self.assertEqual(len(midbccal), 1)
            self.assertEqual({"db_fullpath": test_db_path}, midbccal[0][1])
            self.assertEqual(mockmidbc(), mw.mylist_info_db)
            mockmidbc.reset_mock()

            mockmmwl.assert_called_once()

            wdcal = mockwd.call_args_list
            self.assertEqual(len(wdcal), 1)
            self.assertEqual(("NNMM", mockmmwl.return_value), wdcal[0][0])
            self.assertEqual({
                "size": (1130, 900),
                "finalize": True,
                "resizable": True,
            }, wdcal[0][1])
            self.assertEqual(r_mock, mw.window)
            mockwd.reset_mock()

            lcfccal = mocklcfc.call_args_list
            self.assertEqual(len(lcfccal), 1)
            self.assertEqual(("./log/logging.ini", ), lcfccal[0][0])
            self.assertEqual({"disable_existing_loggers": False}, lcfccal[0][1])
            mocklcfc.reset_mock()

            umscal = mockums.call_args_list
            self.assertEqual(len(umscal), 1)
            self.assertEqual((r_mock, mockmdbc()), umscal[0][0])
            mockums.reset_mock()

            # イベントと処理の辞書
            # 新機能を追加したらここにも追加する
            expect_ep_dict = {
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
                "-ALL_UPDATE_THREAD_PROGRESS-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadProgress,
                "-ALL_UPDATE_THREAD_DONE-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadDone,
                "-PARTIAL_UPDATE-": ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfo,
                "-PARTIAL_UPDATE_THREAD_PROGRESS-": ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfoThreadProgress,
                "-PARTIAL_UPDATE_THREAD_DONE-": ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfoThreadDone,
                "-C_CONFIG_SAVE-": ConfigMain.ProcessConfigSave,
                "-C_MYLIST_SAVE-": ConfigMain.ProcessMylistSaveCSV,
                "-C_MYLIST_LOAD-": ConfigMain.ProcessMylistLoadCSV,
                "-TIMER_SET-": Timer.ProcessTimer,
            }
            self.assertEqual(expect_ep_dict, mw.ep_dict)
        pass

    def test_MakeMainWindowLayout(self):
        """WindowMainのレイアウトをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.MainWindow.logger.info"))
            # mockwd = stack.enter_context(patch("NNMM.MainWindow.sg.Window"))
            mockcps = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.SetConfig"))
            mockcpg = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig"))
            mockmdbc = stack.enter_context(patch("NNMM.MainWindow.MylistDBController"))
            mockmidbc = stack.enter_context(patch("NNMM.MainWindow.MylistInfoDBController"))
            # mockmmwl = stack.enter_context(patch("NNMM.MainWindow.MainWindow.MakeMainWindowLayout"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mockums = stack.enter_context(patch("NNMM.MainWindow.UpdateMylistShow"))
            mockcmgcl = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfigLayout"))

            def DummyCFLayout():
                cf_layout = [[
                    sg.Frame("Config", [
                        [sg.Text("dummy layout")]
                    ], size=(1070, 100))
                ]]
                return cf_layout
            mockcmgcl.side_effect = DummyCFLayout

            mw = None
            # with ExitStack() as stack2:
            #     mockwd = stack2.enter_context(patch("NNMM.MainWindow.sg.Window"))
            #     mockmmwl = stack2.enter_context(patch("NNMM.MainWindow.MainWindow.MakeMainWindowLayout"))
            mw = MainWindow()

            def ExpectMakeMainWindowLayout():
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
                    [sg.Button(" partial(intarval update) ", key="-PARTIAL_UPDATE-"), sg.Button(" all(forced update) ", key="-ALL_UPDATE-")],
                    [sg.Button("  +  ", key="-CREATE-"), sg.Button("  -  ", key="-DELETE-"), sg.Input("", key="-INPUT2-", size=(24, 10))],
                ]

                # 右ペイン
                table_cols_name = [" No. ", "   動画ID   ", "               動画名               ", "    投稿者    ", "  状況  ", "     投稿日時      ", "動画URL", "所属マイリストURL"]
                cols_width = [20, 20, 20, 20, 80, 100, 0, 0]
                def_data = [["", "", "", "", "", "", "", ""]]
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
                        "動画ダウンロード::-TR-",
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
                    [sg.Input("", key="-INPUT1-", size=(91, 100)), sg.Button("更新", key="-UPDATE-"), sg.Button("終了", key="-EXIT-")],
                    [sg.Column([[t]], expand_x=True)],
                ]

                # ウィンドウのレイアウト
                mf_layout = [[
                    sg.Frame("Main", [
                        [sg.Column(l_pane, expand_x=True), sg.Column(r_pane, expand_x=True, element_justification="right")]
                    ], size=(1070, 100))
                ]]
                cf_layout = DummyCFLayout()
                lf_layout = [[
                    sg.Frame("ログ", [
                        [sg.Column([[sg.Output(size=(1080, 100), echo_stdout_stderr=True)]])]
                    ], size=(1070, 100))
                ]]
                layout = [[
                    sg.TabGroup([[
                        sg.Tab("マイリスト", mf_layout),
                        sg.Tab("設定", cf_layout),
                        sg.Tab("ログ", lf_layout)
                    ]], key="-TAB_CHANGED-", enable_events=True)
                ]]
                return layout

            # 正常系
            actual = mw.MakeMainWindowLayout()
            expect = ExpectMakeMainWindowLayout()

            def CheckLayout(e, a):
                """sgオブジェクトは別IDで生成されるため、各要素を比較する
                    self.assertEqual(expect, actual)
                """
                # typeチェック
                self.assertEqual(type(e), type(a))
                # イテラブルなら再起
                if hasattr(e, "__iter__") and hasattr(a, "__iter__"):
                    self.assertEqual(len(e), len(a))
                    for e1, a1 in zip(e, a):
                        CheckLayout(e1, a1)
                # Rows属性を持つなら再起
                if hasattr(e, "Rows") and hasattr(a, "Rows"):
                    for e2, a2 in zip(e.Rows, a.Rows):
                        CheckLayout(e2, a2)
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

            try:
                # 作成したレイアウトを比較
                CheckLayout(expect, actual)

                # 作成したウィンドウのイベントを処理してクローズしないとdelエラーが出る
                # THINK::一瞬だけウィンドウが生成されて見えてしまう・・
                mw.window.read()
                mw.window.close()
            except Exception:
                pass
        pass

    def test_Run(self):
        """WindowMainのメインベントループをテストする
        """
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
