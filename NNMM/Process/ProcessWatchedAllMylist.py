# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


logger = getLogger("root")
logger.setLevel(INFO)


def ProcessWatchedAllMylist(window: sg.Window, values: dict, mylist_db: MylistDBController, mylist_info_db: MylistInfoDBController):
    # マイリスト右クリックで「視聴済にする（全て）」が選択された場合
    m_list = mylist_db.Select()
    records = [m for m in m_list if m["is_include_new"]]

    all_num = len(records)
    for i, record in enumerate(records):
        mylist_url = record.get("url")

        # マイリストの新着フラグがFalseなら何もしない
        if not record.get("is_include_new"):
            continue

        # マイリスト情報内の視聴済フラグを更新
        mylist_info_db.UpdateStatusInMylist(mylist_url, "")
        # マイリストの新着フラグを更新
        mylist_db.UpdateIncludeFlag(mylist_url, False)

        logger.info(f'{mylist_url} -> all include videos status are marked "watched" ... ({i + 1}/{all_num}).')

    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)
    # テーブル画面表示更新
    UpdateTableShow(window, mylist_db, mylist_info_db)
    

if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
