# coding: utf-8
import logging.config
from logging import INFO, getLogger
from pathlib import Path
from typing import Text

import PySimpleGUI as sg

from NNMM import GetMyListInfo
from NNMM.MylistDBController import *

# 左ペイン
treedata = sg.TreeData()
treedata.Insert("", "k1", "t1", values=[])
tree_style = {
    "data": treedata,
    "headings": [],
    "auto_size_columns": False,
    "num_rows": 2400,
    "col0_width": 32,
    "key": "-TREE-",
    "show_expanded": False,
    "enable_events": False,
    "justification": "left",
}
l_pane = [
    [sg.Listbox(["willow8713さんの投稿動画", "moco78さんの投稿動画", "エラー値"], key="-LIST-", enable_events=False, size=(40, 100), auto_size_text=True)]
    # [sg.Tree(**tree_style)]
]

# 右ペイン
table_cols_name = [" No. ", "   動画ID   ", "              動画名              ", "    投稿者    ", "  状況  ", "   投稿日時   "]
cols_width = [20, 20, 20, 20, 80, 80]
def_data = [['x', '0', '[ゆっくり実況]\u3000大神\u3000絶景版\u3000その87', '0', '00', '0']]
table_style = {
    'values': def_data,
    'headings': table_cols_name,
    'max_col_width': 500,
    # 'def_col_width': 72 // len(cols_width),
    'def_col_width': cols_width,
    "size": (1000, 1000),
    "auto_size_columns": True,
    "bind_return_key": True,
    "justification": "left",
    'key': '-TABLE-'
}
t = sg.Table(**table_style)
ip = sg.Input("", key="-INPUT1-", size=(90, 100))
r_pane = [
    [ip, sg.Button("終了", key="-EXIT-")],
    [sg.Column([[t]], expand_x=True)],
]

db_fullpath = Path("NNMM_DB.db")
mylist_db = MylistDBController(db_fullpath=str(db_fullpath))


def GuiMain():
    # 対象URL例サンプル
    target_url_example = {
        "willow8713さんの投稿動画": "https://www.nicovideo.jp/user/12899156/video",
        "moco78さんの投稿動画": "https://www.nicovideo.jp/user/1594318/video",
        "エラー値": "https://www.nicovideo.jp/user/error_address/video",
    }

    # ウィンドウのレイアウト
    mf = sg.Frame("F1",
                  [
                      [sg.Column(l_pane, expand_x=True), sg.Column(r_pane, expand_x=True, element_justification="right")]
                  ], size=(1070, 100))
    layout = [
        [mf],
    ]

    # ウィンドウオブジェクトの作成
    window = sg.Window("NNMM", layout, size=(1070, 900), finalize=True, resizable=True)
    # window["-TREE-"].bind("<Double-Button1>", "-LIST_D-")
    window['-LIST-'].bind('<Double-Button-1>', "+DOUBLE CLICK+")

    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    logger = getLogger("root")
    logger.setLevel(INFO)

    # listbox初期化
    m_list = mylist_db.Select()
    list_data = [m["listname"] for m in m_list]
    list_data[0] = "*:" + list_data[0]
    # list_data = sg.TreeData()
    # for r in m_list:
    #     list_data.Insert("", r["listname"], "*" + r["listname"], values=[])
    window['-LIST-'].update(values=list_data)

    def_data = [['y', '0', '[ゆっくり実況]\u3000大神\u3000絶景版\u3000その87', '0', '00', '0']]
    window['-TABLE-'].update(values=def_data)

    # イベントのループ
    while True:
        # イベントの読み込み
        event, values = window.read()
        # print(event, values)
        if event in [sg.WIN_CLOSED, "-EXIT-"]:
            # ウィンドウの×ボタンが押されれば終了
            break
        if event == "-LIST-+DOUBLE CLICK+":
            # リストボックスの項目がダブルクリックされた場合（単一）
            v = values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値
            def_data = window['-TABLE-'].Values  # 現在のtableの全リスト

            # target_url = target_url_example.get(v, "")  # listboxの選択値に対応するアドレス
            if v[:2] == "*:":
                v = v[2:]
            target_url = mylist_db.SelectFromListname(v)[0].get("url")
            window["-INPUT1-"].update(value=target_url)  # 対象マイリスのアドレスをテキストボックスに表示

            # 右ペインのテーブルに表示するマイリスト情報を取得
            def_data = []
            table_cols = ["no", "id", "title", "username", "status", "uploaded", "url"]
            movie_list = GetMyListInfo.GetMyListInfo(target_url)

            # 右ペインのテーブルにマイリスト情報を表示
            for m in movie_list:
                a = [m["no"], m["id"], m["title"], m["username"], m["status"], m["uploaded"]]
                def_data.append(a)
            window['-TABLE-'].update(values=def_data)
            pass
        if event == "-TARGET-":
            work_kind = values["-TARGET-"]
            # print(target_url_example[work_kind])
            window["-WORK_URL_SAMPLE-"].update(target_url_example[work_kind])
        if event == "-RUN-":
            work_kind = values["-TARGET-"]
            work_url = values["-WORK_URL-"]
            save_path = values["-SAVE_PATH-"]
            # print(work_kind + "_" + work_url + "_" + save_path)

            # res = LinkSearchMain.LinkSearchMain(work_kind, work_url, save_path)
            res = -1
            if res == 0:
                logger.info("Process done: success!")
            else:
                logger.info("Process failed...")

    # ウィンドウ終了処理
    window.close()
    return 0


if __name__ == "__main__":
    GuiMain()
