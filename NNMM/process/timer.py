import re
import threading
from datetime import datetime, timedelta
from logging import INFO, getLogger

from NNMM.process.base import ProcessBase
from NNMM.process.config import ConfigBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class Timer(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.timer_thread = None

    def _timer_cancel(self) -> None:
        """現在タイマー待機中のものがあればキャンセルする"""
        if self.timer_thread:
            self.timer_thread.cancel()
            self.timer_thread = None

    def run(self) -> Result:
        """タイマー実行時の処理

        Notes:
            "-TIMER_SET-"
            "-FIRST_SET-" が同時に指定されていた場合、初回サイクルとみなしてスキップする

        Returns:
            Result: 成功時success, エラー時failed
        """
        # オートリロード設定を取得する
        config = ConfigBase.get_config()
        i_str = config["general"].get("auto_reload", "")
        if i_str == "(使用しない)" or i_str == "":
            # オートリロード間隔が設定されていないならばスキップ
            # 現在タイマー待機中のものがあればキャンセルする
            self._timer_cancel()
            return Result.failed

        # オートリロード間隔を取得する
        interval = -1
        try:
            pattern = r"^([0-9]+)分毎$"
            interval = int(re.findall(pattern, i_str)[0])
        except IndexError:
            logger.error("Timer Init failed, interval config error.")
            return Result.failed

        # 更新処理スキップ判定
        pattern = r"^.*(取得中|更新中).*$"
        v = self.get_bottom_textbox().to_str()
        if self.values.get("-TIMER_SET-") == "-FIRST_SET-":
            # 初回起動ならスキップ
            self.values["-TIMER_SET-"] = ""
            logger.info("Auto-reload -FIRST_SET- ... skip first auto-reload cycle.")
        elif re.search(pattern, v):
            # 既に更新処理中ならスキップ
            self.values["-TIMER_SET-"] = ""
            logger.info("-ALL_UPDATE- running now ... skip this auto-reload cycle.")
        else:
            # 更新処理起動
            # すべて更新ボタンが押された場合の処理を起動する
            # self.window.write_event_value("-ALL_UPDATE-", "")
            # 一部更新ボタンが押された場合の処理を起動する
            self.window.write_event_value("-PARTIAL_UPDATE-", "")
            logger.info("Auto-reload start.")

        # 現在タイマー待機中のものがあればキャンセルする
        self._timer_cancel()

        # 次回起動タイマーをセット
        s_interval = interval * 60  # [min] -> [sec]
        self.timer_thread = threading.Timer(s_interval, self.run)
        self.timer_thread.setDaemon(True)
        self.timer_thread.start()

        # 次回起動時間の予測をログに出力
        dst_df = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now() + timedelta(minutes=interval)
        logger.info(f"Next auto-reload cycle start at {dst.strftime(dst_df)}.")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
