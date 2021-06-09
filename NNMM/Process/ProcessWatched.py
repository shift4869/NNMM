# coding: utf-8
import logging.config
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def ProcessWatched(window, values, mylist_db, mylist_info_db):
    # テーブル右クリックで「視聴済にする」が選択された場合
    def_data = window["-TABLE-"].Values  # 現在のtableの全リスト
    for v in values["-TABLE-"]:
        row = int(v)

        # DB更新
        selected = def_data[row]
        record = mylist_info_db.SelectFromMovieID(selected[1])[0]
        record["status"] = ""
        record = mylist_info_db.Upsert(record["video_id"], record["title"], record["username"],
                                       record["status"], record["uploaded_at"], record["video_url"],
                                       record["created_at"])

        # テーブル更新
        def_data[row][4] = ""
    window["-TABLE-"].update(values=def_data)

    # 視聴済になったことでマイリストの新着表示を消すかどうか判定する
    if not IsMylistIncludeNewMovie(window["-TABLE-"].Values):
        # マイリストDB更新
        mylist_url = values["-INPUT1-"]
        record = mylist_db.SelectFromURL(mylist_url)[0]
        record["is_include_new"] = False  # 新着マークを更新
        # record["listname"] = record["listname"][2:]  # *:を削除
        mylist_db.Upsert(record["username"], record["type"], record["listname"],
                         record["url"], record["created_at"], record["is_include_new"])

        # マイリスト画面表示更新
        UpdateMylistShow(window, mylist_db)


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
