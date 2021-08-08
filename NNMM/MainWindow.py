# coding: utf-8
import logging.config
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import ConfigMain
from NNMM import Timer
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import *


logger = getLogger("root")
logger.setLevel(INFO)


class MainWindow():
    """メインウィンドウクラス
    """
    def __init__(self):
        # 設定値初期化
        ConfigMain.ProcessConfigBase.SetConfig()
        self.config = ConfigMain.ProcessConfigBase.GetConfig()

        # DB操作コンポーネント設定
        self.db_fullpath = Path(self.config["db"].get("save_path", ""))
        self.mylist_db = MylistDBController(db_fullpath=str(self.db_fullpath))
        self.mylist_info_db = MylistInfoDBController(db_fullpath=str(self.db_fullpath))

        # ウィンドウレイアウト作成
        layout = self.MakeMainWindowLayout()

        # ウィンドウオブジェクト作成
        self.window = sg.Window("NNMM", layout, size=(1130, 900), finalize=True, resizable=True)
        self.window["-LIST-"].bind("<Double-Button-1>", "+DOUBLE CLICK+")

        # ログ設定
        # ウィンドウレイアウト作成後に行わないとstdout,stderrへの出力がうまくキャッチされない
        # この設定の後からloggerが使用可能になる
        logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)

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
            # "イベントキー": (開始ログ出力するか, 終了ログ出力するか, "処理名", 処理関数)
            # "視聴済にする::-TR-": (True, True, "視聴済にする", ProcessWatched.ProcessWatched),
            # "未視聴にする::-TR-": (True, True, "未視聴にする", ProcessNotWatched.ProcessNotWatched),
            # "ブラウザで開く::-TR-": (True, True, "ブラウザで開く", ProcessVideoPlay.ProcessVideoPlay),
            # "上に移動::-MR-": (True, True, "上に移動", ProcessMoveUp.ProcessMoveUp),
            # "下に移動::-MR-": (True, True, "下に移動", ProcessMoveDown.ProcessMoveDown),
            # "視聴済にする（選択）::-MR-": (True, True, "視聴済にする（選択）", ProcessWatchedMylist.ProcessWatchedMylist),
            # "視聴済にする（全て）::-MR-": (True, True, "視聴済にする（全て）", ProcessWatchedAllMylist.ProcessWatchedAllMylist),
            # "検索::-MR-": (True, True, "マイリスト検索", ProcessSearch.ProcessMylistSearch),
            # "-LIST-+DOUBLE CLICK+": (True, True, "マイリスト内容表示", ProcessShowMylistInfo.ProcessShowMylistInfo),
            # "-CREATE-": (True, False, "マイリスト追加", ProcessCreateMylist.ProcessCreateMylist),
            # "-CREATE_THREAD_DONE-": (False, True, "マイリスト追加", ProcessCreateMylist.ProcessCreateMylistThreadDone),
            # "-DELETE-": (True, True, "マイリスト削除", ProcessDeleteMylist.ProcessDeleteMylist),
            # "-UPDATE-": (True, False, "マイリスト内容更新", ProcessUpdateMylistInfo.ProcessUpdateMylistInfo),
            # "-UPDATE_THREAD_DONE-": (False, True, "マイリスト内容更新", ProcessUpdateMylistInfo.ProcessUpdateMylistInfoThreadDone),
            # "-ALL_UPDATE-": (True, False, "全マイリスト内容更新", ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo),
            # "-ALL_UPDATE_THREAD_PROGRESS-": (False, False, "全マイリスト内容更新", ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadProgress),
            # "-ALL_UPDATE_THREAD_DONE-": (False, True, "全マイリスト内容更新", ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadDone),
            # "-C_CONFIG_SAVE-": (True, True, "設定保存", ConfigMain.ProcessConfigSave),
            # "-C_MYLIST_SAVE-": (True, True, "マイリスト一覧出力", ConfigMain.ProcessMylistSaveCSV),
            # "-C_MYLIST_LOAD-": (True, True, "マイリスト一覧入力", ConfigMain.ProcessMylistLoadCSV),
            # "-TIMER_SET-": (False, False, "タイマーセット", Timer.ProcessTimer),
        }

        # イベントと処理の辞書(new)
        self.epc_dict = {
            "視聴済にする::-TR-": ProcessWatched.ProcessWatched,
            "未視聴にする::-TR-": ProcessNotWatched.ProcessNotWatched,
            "ブラウザで開く::-TR-": ProcessVideoPlay.ProcessVideoPlay,
            "上に移動::-MR-": ProcessMoveUp.ProcessMoveUp,
            "下に移動::-MR-": ProcessMoveDown.ProcessMoveDown,
            "視聴済にする（選択）::-MR-": ProcessWatchedMylist.ProcessWatchedMylist,
            "視聴済にする（全て）::-MR-": ProcessWatchedAllMylist.ProcessWatchedAllMylist,
            "検索::-MR-": ProcessSearch.ProcessMylistSearch,
            "-LIST-+DOUBLE CLICK+": ProcessShowMylistInfo.ProcessShowMylistInfo,
            "-CREATE-": ProcessCreateMylist.ProcessCreateMylist,
            "-CREATE_THREAD_DONE-": ProcessCreateMylist.ProcessCreateMylistThreadDone,
            "-DELETE-": ProcessDeleteMylist.ProcessDeleteMylist,
            "-UPDATE-": ProcessUpdateMylistInfo.ProcessUpdateMylistInfo,
            "-UPDATE_THREAD_DONE-": ProcessUpdateMylistInfo.ProcessUpdateMylistInfoThreadDone,
            "-ALL_UPDATE-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo,
            "-ALL_UPDATE_THREAD_PROGRESS-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadProgress,
            "-ALL_UPDATE_THREAD_DONE-": ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadDone,
            "-C_CONFIG_SAVE-": ConfigMain.ProcessConfigSave,
            "-C_MYLIST_SAVE-": ConfigMain.ProcessMylistSaveCSV,
            "-C_MYLIST_LOAD-": ConfigMain.ProcessMylistLoadCSV,
            "-TIMER_SET-": Timer.ProcessTimer,
        }

        logger.info("window setup done.")

    def MakeMainWindowLayout(self):
        # 左ペイン
        listbox_right_click_menu = [
            "-LISTBOX_RIGHT_CLICK_MENU-", [
                "! ",
                "---",
                "上に移動::-MR-",
                "下に移動::-MR-",
                "---",
                "視聴済にする（選択）::-MR-",
                "視聴済にする（全て）::-MR-",
                "---",
                "検索::-MR-",
            ]
        ]
        l_pane = [
            [sg.Listbox([], key="-LIST-", enable_events=False, size=(40, 46), auto_size_text=True, right_click_menu=listbox_right_click_menu)],
            [sg.Button("  +  ", key="-CREATE-"), sg.Button("  -  ", key="-DELETE-"), sg.Button(" all ", key="-ALL_UPDATE-"),
             sg.Input("", key="-INPUT2-", size=(24, 10))],
        ]

        # 右ペイン
        table_cols_name = [" No. ", "   動画ID   ", "               動画名               ", "    投稿者    ", "  状況  ", "     投稿日時     "]
        cols_width = [20, 20, 20, 20, 80, 100]
        def_data = [["", "", "", "", "", ""]]
        table_right_click_menu = [
            "-TABLE_RIGHT_CLICK_MENU-", [
                "! ",
                "---",
                "ブラウザで開く::-TR-",
                "---",
                "視聴済にする::-TR-",
                "未視聴にする::-TR-"
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
        cf_layout = ConfigMain.ProcessConfigBase.GetConfigLayout()
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

    def Run(self):
        # イベントのループ
        while True:
            # イベントの読み込み
            event, values = self.window.read()
            # print(event, values)

            if event in [sg.WIN_CLOSED, "-EXIT-"]:
                # 終了ボタンかウィンドウの×ボタンが押されれば終了
                logger.info("window exit.")
                break

            # イベント処理(new)
            if self.epc_dict.get(event):
                self.values = values
                pb = self.epc_dict.get(event)()

                if pb.log_sflag:
                    logger.info(f'"{pb.process_name}" starting.')

                pb.Run(self)

                if pb.log_eflag:
                    logger.info(f'"{pb.process_name}" finished.')

            # イベント処理
            if self.ep_dict.get(event):
                t = self.ep_dict.get(event)
                log_sflag = t[0]
                log_eflag = t[1]
                p_str = t[2]
                p_func = t[3]

                if log_sflag:
                    logger.info(f'"{p_str}" starting.')

                p_func(self.window, values, self.mylist_db, self.mylist_info_db)

                if log_eflag:
                    logger.info(f'"{p_str}" finished.')

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
