import re
from datetime import datetime, timedelta
from logging import INFO, getLogger

from PySide6.QtCore import QTimer, Slot
from PySide6.QtWidgets import QApplication, QWidget

from nnmm.process.base import ProcessBase
from nnmm.process.config import ConfigBase
from nnmm.process.update_mylist import partial
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class Timer(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.timer: QTimer | None = None
        self.first_set = True

    def _timer_cancel(self) -> None:
        """現在タイマー待機中のものがあればキャンセルする"""
        if self.timer and self.timer.remainingTime() > 0:
            self.timer.stop()
            self.timer = None

    def create_component(self) -> QWidget:
        """タイマー関連はコンポーネントは作成しない"""
        return None

    @Slot()
    def callback(self) -> Result:
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
            logger.error("Timer Init failed, interval auto_reload is invalid.")
            return Result.failed

        # 更新処理スキップ判定
        pattern = r"^.*(取得中|更新中).*$"
        v = self.get_bottom_textbox().to_str()
        if self.first_set:
            self.first_set = False
            # 初回起動ならスキップ
            logger.info("Auto-reload first set, skip first auto-reload cycle.")
        elif re.search(pattern, v):
            # 既に更新処理中ならスキップ
            logger.info("Update running now ... skip this auto-reload cycle.")
        else:
            # 更新処理起動
            logger.info("Auto-reload start.")
            # 一部更新ボタンが押された場合の処理を起動する
            partial.Partial(ProcessInfo.create("インターバル更新", self.window)).callback()

        # 現在タイマー待機中のものがあればキャンセルする
        self._timer_cancel()

        # 次回起動タイマーをセット
        s_interval = interval * 60 * 1000  # [min] -> [msec]
        self.timer = QTimer(singleShot=True)
        self.timer.timeout.connect(lambda: self.callback())
        self.timer.start(s_interval)

        # 次回起動時間の予測をログに出力
        dst_df = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now() + timedelta(minutes=interval)
        logger.info(f"Next auto-reload cycle start at {dst.strftime(dst_df)}.")
        return Result.success


if __name__ == "__main__":
    import sys

    import qdarktheme
    from PySide6.QtWidgets import QApplication

    from nnmm.main_window import MainWindow

    app = QApplication()
    qdarktheme.setup_theme()
    window_main = MainWindow()
    window_main.show()
    sys.exit(app.exec())
