# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


logger = getLogger("root")
logger.setLevel(INFO)


def ProcessWatched(window: sg.Window, values: dict, mylist_db: MylistDBController, mylist_info_db: MylistInfoDBController):
    # テーブル右クリックで「視聴済にする」が選択された場合

    # 現在のtableの全リスト
    def_data = window["-TABLE-"].Values
    # 現在のマイリストURL
    mylist_url = values["-INPUT1-"]

    # 行が選択されていないなら何もしない
    if not values["-TABLE-"]:
        return

    # 選択された行（複数可）についてすべて処理する
    all_num = len(values["-TABLE-"])
    for i, v in enumerate(values["-TABLE-"]):
        row = int(v)

        # マイリスト情報ステータスDB更新
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時"]
        selected = def_data[row]
        res = mylist_info_db.UpdateStatus(selected[1], mylist_url, "")
        if res == 0:
            logger.info(f'{selected[1]} ({i+1}/{all_num}) -> marked "watched".')
        else:
            logger.info(f"{selected[1]} ({i+1}/{all_num}) -> failed.")

        # テーブル更新
        def_data[row][4] = ""
    window["-TABLE-"].update(values=def_data)

    # テーブルの表示を更新する
    UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)
    window["-TABLE-"].update(select_rows=[row])

    # 視聴済になったことでマイリストの新着表示を消すかどうか判定する
    if not IsMylistIncludeNewVideo(window["-TABLE-"].Values):
        # マイリストDB新着フラグ更新
        mylist_db.UpdateIncludeFlag(mylist_url, False)

        # マイリスト画面表示更新
        UpdateMylistShow(window, mylist_db)


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
