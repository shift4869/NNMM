from logging import INFO, getLogger

from NNMM.process.base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, update_mylist_pane, update_table_pane

logger = getLogger(__name__)
logger.setLevel(INFO)


class WatchedAllMylist(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """すべてのマイリストに含まれる動画情報についてすべて"視聴済"にする

        Notes:
            "視聴済にする（全て）::-MR-"
            マイリスト右クリックで「視聴済にする（全て）」が選択された場合
        """
        logger.info(f"WatchedAllMylist start.")

        m_list = self.mylist_db.select()
        # マイリストの新着フラグがTrueのもののみ対象とする
        records = [m for m in m_list if m["is_include_new"]]

        all_num = len(records)
        for i, record in enumerate(records):
            mylist_url = record.get("url")

            # マイリスト情報内の視聴済フラグを更新
            self.mylist_info_db.update_status_in_mylist(mylist_url, "")
            # マイリストの新着フラグを更新
            self.mylist_db.update_include_flag(mylist_url, False)

            logger.info(f'{mylist_url} -> all include videos status are marked "watched" ... ({i + 1}/{all_num}).')

        # 右上のテキストボックスからマイリストURLを取得
        mylist_url = self.window["-INPUT1-"].get()
        if mylist_url == "":
            # 現在表示しているテーブルの表示をすべて視聴済にする
            def_data = self.window["-TABLE-"].Values  # 現在のtableの全リスト

            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
            STATUS_INDEX = 4
            for i, record in enumerate(def_data):
                def_data[i][STATUS_INDEX] = ""
            self.window["-TABLE-"].update(values=def_data)

        update_mylist_pane(self.window, self.mylist_db)
        update_table_pane(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info(f"WatchedAllMylist success.")
        return Result.success
   

if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
