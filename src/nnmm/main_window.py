import asyncio
import logging.config
import traceback
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process import base, config, copy_mylist_url, copy_video_url, create_mylist, delete_mylist, move_down
from nnmm.process import move_up, not_watched, popup, search, show_mylist_info, show_mylist_info_all, timer
from nnmm.process import video_play, video_play_with_focus_back, watched, watched_all_mylist, watched_mylist
from nnmm.process.update_mylist import every, partial, single
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class MainWindow:
    """メインウィンドウクラス"""

    def __init__(self) -> None:
        """メインウィンドウクラスのコンストラクタ"""
        # 設定値初期化
        self.config = config.ConfigBase.set_config()

        # DB操作コンポーネント設定
        self.db_fullpath = Path(self.config["db"].get("save_path", ""))
        self.mylist_db = MylistDBController(db_fullpath=str(self.db_fullpath))
        self.mylist_info_db = MylistInfoDBController(db_fullpath=str(self.db_fullpath))

        # ウィンドウレイアウト作成
        layout = self.make_layout()

        # アイコン画像取得
        ICON_PATH = "./image/icon.png"
        icon_binary = None
        with Path(ICON_PATH).open("rb") as fin:
            icon_binary = fin.read()

        # ウィンドウオブジェクト作成
        self.window = sg.Window("NNMM", layout, icon=icon_binary, size=(1330, 900), finalize=True, resizable=True)
        self.window["-LIST-"].bind("<Double-Button-1>", "+DOUBLE CLICK+")

        # ログ設定
        # ウィンドウレイアウト作成後に行わないとstdout,stderrへの出力がうまくキャッチされない
        # この設定の後からloggerが使用可能になる
        logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
        for name in logging.root.manager.loggerDict:
            if "NNMM" not in name:
                getLogger(name).disabled = True

        # Windows特有のruntimeError抑止
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # マイリスト一覧初期化
        # DBからマイリスト一覧を取得する
        self.update_mylist_pane()

        # テーブル初期化
        def_data = [[]]
        self.window["-TABLE-"].update(values=def_data)

        # タイマーセットイベントを起動
        self.window.write_event_value("-TIMER_SET-", "-FIRST_SET-")

        # イベントと処理の辞書
        self.dict = {
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

        logger.info("window setup done.")

    def make_layout(self) -> list[list[sg.Frame]] | None:
        """画面のレイアウトを作成する

        Returns:
            list[list[sg.Frame]] | None: 成功時PySimpleGUIのレイアウトオブジェクト、失敗時None
        """
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
            [sg.Button(" インターバル更新 ", key="-PARTIAL_UPDATE-"), sg.Button(" すべて更新 ", key="-ALL_UPDATE-")],
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
        cf_layout = config.ConfigBase.make_layout()
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

    def update_mylist_pane(self) -> Result:
        """マイリストペインの初期表示

        Returns:
            Result: 成功時success
        """
        index = 0

        # マイリスト画面表示更新
        NEW_MARK = "*:"
        m_list = self.mylist_db.select()
        include_new_index_list = []
        for i, m in enumerate(m_list):
            if m["is_include_new"]:
                m["showname"] = NEW_MARK + m["showname"]
                include_new_index_list.append(i)
        list_data = [m["showname"] for m in m_list]
        self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        for i in include_new_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # indexをセットしてスクロール
        self.window["-LIST-"].Widget.see(index)
        self.window["-LIST-"].update(set_to_index=index)
        return Result.success

    def run(self) -> Result:
        """メインイベントループ"""
        while True:
            # イベントの読み込み
            event, values = self.window.read()

            if event in [sg.WIN_CLOSED, "-EXIT-"]:
                # 終了ボタンかウィンドウの×ボタンが押されれば終了
                logger.info("window exit.")
                break

            # イベント処理
            if self.dict.get(event):
                self.values = values
                info = ProcessInfo.create(event, self)

                try:
                    pb: base.ProcessBase = self.dict.get(event)(info)

                    if pb is None or not hasattr(pb, "run"):
                        continue

                    pb.run()
                except Exception:
                    logger.error(traceback.format_exc())
                    logger.error("main event loop error.")

            # タブ切り替え
            if event == "-TAB_CHANGED-":
                select_tab = values["-TAB_CHANGED-"]
                if select_tab == "設定":
                    # 設定タブを開いたときの処理
                    self.values = values
                    info = ProcessInfo.create(event, self)
                    pb = config.ConfigLoad(info)
                    pb.run()

        # ウィンドウ終了処理
        self.window.close()
        return Result.success


if __name__ == "__main__":
    mw = MainWindow()
    mw.run()
