from logging import INFO, getLogger

from NNMM.gui_function import update_mylist_pane, update_table_pane
from NNMM.process.process_base import ProcessBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessWatchedMylist(ProcessBase):

    def __init__(self):
        super().__init__(True, True, "視聴済にする（選択）")

    def run(self, mw):
        """マイリストに含まれる動画情報についてすべて"視聴済"にする

        Notes:
            "視聴済にする（選択）::-MR-"
            マイリスト右クリックで「視聴済にする（選択）」が選択された場合

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, すでに視聴済なら1, エラー時-1
        """
        logger.info(f"WatchedAllMylist start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("WatchedMylist failed, argument error.")
            return -1

        # マイリストが選択されていない場合は何もしない
        if not self.values["-LIST-"]:
            logger.error("WatchedMylist failed, no mylist selected.")
            return -1

        v = self.values["-LIST-"][0]  # 選択値

        NEW_MARK = "*:"
        if v[:2] == NEW_MARK:
            v = v[2:]
        record = self.mylist_db.select_from_showname(v)[0]
        mylist_url = record.get("url")

        # マイリストの新着フラグがFalseなら何もしない
        if not record.get("is_include_new"):
            logger.error('WatchedMylist success, selected mylist is already "watched".')
            return 1

        # マイリスト情報内の視聴済フラグを更新
        self.mylist_info_db.update_status_in_mylist(mylist_url, "")
        # マイリストの新着フラグを更新
        self.mylist_db.update_include_flag(mylist_url, False)

        logger.info(f'{mylist_url} -> all include videos status are marked "watched".')

        # マイリスト画面表示更新
        update_mylist_pane(self.window, self.mylist_db)
        # テーブル画面表示更新
        update_table_pane(self.window, self.mylist_db, self.mylist_info_db)

        logger.info(f"WatchedMylist success.")
        return 0
    

if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()()
    mw.run()
