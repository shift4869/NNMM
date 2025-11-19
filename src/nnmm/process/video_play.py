import subprocess
from logging import INFO, getLogger
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget

from nnmm.process import config as process_config
from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row import Status
from nnmm.process.watched import Watched
from nnmm.util import Result, popup

logger = getLogger(__name__)
logger.setLevel(INFO)


class VideoPlay(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        """QTableWidgetの右クリックメニューから起動するためコンポーネントは作成しない"""
        return None

    @Slot()
    def callback(self) -> Result:
        """選択された動画をブラウザで開く

        Notes:
            "ブラウザで開く::-TR-"
            テーブル右クリックで「再生」が選択された場合
        """
        logger.info(f"VideoPlay start.")

        # テーブルの行が選択されていなかったら何もしない
        selected_table_row_index_list = self.get_selected_table_row_index_list()
        if not selected_table_row_index_list:
            logger.info("VideoPlay failed, Table row is not selected.")
            return Result.failed

        # 選択されたテーブル行
        selected_table_row_list = self.get_selected_table_row_list()
        selected_table_row = selected_table_row_list[0]

        # 動画URLを取得
        records = self.mylist_info_db.select_from_video_id(selected_table_row.video_id.id)
        record = records[0]
        video_url = record.get("video_url")

        config = process_config.ConfigBase.get_config()
        cmd = config["general"].get("browser_path", "")
        if cmd != "" and Path(cmd).is_file():
            # ブラウザに動画urlを渡す
            result = subprocess.run([cmd, video_url])
            # logger.info(sg.execute_get_results(sp)[0])
            logger.info(f"{cmd} -> valid browser path.")
            logger.info(f"{video_url} -> video page opened with browser.")
        else:
            # ブラウザパスが不正
            popup("ブラウザパスが不正です。設定タブから設定してください。")
            logger.info(f"{cmd} -> invalid browser path.")
            logger.info(f"{video_url} -> video page open failed.")
            return Result.failed

        # 状況を更新
        if selected_table_row.status != Status.watched:
            # 視聴済にする
            pb = Watched(self.process_info)
            pb.callback()

        logger.info(f"VideoPlay success.")
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
