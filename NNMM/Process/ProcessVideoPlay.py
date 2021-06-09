# coding: utf-8
import logging.config
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def ProcessVideoPlay(window, values, mylist_db, mylist_info_db):
    # テーブル右クリックで「再生」が選択された場合

    # テーブルが何も選択されていなかったら何もしない
    if not values["-TABLE-"]:
        return

    # 選択されたテーブル行数
    row = int(values["-TABLE-"][0])
    # 現在のテーブルの全リスト
    def_data = window["-TABLE-"].Values
    # 選択されたテーブル行
    selected = def_data[row]

    # 視聴済にする
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時"]
    # 状況を更新
    if def_data[row][4] != "":
        def_data[row][4] = ""
        window["-TABLE-"].update(values=def_data)

    # 視聴済になったことでマイリストの新着表示を消すかどうか判定する
    if not IsMylistIncludeNewMovie(window["-TABLE-"].Values):
        # マイリストDB更新
        mylist_url = values["-INPUT1-"]
        record = mylist_db.SelectFromURL(mylist_url)[0]
        record["is_include_new"] = False  # 新着マークを更新
        mylist_db.Upsert(record["username"], record["type"], record["listname"],
                         record["url"], record["created_at"], record["is_include_new"])

        # マイリスト画面表示更新
        UpdateMylistShow(window, mylist_db)

    # ブラウザに動画urlを渡す
    video_url = mylist_info_db.SelectFromMovieID(selected[1])[0].get("video_url")
    cmd = "C:/Program Files (x86)/Mozilla Firefox/firefox.exe"
    sp = sg.execute_command_subprocess(cmd, video_url)
    # print(sg.execute_get_results(sp)[0])


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
