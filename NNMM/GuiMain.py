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

# 左ペイン
listbox_right_click_menu = ["-LISTBOX_RIGHT_CLICK_MENU-", ["! ", "---", "上に移動", "下に移動", "---", "視聴済にする（選択）", "視聴済にする（全て）"]]
l_pane = [
    [sg.Listbox([], key="-LIST-", enable_events=False, size=(40, 46), auto_size_text=True, right_click_menu=listbox_right_click_menu)],
    [sg.Button("  +  ", key="-CREATE-"), sg.Button("  -  ", key="-DELETE-"), sg.Button(" all ", key="-ALL_UPDATE-"),
     sg.Input("", key="-INPUT2-", size=(24, 10))],
]

# 右ペイン
table_cols_name = [" No. ", "   動画ID   ", "               動画名               ", "    投稿者    ", "  状況  ", "     投稿日時     "]
cols_width = [20, 20, 20, 20, 80, 100]
def_data = [["", "", "", "", "", ""]]
table_right_click_menu = ["-TABLE_RIGHT_CLICK_MENU-", ["! ", "---", "ブラウザで開く", "---", "視聴済にする", "未視聴にする"]]
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

# 設定値初期化
ConfigMain.SetConfig()
config = ConfigMain.global_config

# DB操作コンポーネント設定
db_fullpath = Path(config["db"].get("save_path", ""))
mylist_db = MylistDBController(db_fullpath=str(db_fullpath))
mylist_info_db = MylistInfoDBController(db_fullpath=str(db_fullpath))


def GuiMain():
    # ウィンドウのレイアウト
    mf_layout = [[
        sg.Frame("Main", [
            [sg.Column(l_pane, expand_x=True), sg.Column(r_pane, expand_x=True, element_justification="right")]
        ], size=(1070, 100))
    ]]
    cf_layout = ConfigMain.GetConfigLayout()
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

    # ウィンドウオブジェクトの作成
    window = sg.Window("NNMM", layout, size=(1130, 900), finalize=True, resizable=True)
    window["-LIST-"].bind("<Double-Button-1>", "+DOUBLE CLICK+")

    # ログ設定
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    logger = getLogger("root")
    logger.setLevel(INFO)

    # マイリスト一覧初期化
    # DBからマイリスト一覧を取得する
    UpdateMylistShow(window, mylist_db)

    # テーブル初期化
    def_data = [[]]
    window["-TABLE-"].update(values=def_data)

    # タイマーセットイベントを起動
    window.write_event_value("-TIMER_SET-", "-FIRST_SET-")

    # イベントのループ
    while True:
        # イベントの読み込み
        event, values = window.read()
        # print(event, values)

        if event in [sg.WIN_CLOSED, "-EXIT-"]:
            # 終了ボタンかウィンドウの×ボタンが押されれば終了
            break
        if event == "視聴済にする":
            # テーブル右クリックで「視聴済にする」が選択された場合
            ProcessWatched.ProcessWatched(window, values, mylist_db, mylist_info_db)
        if event == "未視聴にする":
            # テーブル右クリックで「未視聴にする」が選択された場合
            ProcessNotWatched.ProcessNotWatched(window, values, mylist_db, mylist_info_db)
        if event == "ブラウザで開く":
            # テーブル右クリックで「ブラウザで開く」が選択された場合
            ProcessVideoPlay.ProcessVideoPlay(window, values, mylist_db, mylist_info_db)
        if event == "上に移動":
            # マイリスト右クリックで「上に移動」が選択された場合
            ProcessMoveUp.ProcessMoveUp(window, values, mylist_db, mylist_info_db)
        if event == "下に移動":
            # マイリスト右クリックで「下に移動」が選択された場合
            ProcessMoveDown.ProcessMoveDown(window, values, mylist_db, mylist_info_db)
        if event == "視聴済にする（選択）":
            # マイリスト右クリックで「視聴済にする（選択）」が選択された場合
            ProcessWatchedMylist.ProcessWatchedMylist(window, values, mylist_db, mylist_info_db)
        if event == "視聴済にする（全て）":
            # マイリスト右クリックで「視聴済にする（全て）」が選択された場合
            ProcessWatchedAllMylist.ProcessWatchedAllMylist(window, values, mylist_db, mylist_info_db)
        if event == "-LIST-+DOUBLE CLICK+":
            # リストボックスの項目がダブルクリックされた場合（単一）
            ProcessShowMylistInfo.ProcessShowMylistInfo(window, values, mylist_db, mylist_info_db)
        if event == "-CREATE-":
            # 左下、マイリスト追加ボタンが押された場合
            ProcessCreateMylist.ProcessCreateMylist(window, values, mylist_db, mylist_info_db)
        if event == "-CREATE_THREAD_DONE-":
            # -CREATE-のマルチスレッド処理が終わった後の処理
            ProcessCreateMylist.ProcessCreateMylistThreadDone(window, values, mylist_db, mylist_info_db)
        if event == "-DELETE-":
            # 左下、マイリスト削除ボタンが押された場合
            ProcessDeleteMylist.ProcessDeleteMylist(window, values, mylist_db, mylist_info_db)
        if event == "-UPDATE-":
            # 右上の更新ボタンが押された場合
            ProcessUpdateMylistInfo.ProcessUpdateMylistInfo(window, values, mylist_db, mylist_info_db)
        if event == "-UPDATE_THREAD_DONE-":
            # -UPDATE-のマルチスレッド処理が終わった後の処理
            ProcessUpdateMylistInfo.ProcessUpdateMylistInfoThreadDone(window, values, mylist_db, mylist_info_db)
        if event == "-ALL_UPDATE-":
            # 左下のすべて更新ボタンが押された場合
            ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo(window, values, mylist_db, mylist_info_db)
        if event == "-ALL_UPDATE_THREAD_PROGRESS-":
            # -ALL_UPDATE-処理中の処理
            ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadProgress(window, values, mylist_db, mylist_info_db)
        if event == "-ALL_UPDATE_THREAD_DONE-":
            # -ALL_UPDATE-のマルチスレッド処理が終わった後の処理
            ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadDone(window, values, mylist_db, mylist_info_db)
        if event == "-TAB_CHANGED-":
            select_tab = values["-TAB_CHANGED-"]
            if select_tab == "設定":
                # 設定タブを開いたときの処理
                ConfigMain.ProcessConfigLoad(window, values, mylist_db, mylist_info_db)
        if event == "-C_CONFIG_SAVE-":
            # 設定保存ボタンが押された場合
            ConfigMain.ProcessConfigSave(window, values, mylist_db, mylist_info_db)
        if event == "-C_MYLIST_SAVE-":
            # マイリスト一覧保存ボタンが押された場合
            ConfigMain.ProcessMylistSaveCSV(window, values, mylist_db, mylist_info_db)
        if event == "-C_MYLIST_LOAD-":
            # マイリスト一覧読込ボタンが押された場合
            ConfigMain.ProcessMylistLoadCSV(window, values, mylist_db, mylist_info_db)
        if event == "-TIMER_SET-":
            # タイマーセットイベントが登録された場合
            Timer.ProcessTimer(window, values, mylist_db, mylist_info_db)

    # ウィンドウ終了処理
    window.close()
    return 0


if __name__ == "__main__":
    GuiMain()
