from logging import INFO, getLogger

from PySide6.QtCore import QDateTime, QDir, QLibraryInfo, QSysInfo, Qt, QTimer, Slot, qVersion
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton
from PySide6.QtWidgets import QTableWidget, QVBoxLayout, QWidget

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row_list import TableRowList
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class ShowMylistInfoAll(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        """動画情報レコード表示はListWidgetダブルクリックから起動"""
        return None

    @Slot()
    def callback(self) -> Result:
        """すべてのマイリストを横断的に探索し、含まれる動画情報レコードを100件まで表示する

        Notes:
            "全動画表示::-MR-"
            マイリスト右クリックで「全動画表示」が選択された場合
            動画IDの数値で判定し、降順に動画情報レコードを100件まで表示する

        Todo:
            最新のレコードを表示するためのソート順を考える
                動画ID→予約投稿を考えると投稿日時順とは必ずしも一致しない
                投稿日時→投コメ修正などの更新でも日時が更新されてしまう
            初回格納時の投稿日時のみ保持するようにし、
            それ以降投稿日時が上書きされないようにした上で投稿日時順ソートが有効か
        """
        logger.info("ShowMylistInfoAll start.")

        # 現在選択中のマイリストがある場合そのindexを保存
        selected_mylist_row_index = self.get_selected_mylist_row_index()
        index = 0
        if selected_mylist_row_index:
            index = int(selected_mylist_row_index)

        # 全動画情報を取得
        NUM = 100
        video_info_list = self.mylist_info_db.select()  # DB内にある全ての動画情報を取得
        records = sorted(video_info_list, key=lambda x: int(x["video_id"][2:]), reverse=True)[
            0:NUM
        ]  # 最大100要素までのスライス
        table_row_list = []
        for i, r in enumerate(records):
            a = [
                i + 1,
                r["video_id"],
                r["title"],
                r["username"],
                r["status"],
                r["uploaded_at"],
                r["registered_at"],
                r["video_url"],
                r["mylist_url"],
            ]
            table_row_list.append(a)
        def_data = TableRowList.create(table_row_list)

        # 右上のマイリストURLは空白にする
        self.set_upper_textbox("")

        # テーブル更新
        # update_table_paneはリフレッシュには使えるが初回は別に設定が必要なため使用できない
        list_widget: QListWidget = self.window.list_widget
        list_widget.setCurrentRow(index)

        table_widget: QTableWidget = self.window.table_widget
        self.set_all_table_row(def_data)
        if len(def_data) > 0:
            table_widget.selectRow(0)
        # 1行目は背景色がリセットされないので個別に指定してdefaultの色で上書き
        # self.window["-TABLE-"].update(row_colors=[(0, "", "")])

        logger.info("ShowMylistInfoAll success.")
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
