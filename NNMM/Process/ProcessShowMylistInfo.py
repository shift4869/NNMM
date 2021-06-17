# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


logger = getLogger("root")
logger.setLevel(INFO)


def ProcessShowMylistInfo(window, values, mylist_db, mylist_info_db):
    # リストボックスの項目がダブルクリックされた場合（単一）
    v = values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値
    def_data = window["-TABLE-"].Values  # 現在のtableの全リスト

    if v[:2] == "*:":
        v = v[2:]
    record = mylist_db.SelectFromListname(v)[0]
    username = record.get("username")
    mylist_url = record.get("url")
    window["-INPUT1-"].update(value=mylist_url)  # 対象マイリスのアドレスをテキストボックスに表示

    # テーブル更新
    UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)

    logger.info(f"{mylist_url} -> mylist info shown.")


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
