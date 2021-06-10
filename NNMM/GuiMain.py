# coding: utf-8
import logging.config
import time
import threading
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import GetMyListInfo
from NNMM import GuiFunction
from NNMM import ConfigMain
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import *

# 左ペイン
l_pane = [
    [sg.Listbox([], key="-LIST-", enable_events=False, size=(40, 46), auto_size_text=True)],
    [sg.Button("  +  ", key="-CREATE-"), sg.Button("  -  ", key="-DELETE-"), sg.Button(" all ", key="-ALL_UPDATE-"),
     sg.Input("", key="-INPUT2-", size=(24, 10))],
]

# 右ペイン
table_cols_name = [" No. ", "   動画ID   ", "              動画名              ", "    投稿者    ", "  状況  ", "   投稿日時   "]
cols_width = [20, 20, 20, 20, 80, 80]
def_data = [["", "", "", "", "", ""]]
right_click_menu = ["Unused", ["ブラウザで開く", "---", "視聴済にする", "未視聴にする"]]
table_style = {
    "values": def_data,
    "headings": table_cols_name,
    "max_col_width": 500,
    "def_col_width": cols_width,
    "num_rows": 2400,
    "auto_size_columns": True,
    "bind_return_key": True,
    "justification": "left",
    "key": "-TABLE-",
    "right_click_menu": right_click_menu,
}
t = sg.Table(**table_style)
r_pane = [
    [sg.Input("", key="-INPUT1-", size=(84, 100)), sg.Button("更新", key="-UPDATE-"), sg.Button("終了", key="-EXIT-")],
    [sg.Column([[t]], expand_x=True)],
]

# DB操作コンポーネント設定
db_fullpath = Path("NNMM_DB.db")
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
    layout = [
        [sg.TabGroup([[sg.Tab("マイリスト", mf_layout), sg.Tab("設定", cf_layout)]])]
    ]

    # ウィンドウオブジェクトの作成
    window = sg.Window("NNMM", layout, size=(1070, 900), finalize=True, resizable=True)
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

    # イベントのループ
    while True:
        # イベントの読み込み
        event, values = window.read()

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

    # ウィンドウ終了処理
    window.close()
    return 0


if __name__ == "__main__":
    GuiMain()
