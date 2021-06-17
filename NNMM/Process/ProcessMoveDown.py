# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


logger = getLogger("root")
logger.setLevel(INFO)


def ProcessMoveDown(window: sg.Window, values: dict, mylist_db: MylistDBController, mylist_info_db: MylistInfoDBController):
    # マイリスト右クリックで「下に移動」が選択された場合
    src_index = 0
    if window["-LIST-"].get_indexes():
        src_index = window["-LIST-"].get_indexes()[0]
    src_v = values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値
    list_data = window["-LIST-"].Values  # 現在のtableの全リスト

    max_index = len(mylist_db.Select()) - 1
    if src_index >= max_index:
        logger.info(f"{src_v} -> index is {max_index} , can't move down.")
        return

    if src_v[:2] == "*:":
        src_v = src_v[2:]
    src_record = mylist_db.SelectFromListname(src_v)[0]

    dst_index = src_index + 1
    dst_v = list_data[dst_index]
    if dst_v[:2] == "*:":
        dst_v = dst_v[2:]
    dst_record = mylist_db.SelectFromListname(dst_v)[0]

    mylist_db.SwapId(src_record["id"], dst_record["id"])

    # テーブル更新
    UpdateMylistShow(window, mylist_db)
    window["-LIST-"].update(set_to_index=dst_index)

    logger.info(f"{src_v} -> index move down from {src_index} to {dst_index}.")


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
