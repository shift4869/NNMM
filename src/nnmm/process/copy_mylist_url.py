from logging import INFO, getLogger

import pyperclip
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QWidget

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class CopyMylistUrl(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        """QListWidgetの右クリックメニューから起動するためコンポーネントは作成しない"""
        return None

    @Slot()
    def callback(self) -> Result:
        """選択されたマイリストのURLをクリップボードにコピーする

        "マイリストURLをクリップボードにコピー::-MR-"
        """
        logger.info(f"CopyMylistUrl start.")

        # マイリストが選択されていなかったら何もしない
        selected_mylist_row = self.get_selected_mylist_row()
        if not selected_mylist_row:
            logger.info("CopyMylistUrl failed, no mylist selected.")
            return Result.failed

        # マイリストURLを取得
        showname = selected_mylist_row.without_new_mark_name()
        record = self.mylist_db.select_from_showname(showname)[0]
        mylist_url = record.get("url")

        # クリップボードに保存
        pyperclip.copy(mylist_url)
        self.set_bottom_textbox("マイリストURLコピー成功！")

        logger.info(f"CopyMylistUrl done.")
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
