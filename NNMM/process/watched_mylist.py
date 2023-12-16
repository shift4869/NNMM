from logging import INFO, getLogger

from NNMM.process.base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, update_mylist_pane, update_table_pane

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
        if not self.values["-LIST-"]:
            logger.error("WatchedMylist failed, no mylist selected.")
            return Result.failed

        v = self.values["-LIST-"][0]  # 選択値

        NEW_MARK = "*:"
        if v[:2] == NEW_MARK:
            v = v[2:]
        record = self.mylist_db.select_from_showname(v)[0]
        mylist_url = record.get("url")

        # マイリストの新着フラグがFalseなら何もしない
        if not record.get("is_include_new"):
            logger.error('WatchedMylist success, selected mylist is already "watched".')
            return Result.failed

        # マイリスト情報内の視聴済フラグを更新
        self.mylist_info_db.update_status_in_mylist(mylist_url, "")
        # マイリストの新着フラグを更新
        self.mylist_db.update_include_flag(mylist_url, False)

        logger.info(f'{mylist_url} -> all include videos status are marked "watched".')

        update_mylist_pane(self.window, self.mylist_db)
        update_table_pane(self.window, self.mylist_db, self.mylist_info_db, "")

        logger.info(f"WatchedMylist success.")
        return Result.success
    

if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
