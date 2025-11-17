import sys
import unittest
from contextlib import ExitStack
from pathlib import Path

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
    def _get_instance(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("nnmm.main_window.logger.info"))
            mockwd = stack.enter_context(patch("nnmm.main_window.QDialog", spec=QDialog))
            mockcps = stack.enter_context(patch("nnmm.main_window.config.ConfigBase.set_config"))
            mockcpg = stack.enter_context(patch("nnmm.main_window.config.ConfigBase.get_config"))
            mockmdbc = stack.enter_context(patch("nnmm.main_window.MylistDBController", spec=MylistDBController))
            mockmidbc = stack.enter_context(
                patch("nnmm.main_window.MylistInfoDBController", spec=MylistInfoDBController)
            )
            mockmmwl = stack.enter_context(patch("nnmm.main_window.MainWindow.make_layout"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mock_logger_dict = stack.enter_context(patch("logging.root.manager.loggerDict"))
            mockump = stack.enter_context(patch("nnmm.main_window.MainWindow.update_mylist_pane"))
            mockcmgcl = stack.enter_context(patch("nnmm.main_window.config.ConfigBase.make_layout"))
            mockcmpcl = stack.enter_context(patch("nnmm.main_window.config.ConfigLoad"))
            mockpi = stack.enter_context(patch("nnmm.main_window.ProcessInfo.create"))
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
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("nnmm.main_window.logger.info"))
            mockwd = stack.enter_context(patch("nnmm.main_window.QDialog"))
            mockcps = stack.enter_context(patch("nnmm.main_window.config.ConfigBase.set_config"))
            mockmdbc = stack.enter_context(patch("nnmm.main_window.MylistDBController"))
            mockmidbc = stack.enter_context(patch("nnmm.main_window.MylistInfoDBController"))
            mockmmwl = stack.enter_context(patch("nnmm.main_window.MainWindow.make_layout"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mockump = stack.enter_context(patch("nnmm.main_window.MainWindow.update_mylist_pane"))

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
            self.assertEqual(("./log/logging.ini",), lcfccal[0][0])
            self.assertEqual({"disable_existing_loggers": False}, lcfccal[0][1])
            mocklcfc.reset_mock()

            mockump.assert_called_once_with()
            mockump.reset_mock()

            # イベントと処理の辞書
            expect_dict = {
                "ブラウザで開く::-TR-": video_play.VideoPlay,
                "ブラウザで開く（フォーカスを戻す）::-TR-": video_play_with_focus_back.VideoPlayWithFocusBack,
                "動画URLをクリップボードにコピー::-TR-": copy_video_url.CopyVideoUrl,
                "視聴済にする::-TR-": watched.Watched,
                "未視聴にする::-TR-": not_watched.NotWatched,
                "検索（動画名）::-TR-": search.VideoSearch,
                "強調表示を解除::-TR-": search.VideoSearchClear,
                "情報表示::-TR-": popup.PopupVideoWindow,
                "全動画表示::-MR-": show_mylist_info_all.ShowMylistInfoAll,
                "マイリストURLをクリップボードにコピー::-MR-": copy_mylist_url.CopyMylistUrl,
                "視聴済にする（選択）::-MR-": watched_mylist.WatchedMylist,
                "視聴済にする（全て）::-MR-": watched_all_mylist.WatchedAllMylist,
                "上に移動::-MR-": move_up.MoveUp,
                "下に移動::-MR-": move_down.MoveDown,
                "マイリスト追加::-MR-": create_mylist.CreateMylist,
                "マイリスト削除::-MR-": delete_mylist.DeleteMylist,
                "検索（マイリスト名）::-MR-": search.MylistSearch,
                "検索（動画名）::-MR-": search.MylistSearchFromVideo,
                "検索（URL）::-MR-": search.MylistSearchFromMylistURL,
                "強調表示を解除::-MR-": search.MylistSearchClear,
                "情報表示::-MR-": popup.PopupMylistWindow,
                "-LIST-+DOUBLE CLICK+": show_mylist_info.ShowMylistInfo,
                "-CREATE-": create_mylist.CreateMylist,
                "-CREATE_THREAD_DONE-": create_mylist.CreateMylistThreadDone,
                "-DELETE-": delete_mylist.DeleteMylist,
                "-UPDATE-": single.Single,
                "-UPDATE_THREAD_DONE-": single.SingleThreadDone,
                "-ALL_UPDATE-": every.Every,
                "-ALL_UPDATE_THREAD_DONE-": every.EveryThreadDone,
                "-PARTIAL_UPDATE-": partial.Partial,
                "-PARTIAL_UPDATE_THREAD_DONE-": partial.PartialThreadDone,
                "-C_CONFIG_SAVE-": config.ConfigSave,
                "-C_MYLIST_SAVE-": config.MylistSaveCSV,
                "-C_MYLIST_LOAD-": config.MylistLoadCSV,
                "-TIMER_SET-": timer.Timer,
            }
            self.assertEqual(expect_dict, mw.dict)
        pass

    def test_make_layout(self):
        """WindowMainのレイアウトをテストする"""
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("nnmm.main_window.logger.info"))
            mockcps = stack.enter_context(patch("nnmm.main_window.config.ConfigBase.set_config"))
            mockcpg = stack.enter_context(patch("nnmm.main_window.config.ConfigBase.get_config"))
            mockmdbc = stack.enter_context(patch("nnmm.main_window.MylistDBController"))
            mockmidbc = stack.enter_context(patch("nnmm.main_window.MylistInfoDBController"))
            mocklcfc = stack.enter_context(patch("logging.config.fileConfig"))
            mockump = stack.enter_context(patch("nnmm.main_window.MainWindow.update_mylist_pane"))
            mockcmgcl = stack.enter_context(patch("nnmm.main_window.config.ConfigBase.make_layout"))

            # sg.Outputだけは標準エラー等に干渉するためdummyに置き換える
            mockop = stack.enter_context(patch("nnmm.main_window.sg.Output"))
            mockop.side_effect = lambda size, echo_stdout_stderr: sg.Text("dummy")

            # configレイアウトのdummy
            def DummyCFLayout():
                cf_layout = [[sg.Frame("Config", [[sg.Text("dummy layout")]], size=(1370, 100))]]
                return cf_layout

            mockcmgcl.side_effect = DummyCFLayout

            # インスタンス生成
            mw = None
            with ExitStack() as stack2:
                mockwd = stack2.enter_context(patch("nnmm.main_window.QDialog"))
                mockmmwl = stack2.enter_context(patch("nnmm.main_window.MainWindow.make_layout"))
                mw = MainWindow()

            # レイアウト予測値生成
            def make_layout():
                # 左ペイン
                listbox_right_click_menu = [
                    "-LISTBOX_RIGHT_CLICK_MENU-",
                    [
                        "! ",
                        "---",
                        "全動画表示::-MR-",
                        "マイリストURLをクリップボードにコピー::-MR-",
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
                        "検索（URL）::-MR-",
                        "強調表示を解除::-MR-",
                        "---",
                        "情報表示::-MR-",
                    ],
                ]
                l_pane = [
                    [
                        sg.Listbox(
                            [],
                            key="-LIST-",
                            enable_events=False,
                            size=(40, 44),
                            auto_size_text=True,
                            right_click_menu=listbox_right_click_menu,
                        )
                    ],
                    [
                        sg.Button(" インターバル更新 ", key="-PARTIAL_UPDATE-"),
                        sg.Button(" すべて更新 ", key="-ALL_UPDATE-"),
                    ],
                    [
                        sg.Button("  +  ", key="-CREATE-"),
                        sg.Button("  -  ", key="-DELETE-"),
                        sg.Input("", key="-INPUT2-", size=(24, 10)),
                    ],
                ]

                # 右ペイン
                table_cols_name = [
                    "No.",
                    "   動画ID   ",
                    "                動画名                ",
                    "   投稿者   ",
                    "  状況  ",
                    "     投稿日時      ",
                    "     登録日時      ",
                    "動画URL",
                    "所属マイリストURL",
                ]
                cols_width = [20, 20, 20, 20, 80, 100, 100, 0, 0]
                def_data = [["", "", "", "", "", "", "", "", ""]]
                table_right_click_menu = [
                    "-TABLE_RIGHT_CLICK_MENU-",
                    [
                        "! ",
                        "---",
                        "ブラウザで開く::-TR-",
                        "ブラウザで開く（フォーカスを戻す）::-TR-",
                        "動画URLをクリップボードにコピー::-TR-",
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
                    ],
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
                    [
                        sg.Input("", key="-INPUT1-", size=(120, 100)),
                        sg.Button("更新", key="-UPDATE-"),
                        sg.Button("終了", key="-EXIT-"),
                    ],
                    [sg.Column([[t]], expand_x=True)],
                ]

                # ウィンドウのレイアウト
                mf_layout = [
                    [
                        sg.Frame(
                            "Main",
                            [
                                [
                                    sg.Column(l_pane, expand_x=True),
                                    sg.Column(r_pane, expand_x=True, element_justification="right"),
                                ]
                            ],
                            size=(1370, 1000),
                        )
                    ]
                ]
                cf_layout = DummyCFLayout()
                lf_layout = [
                    [
                        sg.Frame(
                            "ログ",
                            [
                                [
                                    sg.Column([
                                        [
                                            sg.Multiline(
                                                size=(1080, 100),
                                                auto_refresh=True,
                                                autoscroll=True,
                                                reroute_stdout=True,
                                                reroute_stderr=True,
                                            )
                                        ]
                                    ])
                                ]
                            ],
                            size=(1370, 1000),
                        )
                    ]
                ]
                layout = [
                    [
                        sg.TabGroup(
                            [[sg.Tab("マイリスト", mf_layout), sg.Tab("設定", cf_layout), sg.Tab("ログ", lf_layout)]],
                            key="-TAB_CHANGED-",
                            enable_events=True,
                        )
                    ]
                ]
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

    def test_update_mylist_pane(self):
        with ExitStack() as stack:
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

    def test_run(self):
        """WindowMainのメインベントループをテストする"""
        with ExitStack() as stack:
            mock_config_load = stack.enter_context(patch("nnmm.main_window.config.ConfigLoad"))
            mock_logger = stack.enter_context(patch("nnmm.main_window.logger.error"))

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
