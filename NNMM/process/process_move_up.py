from logging import INFO, getLogger

from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, update_mylist_pane

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessMoveUp(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリストの並び順を一つ上に移動させる

        Notes:
            "上に移動::-MR-"
            マイリスト右クリックで「上に移動」が選択された場合
        """
        if not self.values["-LIST-"]:
            logger.error("MoveUp failed, no mylist selected.")
            return Result.failed

        src_index = 0
        if self.window["-LIST-"].get_indexes():
            src_index = self.window["-LIST-"].get_indexes()[0]
        src_v = self.values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値
        list_data = self.window["-LIST-"].Values  # 現在のtableの全リスト

        if src_index == 0:
            logger.info(f"{src_v} -> index is 0 , can't move up.")
            return Result.failed

        if src_v[:2] == "*:":
            src_v = src_v[2:]
        src_record = self.mylist_db.select_from_showname(src_v)[0]

        dst_index = src_index - 1
        dst_v = list_data[dst_index]
        if dst_v[:2] == "*:":
            dst_v = dst_v[2:]
        dst_record = self.mylist_db.select_from_showname(dst_v)[0]

        self.mylist_db.swap_id(src_record["id"], dst_record["id"])

        # テーブル更新
        update_mylist_pane(self.window, self.mylist_db)
        self.window["-LIST-"].update(set_to_index=dst_index)

        logger.info(f"{src_v} -> index move up from {src_index} to {dst_index}.")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
