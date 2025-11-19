from logging import INFO, getLogger

import pyperclip
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QTableWidget, QWidget

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class CopyVideoUrl(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        """QTableWidgetの右クリックメニューから起動するためコンポーネントは作成しない"""
        return None

    @Slot()
    def callback(self) -> Result:
        """選択された動画のURLをクリップボードにコピーする

        "動画URLをクリップボードにコピー::-TR-"
        """
        logger.info(f"CopyVideoUrl start.")

        # テーブルの行が選択されていなかったら何もしない
        selected_table_row_index_list = self.get_selected_table_row_index_list()
        if not selected_table_row_index_list:
            logger.info("CopyVideoUrl failed, Table row is not selected.")
            return Result.failed

        # 選択されたテーブル行
        selected_table_row_list = self.get_selected_table_row_list()
        selected_table_row = selected_table_row_list[0]

        # 動画URLを取得
        video_id = selected_table_row.video_id.id
        record = self.mylist_info_db.select_from_video_id(video_id)[0]
        video_url = record.get("video_url")

        # クリップボードに保存
        pyperclip.copy(video_url)
        self.set_bottom_textbox("動画URLコピー成功！")

        logger.info(f"CopyVideoUrl done.")
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
