# coding: utf-8
import re
import threading
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase
from NNMM.ConfigMain import ProcessConfigBase

logger = getLogger("root")
logger.setLevel(INFO)


class ProcessTimer(ProcessBase.ProcessBase):
    timer_thread = None
    window = None
    values = None

    def __init__(self):
        super().__init__(False, False, "タイマーセット")

    def Run(self, mw):
        self.window = mw.window
        self.values = mw.values

        # タイマーセットイベントが登録された場合
        # v = values["-TIMER_SET-"]
        # if v == "-FIRST_SET-":
        #     pass

        # オートリロード間隔を取得する
        config = ProcessConfigBase.GetConfig()
        i_str = config["general"].get("auto_reload", "")
        if i_str == "(使用しない)" or i_str == "":
            if self.timer_thread:
                self.timer_thread.cancel()
                self.timer_thread = None
            return

        pattern = "^([0-9]+)分毎$"
        interval = int(re.findall(pattern, i_str)[0])

        # 既に更新中なら二重に実行はしない
        pattern = "^更新中\([0-9]+\/[0-9]+\)$|^更新中$"
        v = self.window["-INPUT2-"].get()
        if self.values.get("-TIMER_SET-") == "-FIRST_SET-":
            self.values["-TIMER_SET-"] = ""
            logger.info("Auto-reload -FIRST_SET- ... skip first auto-reload cycle.")

            if self.timer_thread:
                self.timer_thread.cancel()
                self.timer_thread = None

        elif re.search(pattern, v):
            self.values["-TIMER_SET-"] = ""
            logger.info("-ALL_UPDATE- running now ... skip this auto-reload cycle.")
            pass
        else:
            # すべて更新ボタンが押された場合の処理を起動する
            # self.window.write_event_value("-ALL_UPDATE-", "")
            # 一部更新ボタンが押された場合の処理を起動する
            self.window.write_event_value("-PARTIAL_UPDATE-", "")

        # タイマーをセットして起動
        s_interval = interval * 60  # [min] -> [sec]
        # s_interval = 5  # デバッグ用
        self.timer_thread = threading.Timer(s_interval, self.Run, (mw, ))
        # デーモンスレッドはデーモンスレッド以外のスレッドが動いていない場合に自動的に終了される
        self.timer_thread.setDaemon(True)
        self.timer_thread.start()

        dts_format = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now() + timedelta(minutes=interval)
        logger.info(f"Next auto-reload cycle start at {dst.strftime(dts_format)}.")
        return 0


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
