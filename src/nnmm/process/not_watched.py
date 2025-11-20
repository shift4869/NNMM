from logging import INFO, getLogger

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QTableWidget, QWidget

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row import Status
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from nnmm.process.value_objects.table_row_list import TableRowList
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class NotWatched(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        """QTableWidgetの右クリックメニューから起動するためコンポーネントは作成しない"""
        return None

    @Slot()
    def callback(self) -> Result:
        """動画の状況ステータスを"未視聴"に設定する

        Notes:
            "未視聴にする::-TR-"
            テーブル右クリックで「未視聴にする」が選択された場合

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("NotWatched start.")

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
            res = self.mylist_info_db.update_status(video_id, mylist_url, "未視聴")
            if res == 0:
                logger.info(f'{video_id} ({i + 1}/{all_num}) -> marked "non-watched".')
            else:
                logger.info(f"{video_id} ({i + 1}/{all_num}) -> failed.")

            # テーブル更新
            updated_row = selected_row.replace_from_typed_value(status=Status.not_watched)
            table_row_list[row_index] = updated_row

            # 未視聴になったことでマイリストの新着表示を表示する
            # 未視聴にしたので必ず新着あり扱いになる
            # マイリストDB新着フラグ更新
            self.mylist_db.update_include_flag(mylist_url, True)

        # テーブル更新を反映させる
        self.set_all_table_row(table_row_list)

        # テーブルの表示を更新する
        mylist_url = self.get_upper_textbox().to_str()
        table_widget: QTableWidget = self.window.table_widget
        table_widget.selectRow(row_index)

        # マイリスト画面表示更新
        self.update_mylist_pane()

        logger.info("NotWatched done.")
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
