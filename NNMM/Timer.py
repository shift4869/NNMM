# coding: utf-8
import logging.config
import re
import threading
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import ConfigMain
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *


def ProcessTimer(window, values, mylist_db, mylist_info_db):
    # global timer_thread

    # タイマーセットイベントが登録された場合
    # v = values["-TIMER_SET-"]
    # if v == "-FIRST_SET-":
    #     pass

    # オートリロード間隔を取得する
    config = ConfigMain.GetConfig()
    i_str = config["general"].get("auto_reload", "")
    if i_str == "(使用しない)" or i_str == "":
        return

    pattern = "^([0-9]+)分毎$"
    interval = int(re.findall(pattern, i_str)[0])

    # 既に更新中なら二重に実行はしない
    pattern = "^更新中\([0-9]+\/[0-9]+\)$|^更新中$"
    v = window["-INPUT2-"].get()
    if re.search(pattern, v) or values["-TIMER_SET-"] == "-FIRST_SET-":
        values["-TIMER_SET-"] = ""
        print("-ALL_UPDATE- running now ... skip this auto-reload cycle.")
        pass
    else:
        # すべて更新ボタンが押された場合の処理を起動する
        window.write_event_value("-ALL_UPDATE-", "")

    # タイマーをセットして起動
    # interval = 5
    interval = interval * 60  # [min] -> [sec]
    timer_thread = threading.Timer(interval, ProcessTimer, (window, values, mylist_db, mylist_info_db))
    timer_thread.start()

    return


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
