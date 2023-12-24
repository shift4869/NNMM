from logging import INFO, getLogger

from NNMM.process.base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class MoveUp(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリストの並び順を一つ上に移動させる

        Notes:
            "上に移動::-MR-"
            マイリスト右クリックで「上に移動」が選択された場合
        """
        selected_mylist_row = self.get_selected_mylist_row()
        if not selected_mylist_row:
            logger.error("MoveUp failed, no mylist selected.")
            return Result.failed

        src_index = 0
        selected_mylist_row_index = self.get_selected_mylist_row_index()
        if selected_mylist_row_index:
            src_index = int(selected_mylist_row_index)
        src_v = selected_mylist_row.without_new_mark_name()
        list_data = self.get_all_mylist_row()

        if src_index == 0:
            logger.info(f"{src_v} -> index is 0 , can't move up.")
            return Result.failed

        src_record = self.mylist_db.select_from_showname(src_v)[0]

        dst_index = src_index - 1
        dst_v = list_data[dst_index].without_new_mark_name()
        dst_record = self.mylist_db.select_from_showname(dst_v)[0]

        self.mylist_db.swap_id(src_record["id"], dst_record["id"])

        self.update_mylist_pane()
        self.window["-LIST-"].update(set_to_index=dst_index)

        logger.info(f"{src_v} -> index move up from {src_index} to {dst_index}.")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
