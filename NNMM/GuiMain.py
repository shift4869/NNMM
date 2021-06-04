# coding: utf-8
import logging.config
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

# 左ペイン
l_pane = [
    [sg.Listbox(["a", "b", "c"], key="-LIST-", enable_events=False, size=(40, 100), auto_size_text=True)]
]

# 右ペイン
table_cols = ["No.", "  動画ID  ", "               動画名               ", "      投稿者      ", "  状況  ", "  投稿日時  "]
cols_width = [20, 20, 20, 20, 80, 80]
def_data = [['x', '0', '0', '0', '00', '0']]
table_style = {
    'values': def_data,
    'headings': table_cols,
    'max_col_width': 500,
    # 'def_col_width': 72 // len(cols_width),
    'def_col_width': cols_width,
    "size": (1000, 1000),
    "auto_size_columns": True,
    "bind_return_key": True,
    'key': '-TABLE-'
}
t = sg.Table(**table_style)
ip = sg.Input("", size=(90, 100))
r_pane = [
    [ip, sg.Button("終了", key="-EXIT-")],
    [sg.Column([[t]], expand_x=True)],
]


def GuiMain():
    # 対象URL例サンプル
    target_url_example = {
        "pixiv": "https://www.pixiv.net/artworks/xxxxxxxx",
        "nijie": "http://nijie.info/view_popup.php?id=xxxxxx",
        "seiga": "https://seiga.nicovideo.jp/seiga/imxxxxxxx",
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
    # window["-LIST-"].bind("<Double-Button1>", "-LIST_D-")
    window['-LIST-'].bind('<Double-Button-1>', "+DOUBLE CLICK+")

    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    logger = getLogger("root")
    logger.setLevel(INFO)

    # イベントのループ
    while True:
        # イベントの読み込み
        event, values = window.read()
        # print(event, values)
        # ウィンドウの×ボタンが押されれば終了
        if event in [sg.WIN_CLOSED, "-EXIT-"]:
            break
        if event == "-LIST-+DOUBLE CLICK+":
            v = values["-LIST-"][0]
            def_data = window['-TABLE-'].Values
            a_data = [v, '0', '0', '0', '00', '0']
            def_data.append(a_data)
            window['-TABLE-'].update(values=def_data)
            print("ok")
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
