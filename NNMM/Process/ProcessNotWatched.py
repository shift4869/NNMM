# coding: utf-8
import logging.config
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def ProcessNotWatched(window, values, mylist_db, mylist_info_db):
    # テーブル右クリックで「未視聴にする」が選択された場合
    def_data = window["-TABLE-"].Values  # 現在のtableの全リスト
    for v in values["-TABLE-"]:
        row = int(v)

        # DB更新
        selected = def_data[row]
        record = mylist_info_db.SelectFromMovieID(selected[1])[0]
        record["status"] = "未視聴"
        record = mylist_info_db.Upsert(record["movie_id"], record["title"], record["username"],
                                       record["status"], record["uploaded_at"], record["url"],
                                       record["created_at"])

        # テーブル更新
        def_data[row][4] = "未視聴"
    window["-TABLE-"].update(values=def_data)

    # 未視聴になったことでマイリストの新着表示を表示する
    # 未視聴にしたので必ず新着あり扱いになる
    # マイリストDB更新
    mylist_url = values["-INPUT1-"]
    record = mylist_db.SelectFromURL(mylist_url)[0]
    record["is_include_new"] = True
    mylist_db.Upsert(record["username"], record["type"], record["listname"],
                     record["url"], record["created_at"], record["is_include_new"])

    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
