import re
import threading
from datetime import datetime, timedelta
from logging import INFO, getLogger

from NNMM.config_main import ProcessConfigBase
from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessTimer(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.timer_thread = None

    def run(self) -> None:
        """タイマー実行時の処理

        Notes:
            "-TIMER_SET-"
            "-FIRST_SET-" が同時に指定されていた場合、初回サイクルとみなしてスキップする
        """
        # オートリロード設定を取得する
        config = ProcessConfigBase.get_config()
        i_str = config["general"].get("auto_reload", "")
        if i_str == "(使用しない)" or i_str == "":
            # 現在タイマー待機中のものがあればキャンセルする
            if self.timer_thread:
                self.timer_thread.cancel()
                self.timer_thread = None
            return

        # オートリロード間隔を取得する
        interval = -1
        try:
            pattern = "^([0-9]+)分毎$"
            interval = int(re.findall(pattern, i_str)[0])
        except IndexError:
            logger.error("Timer Init failed, interval config error.")
            return
        if interval < 0:
            logger.error("Timer Init failed, interval config error.")
            return

        # スキップ判定
        pattern = r"^更新中\([0-9]+\/[0-9]+\)$|^更新中$"
        v = self.window["-INPUT2-"].get()
        if self.values.get("-TIMER_SET-") == "-FIRST_SET-":
            # 初回起動ならスキップ
            self.values["-TIMER_SET-"] = ""
            logger.info("Auto-reload -FIRST_SET- ... skip first auto-reload cycle.")

            # 現在タイマー待機中のものがあればキャンセルする
            if self.timer_thread:
                self.timer_thread.cancel()
                self.timer_thread = None
        elif re.search(pattern, v):
            # 既に更新中ならスキップ
            self.values["-TIMER_SET-"] = ""
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
        self.timer_thread = threading.Timer(s_interval, self.run)
        # デーモンスレッドはデーモンスレッド以外のスレッドが動いていない場合に自動的に終了される
        self.timer_thread.setDaemon(True)
        self.timer_thread.start()

        # 次回起動時間の予測をログに出力
        dst_df = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now() + timedelta(minutes=interval)
        logger.info(f"Next auto-reload cycle start at {dst.strftime(dst_df)}.")
        return


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
