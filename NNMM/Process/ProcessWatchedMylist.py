# coding: utf-8
import logging.config
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def ProcessWatchedMylist(window: sg.Window, values: dict, mylist_db: MylistDBController, mylist_info_db: MylistInfoDBController):
    # マイリスト右クリックで「視聴済にする（選択）」が選択された場合
    v = values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値

    if v[:2] == "*:":
        v = v[2:]
    record = mylist_db.SelectFromListname(v)[0]
    mylist_url = record.get("url")

    # マイリストの新着フラグがFalseなら何もしない
    if not record.get("is_include_new"):
        return

    # マイリスト情報内の視聴済フラグを更新
    mylist_info_db.UpdateStatusInMylist(mylist_url, "")
    # マイリストの新着フラグを更新
    mylist_db.UpdateIncludeFlag(mylist_url, False)

    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)
    # テーブル画面表示更新
    UpdateTableShow(window, mylist_db, mylist_info_db)
    

if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
