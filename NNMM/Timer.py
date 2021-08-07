# coding: utf-8
import re
import threading
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import ConfigMain
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


logger = getLogger("root")
logger.setLevel(INFO)

timer_thread = None


def ProcessTimer(window, values, mylist_db, mylist_info_db):
    global timer_thread

    # タイマーセットイベントが登録された場合
    # v = values["-TIMER_SET-"]
    # if v == "-FIRST_SET-":
    #     pass

    # オートリロード間隔を取得する
    config = ConfigMain.GetConfig()
    i_str = config["general"].get("auto_reload", "")
    if i_str == "(使用しない)" or i_str == "":
        if timer_thread:
            timer_thread.cancel()
            timer_thread = None
        return

    pattern = "^([0-9]+)分毎$"
    interval = int(re.findall(pattern, i_str)[0])

    # 既に更新中なら二重に実行はしない
    pattern = "^更新中\([0-9]+\/[0-9]+\)$|^更新中$"
    v = window["-INPUT2-"].get()
    if values["-TIMER_SET-"] == "-FIRST_SET-":
        values["-TIMER_SET-"] = ""
        logger.info("Auto-reload -FIRST_SET- ... skip first auto-reload cycle.")

        if timer_thread:
            timer_thread.cancel()
            timer_thread = None

    elif re.search(pattern, v):
        values["-TIMER_SET-"] = ""
        logger.info("-ALL_UPDATE- running now ... skip this auto-reload cycle.")
        pass
    else:
        # すべて更新ボタンが押された場合の処理を起動する
        window.write_event_value("-ALL_UPDATE-", "")

    # タイマーをセットして起動
    # interval = 5
    s_interval = interval * 60  # [min] -> [sec]
    timer_thread = threading.Timer(s_interval, ProcessTimer, (window, values, mylist_db, mylist_info_db))
    # デーモンスレッドはデーモンスレッド以外のスレッドが動いていない場合に自動的に終了される
    timer_thread.setDaemon(True)
    timer_thread.start()

    dts_format = "%Y-%m-%d %H:%M:%S"
    dst = datetime.now() + timedelta(minutes=interval)
    logger.info(f"Next auto-reload cycle start at {dst.strftime(dts_format)}.")
    return


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
