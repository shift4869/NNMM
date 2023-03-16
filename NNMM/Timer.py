# coding: utf-8
import re
import threading
from datetime import datetime, timedelta
from logging import INFO, getLogger
from typing import TYPE_CHECKING

import PySimpleGUI as sg

from NNMM.ConfigMain import ProcessConfigBase
from NNMM.Process import ProcessBase

if TYPE_CHECKING:
    from NNMM.MainWindow import MainWindow

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessTimer(ProcessBase.ProcessBase):
    def __init__(self) -> None:
        super().__init__(False, False, "タイマーセット")
        self.timer_thread = None
        self.window = None
        self.values = None

    def run(self, mw: "MainWindow") -> int:
        """タイマー実行時の処理

        Notes:
            "-TIMER_SET-"
            "-FIRST_SET-" が同時に指定されていた場合、初回サイクルとみなしてスキップする

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: タイマーが実行されて後続のイベントが起動したなら0,
                 タイマー実行がスキップされたなら1,
                 オートリロードしない設定なら2,
                 エラー時-1
        """
        result = 0

        # 引数チェック
        try:
            self.window: sg.Window = mw.window
            self.values: dict = mw.values
        except AttributeError:
            logger.error("Timer Init failed, argument error.")
            return -1

        # オートリロード設定を取得する
        config = ProcessConfigBase.GetConfig()
        i_str = config["general"].get("auto_reload", "")
        if i_str == "(使用しない)" or i_str == "":
            # 現在タイマー待機中のものがあればキャンセルする
            if self.timer_thread:
                self.timer_thread.cancel()
                self.timer_thread = None
            return 2

        # オートリロード間隔を取得する
        interval = -1
        try:
            pattern = "^([0-9]+)分毎$"
            interval = int(re.findall(pattern, i_str)[0])
        except IndexError:
            logger.error("Timer Init failed, interval config error.")
            return -1
        if interval < 0:
            logger.error("Timer Init failed, interval config error.")
            return -1

        # スキップ判定
        pattern = "^更新中\([0-9]+\/[0-9]+\)$|^更新中$"
        v = self.window["-INPUT2-"].get()
        if self.values.get("-TIMER_SET-") == "-FIRST_SET-":
            # 初回起動ならスキップ
            self.values["-TIMER_SET-"] = ""
            result = 1
            logger.info("Auto-reload -FIRST_SET- ... skip first auto-reload cycle.")

            # 現在タイマー待機中のものがあればキャンセルする
            if self.timer_thread:
                self.timer_thread.cancel()
                self.timer_thread = None
        elif re.search(pattern, v):
            # 既に更新中ならスキップ
            self.values["-TIMER_SET-"] = ""
            result = 1
            logger.info("-ALL_UPDATE- running now ... skip this auto-reload cycle.")
        else:
            logger.info("Auto-reload start.")
            # すべて更新ボタンが押された場合の処理を起動する
            # self.window.write_event_value("-ALL_UPDATE-", "")
            # 一部更新ボタンが押された場合の処理を起動する
            self.window.write_event_value("-PARTIAL_UPDATE-", "")

        # タイマーをセットして起動
        s_interval = interval * 60  # [min] -> [sec]
        # s_interval = 5  # デバッグ用
        self.timer_thread = threading.Timer(s_interval, self.run, (mw, ))
        # デーモンスレッドはデーモンスレッド以外のスレッドが動いていない場合に自動的に終了される
        self.timer_thread.setDaemon(True)
        self.timer_thread.start()

        # 次回起動時間の予測をログに出力
        dst_df = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now() + timedelta(minutes=interval)
        logger.info(f"Next auto-reload cycle start at {dst.strftime(dst_df)}.")
        return result


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.run()
