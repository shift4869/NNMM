# coding: utf-8
import logging.config
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def ProcessNotWatched(window, values, mylist_db, mylist_info_db):
    # テーブル右クリックで「未視聴にする」が選択された場合

    # 現在のtableの全リスト
    def_data = window["-TABLE-"].Values
    # 現在のマイリストURL
    mylist_url = values["-INPUT1-"]

    # 行が選択されていないなら何もしない
    if not values["-TABLE-"]:
        return

    # 選択された行（複数可）についてすべて処理する
    for v in values["-TABLE-"]:
        row = int(v)

        # マイリスト情報ステータスDB更新
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時"]
        selected = def_data[row]
        mylist_info_db.UpdateStatus(selected[1], mylist_url, "未視聴")

        # テーブル更新
        def_data[row][4] = "未視聴"
    window["-TABLE-"].update(values=def_data)

    # テーブルの表示を更新する
    UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)
    window["-TABLE-"].update(select_rows=[row])

    # 未視聴になったことでマイリストの新着表示を表示する
    # 未視聴にしたので必ず新着あり扱いになる
    # マイリストDB新着フラグ更新
    mylist_db.UpdateIncludeFlag(mylist_url, True)

    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
