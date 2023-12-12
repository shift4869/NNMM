import asyncio
import logging.config
import traceback
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process import process_base, process_config, process_create_mylist, process_delete_mylist, process_move_down, process_move_up, process_not_watched, process_popup, process_search, process_show_mylist_info, process_show_mylist_info_all
from NNMM.process import process_timer, process_update_all_mylist_info, process_update_mylist_info, process_update_partial_mylist_info, process_video_play, process_watched, process_watched_all_mylist, process_watched_mylist
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, update_mylist_pane

logger = getLogger(__name__)
logger.setLevel(INFO)


class MainWindow():
    """メインウィンドウクラス
    """
    def __init__(self) -> None:
        """メインウィンドウクラスのコンストラクタ
        """
        # 設定値初期化
        self.config = process_config.ProcessConfigBase.set_config()

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
        update_mylist_pane(self.window, self.mylist_db)

        # テーブル初期化
        def_data = [[]]
        self.window["-TABLE-"].update(values=def_data)

        # タイマーセットイベントを起動
        self.window.write_event_value("-TIMER_SET-", "-FIRST_SET-")

        # イベントと処理の辞書
        self.process_dict = {
            "ブラウザで開く::-TR-": process_video_play.ProcessVideoPlay,
            "視聴済にする::-TR-": process_watched.ProcessWatched,
            "未視聴にする::-TR-": process_not_watched.ProcessNotWatched,
            "検索（動画名）::-TR-": process_search.ProcessVideoSearch,
            "強調表示を解除::-TR-": process_search.ProcessVideoSearchClear,
            "情報表示::-TR-": process_popup.PopupVideoWindow,
            "全動画表示::-MR-": process_show_mylist_info_all.ProcessShowMylistInfoAll,
            "視聴済にする（選択）::-MR-": process_watched_mylist.ProcessWatchedMylist,
            "視聴済にする（全て）::-MR-": process_watched_all_mylist.ProcessWatchedAllMylist,
            "上に移動::-MR-": process_move_up.ProcessMoveUp,
            "下に移動::-MR-": process_move_down.ProcessMoveDown,
            "マイリスト追加::-MR-": process_create_mylist.ProcessCreateMylist,
            "マイリスト削除::-MR-": process_delete_mylist.ProcessDeleteMylist,
            "検索（マイリスト名）::-MR-": process_search.ProcessMylistSearch,
            "検索（動画名）::-MR-": process_search.ProcessMylistSearchFromVideo,
            "検索（URL）::-MR-": process_search.ProcessMylistSearchFromMylistURL,
            "強調表示を解除::-MR-": process_search.ProcessMylistSearchClear,
            "情報表示::-MR-": process_popup.PopupMylistWindow,
            "-LIST-+DOUBLE CLICK+": process_show_mylist_info.ProcessShowMylistInfo,
            "-CREATE-": process_create_mylist.ProcessCreateMylist,
            "-CREATE_THREAD_DONE-": process_create_mylist.ProcessCreateMylistThreadDone,
            "-DELETE-": process_delete_mylist.ProcessDeleteMylist,
            "-UPDATE-": process_update_mylist_info.ProcessUpdateMylistInfo,
            "-UPDATE_THREAD_DONE-": process_update_mylist_info.ProcessUpdateMylistInfoThreadDone,
            "-ALL_UPDATE-": process_update_all_mylist_info.ProcessUpdateAllMylistInfo,
            "-ALL_UPDATE_THREAD_DONE-": process_update_all_mylist_info.ProcessUpdateAllMylistInfoThreadDone,
            "-PARTIAL_UPDATE-": process_update_partial_mylist_info.ProcessUpdatePartialMylistInfo,
            "-PARTIAL_UPDATE_THREAD_DONE-": process_update_partial_mylist_info.ProcessUpdatePartialMylistInfoThreadDone,
            "-C_CONFIG_SAVE-": process_config.ProcessConfigSave,
            "-C_MYLIST_SAVE-": process_config.ProcessMylistSaveCSV,
            "-C_MYLIST_LOAD-": process_config.ProcessMylistLoadCSV,
            "-TIMER_SET-": process_timer.ProcessTimer,
        }

        logger.info("window setup done.")

    def make_layout(self) -> list[list[sg.Frame]] | None:
        """画面のレイアウトを作成する

        Returns:
            list[list[sg.Frame]] | None: 成功時PySimpleGUIのレイアウトオブジェクト、失敗時None
        """
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
                "検索（URL）::-MR-",
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
        cf_layout = process_config.ProcessConfigBase.make_layout()
        lf_layout = [[
            sg.Frame("ログ", [
                [sg.Column([[
                    sg.Multiline(size=(1080, 100), auto_refresh=True, autoscroll=True, reroute_stdout=True, reroute_stderr=True)
                ]])]
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

    def run(self) -> Result:
        """メインイベントループ
        """
        while True:
            # イベントの読み込み
            event, values = self.window.read()

            if event in [sg.WIN_CLOSED, "-EXIT-"]:
                # 終了ボタンかウィンドウの×ボタンが押されれば終了
                logger.info("window exit.")
                break

            # イベント処理
            if self.process_dict.get(event):
                self.values = values
                process_info = ProcessInfo.create(event, self)

                try:
                    pb: process_base.ProcessBase = self.process_dict.get(event)(process_info)

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
                    process_info = ProcessInfo.create(event, self)
                    pb = process_config.ProcessConfigLoad(process_info)
                    pb.run()

        # ウィンドウ終了処理
        self.window.close()
        return


if __name__ == "__main__":
    mw = MainWindow()
    mw.run()
