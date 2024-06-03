from logging import INFO, getLogger

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row import Status
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from nnmm.process.value_objects.table_row_list import TableRowList
from nnmm.util import Result, is_mylist_include_new_video

logger = getLogger(__name__)
logger.setLevel(INFO)


class Watched(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """動画の状況ステータスを""(視聴済)に設定する

        Notes:
            "視聴済にする::-TR-"
            テーブル右クリックで「視聴済にする」が選択された場合

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("Watched start.")

        # 行が選択されていないなら何もしない
        selected_table_row_index_list: SelectedTableRowIndexList = self.get_selected_table_row_index_list()
        if not selected_table_row_index_list:
            logger.error("NotWatched failed, no record selected.")
            return Result.failed

        # 現在のtableの全リスト
        table_row_list: TableRowList = self.get_all_table_row()

        # 選択された行（複数可）についてすべて処理する
        all_num = len(selected_table_row_index_list)
        row_index = 0
        for i, table_row_index in enumerate(selected_table_row_index_list):
            row_index = int(table_row_index)

            # マイリスト情報ステータスDB更新
            selected_row = table_row_list[row_index]
            video_id = selected_row.video_id.id
            mylist_url = selected_row.mylist_url.non_query_url
            res = self.mylist_info_db.update_status(video_id, mylist_url, "")
            if res == 0:
                logger.info(f'{video_id} ({i + 1}/{all_num}) -> marked "watched".')
            else:
                logger.info(f"{video_id} ({i + 1}/{all_num}) -> failed.")

            # テーブル更新
            updated_row = selected_row.replace_from_typed_value(status=Status.watched)
            table_row_list[row_index] = updated_row

            # 視聴済になったことでマイリストの新着表示を消すかどうか判定する
            m_list = self.mylist_info_db.select_from_mylist_url(mylist_url)
            m_list = [list(m.values()) for m in m_list]
            if not is_mylist_include_new_video(m_list):
                # マイリストDB新着フラグ更新
                self.mylist_db.update_include_flag(mylist_url, False)

        # テーブル更新を反映させる
        self.window["-TABLE-"].update(values=table_row_list.to_table_data())

        # テーブルの表示を更新する
        mylist_url = self.get_upper_textbox().to_str()
        self.update_table_pane(mylist_url)
        self.window["-TABLE-"].update(select_rows=[row_index])

        # マイリスト画面表示更新
        self.update_mylist_pane()

        logger.info("Watched success.")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
