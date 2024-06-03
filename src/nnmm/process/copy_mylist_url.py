from logging import INFO, getLogger

import pyperclip

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class CopyMylistUrl(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
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
        self.window["-INPUT2-"].update(value=f"マイリストURLコピー成功！")

        logger.info(f"CopyMylistUrl success.")
        return Result.success


if __name__ == "__main__":
    from nnmm import main_window

    mw = main_window.MainWindow()
    mw.run()
