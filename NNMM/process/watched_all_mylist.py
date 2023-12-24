from logging import INFO, getLogger

from NNMM.process.base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.process.value_objects.table_row import Status
from NNMM.util import Result

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
        mylist_url = self.get_upper_textbox().to_str()
        if mylist_url == "":
            # 現在表示しているテーブルの表示をすべて視聴済にする
            def_data = self.get_all_table_row()
            for i, record in enumerate(def_data):
                def_data[i] = def_data[i].replace_from_typed_value(status=Status.watched)
            self.window["-TABLE-"].update(values=def_data.to_table_data())

        self.update_mylist_pane()
        self.update_table_pane(mylist_url)

        logger.info(f"WatchedAllMylist success.")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
