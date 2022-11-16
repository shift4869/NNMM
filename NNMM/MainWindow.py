# coding: utf-8
import asyncio
import logging.config
import traceback
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import ConfigMain
from NNMM import Timer
from NNMM import PopupWindowMain
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessWatched
from NNMM.Process import ProcessNotWatched
from NNMM.Process import ProcessVideoPlay
from NNMM.Process import ProcessShowMylistInfo
from NNMM.Process import ProcessShowMylistInfoAll
from NNMM.Process import ProcessCreateMylist
from NNMM.Process import ProcessDeleteMylist
from NNMM.Process import ProcessUpdateMylistInfo
from NNMM.Process import ProcessUpdateAllMylistInfo
from NNMM.Process import ProcessUpdatePartialMylistInfo
from NNMM.Process import ProcessMoveUp
from NNMM.Process import ProcessMoveDown
from NNMM.Process import ProcessWatchedMylist
from NNMM.Process import ProcessWatchedAllMylist
from NNMM.Process import ProcessSearch
from NNMM.Process import ProcessDownload

logger = getLogger("root")
logger.setLevel(INFO)


class MainWindow():
    """メインウィンドウクラス
    """
    def __init__(self):
        """メインウィンドウクラスのコンストラクタ
        """
        # 設定値初期化
        ConfigMain.ProcessConfigBase.SetConfig()
        self.config = ConfigMain.ProcessConfigBase.GetConfig()

        # DB操作コンポーネント設定
        self.db_fullpath = Path(self.config["db"].get("save_path", ""))
        self.mylist_db = MylistDBController(db_fullpath=str(self.db_fullpath))
        self.mylist_info_db = MylistInfoDBController(db_fullpath=str(self.db_fullpath))

        # ウィンドウレイアウト作成
        layout = self.MakeMainWindowLayout()

        # アイコン画像取得
        ICON_PATH = "./image/check_sheet_icon.png"
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
            getLogger(name).disabled = True

        # Windows特有のRuntimeError抑止
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # マイリスト一覧初期化
        # DBからマイリスト一覧を取得する
        UpdateMylistShow(self.window, self.mylist_db)

        # テーブル初期化
        def_data = [[]]
        self.window["-TABLE-"].update(values=def_data)

        # タイマーセットイベントを起動
        self.window.write_event_value("-TIMER_SET-", "-FIRST_SET-")

        # イベントと処理の辞書
        self.ep_dict = {
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

        logger.info("window setup done.")

    def MakeMainWindowLayout(self) -> list[list[sg.Frame]] | None:
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
            [sg.Input("", key="-INPUT1-", size=(120, 100)), sg.Button("更新", key="-UPDATE-"), sg.Button("終了", key="-EXIT-")],
            [sg.Column([[t]], expand_x=True)],
        ]

        # ウィンドウのレイアウト
        mf_layout = [[
            sg.Frame("Main", [
                [sg.Column(l_pane, expand_x=True), sg.Column(r_pane, expand_x=True, element_justification="right")]
            ], size=(1370, 1000))
        ]]
        cf_layout = ConfigMain.ProcessConfigBase.GetConfigLayout()
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

    def Run(self) -> int:
        """メインイベントループ

        Returns:
            int: 正常終了時0
        """
        while True:
            # イベントの読み込み
            event, values = self.window.read()
            # print(event, values)

            if event in [sg.WIN_CLOSED, "-EXIT-"]:
                # 終了ボタンかウィンドウの×ボタンが押されれば終了
                logger.info("window exit.")
                break

            # イベント処理
            if self.ep_dict.get(event):
                self.values = values

                try:
                    pb = self.ep_dict.get(event)()

                    if pb is None or not hasattr(pb, "Run"):
                        continue

                    pb.Run(self)
                except Exception:
                    logger.error(traceback.format_exc())
                    logger.error("main event loop error.")

            # タブ切り替え
            if event == "-TAB_CHANGED-":
                select_tab = values["-TAB_CHANGED-"]
                if select_tab == "設定":
                    # 設定タブを開いたときの処理
                    pb = ConfigMain.ProcessConfigLoad()
                    pb.Run(self)

        # ウィンドウ終了処理
        self.window.close()
        return 0


if __name__ == "__main__":
    mw = MainWindow()
    mw.Run()
