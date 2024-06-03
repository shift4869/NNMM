from logging import INFO, getLogger

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class WatchedMylist(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリストに含まれる動画情報についてすべて"視聴済"にする

        Notes:
            "視聴済にする（選択）::-MR-"
            マイリスト右クリックで「視聴済にする（選択）」が選択された場合
        """
        logger.info(f"WatchedAllMylist start.")

        # マイリストが選択されていない場合は何もしない
        selected_mylist_row = self.get_selected_mylist_row()
        if not selected_mylist_row:
            logger.error("WatchedMylist failed, no mylist selected.")
            return Result.failed

        showname = selected_mylist_row.without_new_mark_name()
        record = self.mylist_db.select_from_showname(showname)[0]
        mylist_url = record.get("url")

        # マイリストの新着フラグがFalseなら何もしない
        if not record.get("is_include_new"):
            logger.error(f'{mylist_url} -> selected mylist is already "watched".')
            return Result.failed

        # マイリスト情報内の視聴済フラグを更新
        self.mylist_info_db.update_status_in_mylist(mylist_url, "")
        # マイリストの新着フラグを更新
        self.mylist_db.update_include_flag(mylist_url, False)

        logger.info(f'{mylist_url} -> all include videos status are marked "watched".')

        self.update_mylist_pane()
        self.update_table_pane("")

        logger.info(f"WatchedMylist success.")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
