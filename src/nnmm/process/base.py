import logging.config
import time
from abc import ABC, abstractmethod

from PySide6.QtCore import QDateTime, QDir, QLibraryInfo, QModelIndex, QSysInfo, Qt, QTimer, Slot, qVersion
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog, QHeaderView, QLineEdit, QListWidget, QListWidgetItem, QTableWidget
from PySide6.QtWidgets import QTableWidgetItem, QVBoxLayout, QWidget

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.value_objects.mylist_row import MylistRow, SelectedMylistRow
from nnmm.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from nnmm.process.value_objects.mylist_row_list import MylistRowList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row import TableRowTuple
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from nnmm.process.value_objects.table_row_list import SelectedTableRowList, TableRowList
from nnmm.process.value_objects.textbox_bottom import BottomTextbox
from nnmm.process.value_objects.textbox_upper import UpperTextbox
from nnmm.util import CustomLogger, Result

logging.setLoggerClass(CustomLogger)


class ProcessBase(ABC):
    process_info: ProcessInfo
    name: str
    window: QDialog
    mylist_db: MylistDBController
    mylist_info_db: MylistInfoDBController

    def __init__(self, process_info: ProcessInfo) -> None:
        if not isinstance(process_info, ProcessInfo):
            raise ValueError("process_info must be ProcessInfo.")
        self.process_info = process_info
        self.name = process_info.name
        self.window = process_info.window
        self.mylist_db = process_info.mylist_db
        self.mylist_info_db = process_info.mylist_info_db

    @abstractmethod
    def create_component(self) -> QWidget:
        raise NotImplementedError

    @abstractmethod
    @Slot()
    def callback(self) -> Result:
        raise NotImplementedError

    def get_selected_mylist_row_index(self) -> SelectedMylistRowIndex | None:
        """self.window["-LIST-"].get_indexes()[0] から SelectedMylistRowIndex を取得

        マイリストの選択は単数想定

        Returns:
            SelectedMylistRowIndex | None: 選択マイリストインデックス
        """
        if not hasattr(self.window, "list_widget"):
            return None
        try:
            list_widget: QListWidget = self.window.list_widget
            selected_index_list = list_widget.selectedIndexes()
            if not selected_index_list:
                return SelectedMylistRowIndex(0)
            selected_index = selected_index_list[0].row()
            return SelectedMylistRowIndex(int(selected_index))
        except Exception:
            return None

    def get_selected_mylist_row(self) -> SelectedMylistRow | None:
        """list_widget から SelectedMylistRow を取得

        マイリストの選択は単数想定

        Returns:
            SelectedMylistRow | None: 選択マイリスト行
        """
        try:
            list_widget: QListWidget = self.window.list_widget
            selected_mylist_row: list[str] = [item.text() for item in list_widget.selectedItems()]
            if not selected_mylist_row:
                return None
            return SelectedMylistRow.create(selected_mylist_row[0])
        except Exception:
            return None

    def get_all_mylist_row(self) -> MylistRowList | None:
        """list_widget から MylistRowList を取得

        Returns:
            MylistRowList | None: すべてのマイリストを含むリスト
        """
        try:
            return MylistRowList.create(self.window["-LIST-"].Values)
        except Exception:
            return None

    def get_selected_table_row_index_list(self) -> SelectedTableRowIndexList | None:
        """table_widget から SelectedTableRowIndexList を取得

        テーブルの選択は複数想定

        Returns:
            SelectedTableRowIndexList | None: 選択テーブル行インデックスリスト
        """
        try:
            table_widget: QTableWidget = self.window.table_widget
            # 選択されている各セルがそれぞれ行番号を返すので、列数分重複する
            # 重複を排除するために一度setにいれてからlistとして取り出す
            row_index_list = list(set([index.row() for index in table_widget.selectedIndexes()]))
            return SelectedTableRowIndexList.create(row_index_list)
        except Exception:
            return None

    def get_selected_table_row_list(self) -> SelectedTableRowList | None:
        """選択されているテーブル行を取得する

        Returns:
            SelectedTableRowList | None: 選択されているテーブル行
        """
        try:
            selected_table_row_list = []

            table_widget: QTableWidget = self.window.table_widget
            column_count = table_widget.columnCount()

            # すべてのセルの値がまとめて1次元配列として返されるので
            # 列数ごとにスライスして2次元配列にする
            selected_items = [items.text() for items in table_widget.selectedItems()]
            selected_row_num = len(selected_items) // column_count
            for i in range(selected_row_num):
                selected_table_row = list(selected_items[i * column_count : (i + 1) * column_count])
                selected_table_row_list.append(selected_table_row)

            return SelectedTableRowList.create(selected_table_row_list)
        except Exception:
            return None

    def get_all_table_row(self) -> TableRowList | None:
        """table_widget から TableRowList を取得

        Returns:
            TableRowList | None: すべてのテーブル行を含むリスト
        """
        try:
            table_widget: QTableWidget = self.window.table_widget
            row_list = []
            n, m = table_widget.rowCount(), table_widget.columnCount()
            for i in range(n):
                row = []
                for j in range(m):
                    row.append(table_widget.item(i, j).text())
                row_list.append(row)
            return TableRowList.create(row_list)
        except Exception:
            return None

    def set_all_table_row(self, table_row_list: TableRowList) -> TableRowList | None:
        """table_widget に TableRowList を設定する

        Returns:
            TableRowList | None: 設定されたテーブル行のリスト
        """
        table_cols_name = [
            "No.",
            "動画ID",
            "動画名",
            "投稿者",
            "状況",
            "投稿日時",
            "登録日時",
            "動画URL",
            "所属マイリストURL",
        ]
        try:
            table_widget: QTableWidget = self.window.table_widget
            table_widget.clearContents()
            table_widget.setRowCount(0)
            table_widget.setColumnCount(0)

            n = len(table_row_list)
            if n == 0:
                return None
            m = len(table_row_list[0].to_row())
            if m == 0:
                return None
            table_widget.setRowCount(n)
            table_widget.setColumnCount(m)
            table_widget.setHorizontalHeaderLabels(table_cols_name)
            table_widget.verticalHeader().hide()

            # ヘッダーの列幅調整を確実に反映させるために少し遅延させる
            time.sleep(0.1)

            cols_width = [30, 100, 350, 100, 60, 120, 120, 30, 30]
            for i, section_size in enumerate(cols_width):
                table_widget.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                table_widget.horizontalHeader().resizeSection(i, section_size)

            for i, table_row in enumerate(table_row_list):
                row = table_row.to_row()
                for j, text in enumerate(row):
                    table_widget.setItem(i, j, QTableWidgetItem(text))

            table_widget.update()

            return table_row_list
        except Exception:
            return None

    def get_upper_textbox(self) -> UpperTextbox:
        if not hasattr(self.window, "tbox_mylist_url"):
            return None
        try:
            tbox_mylist_url: QLineEdit = self.window.tbox_mylist_url
            return UpperTextbox(tbox_mylist_url.text())
        except Exception:
            return None

    def set_upper_textbox(self, text: str, is_repaint: bool = True) -> UpperTextbox:
        if not hasattr(self.window, "tbox_mylist_url"):
            return None
        try:
            tbox_mylist_url: QLineEdit = self.window.tbox_mylist_url
            tbox_mylist_url.setText(text)
            if is_repaint:
                tbox_mylist_url.repaint()
            else:
                tbox_mylist_url.update()
            return UpperTextbox(text)
        except Exception:
            return None

    def get_bottom_textbox(self) -> BottomTextbox:
        if not hasattr(self.window, "oneline_log"):
            return None
        try:
            oneline_log: QLineEdit = self.window.oneline_log
            return BottomTextbox(oneline_log.text())
        except Exception:
            return None

    def set_bottom_textbox(self, text: str, is_repaint: bool = True) -> BottomTextbox:
        if not hasattr(self.window, "oneline_log"):
            return None
        try:
            oneline_log: QLineEdit = self.window.oneline_log
            oneline_log.setText(text)
            if is_repaint:
                oneline_log.repaint()
            else:
                oneline_log.update()
            return BottomTextbox(text)
        except Exception:
            return None

    def update_mylist_pane(self) -> Result:
        """マイリストペインの表示を更新する

        Returns:
            Result: 成功時success
        """
        # 現在選択中のマイリストがある場合そのindexを保存
        index = 0
        selected_index = self.get_selected_mylist_row_index()
        if selected_index:
            index = int(selected_index)

        # マイリスト画面表示更新
        # NEW_MARK = "*:"
        m_list = self.mylist_db.select()
        include_new_index_list = []
        for i, m in enumerate(m_list):
            if m["is_include_new"]:
                mylist_row = MylistRow.create(m["showname"])
                m["showname"] = mylist_row.with_new_mark_name()
                include_new_index_list.append(i)
        list_data = [m["showname"] for m in m_list]

        list_widget: QListWidget = self.window.list_widget
        list_widget.clear()
        for i, data in enumerate(list_data):
            if i not in include_new_index_list:
                list_widget.addItem(data)
            else:
                # 新着マイリストの背景色とテキスト色を変更する
                item = QListWidgetItem(data)
                item.setBackground(QColor.fromRgb(233, 91, 107))
                list_widget.addItem(item)

        # indexをセットしてスクロール
        list_widget.setCurrentRow(index)
        return Result.success

    def update_table_pane(self, mylist_url: str = "") -> Result:
        """テーブルリストペインの表示を更新する

        Args:
            mylist_url (str): 表示対象マイリスト,
                              空白時は右上のテキストボックスから取得
                              右上のテキストボックスも空なら現在表示中のテーブルをリフレッシュする

        Returns:
            Result: 成功時success
        """
        # 表示対象マイリストが空白の場合は
        # 右上のテキストボックスに表示されている現在のマイリストURLを設定する
        if mylist_url == "":
            mylist_url = self.get_upper_textbox().to_str()

        index = 0
        def_data: TableRowList = []
        if mylist_url == "":
            # 引数も右上のテキストボックスも空白の場合
            # 現在表示しているテーブルの表示をリフレッシュする処理のみ行う
            def_data = self.get_all_table_row()

            # 現在選択中のマイリストがある場合そのindexを保存
            selected_index = self.get_selected_mylist_row_index()
            if selected_index:
                index = int(selected_index)
        else:
            # 現在のマイリストURLからlistboxのindexを求める
            m_list = self.mylist_db.select()
            mylist_url_list = [m["url"] for m in m_list]
            for i, url in enumerate(mylist_url_list):
                if mylist_url == url:
                    index = i
                    break

            # 現在のマイリストURLからテーブル情報を求める
            records = self.mylist_info_db.select_from_mylist_url(mylist_url)
            table_row_list = []
            for i, r in enumerate(records):
                record = TableRowTuple._make([i + 1] + list(r.values())[1:-1])
                table_row = [
                    record.row_index,
                    record.video_id,
                    record.title,
                    record.username,
                    record.status,
                    record.uploaded_at,
                    record.registered_at,
                    record.video_url,
                    record.mylist_url,
                ]
                table_row_list.append(table_row)
            def_data = TableRowList.create(table_row_list)

        # 画面更新
        # LIST は空のときにindexを設定しても問題ないが、
        # TABLE は空のときにselect_rowsしてはいけない
        # self.window["-LIST-"].update(set_to_index=index)
        list_widget: QListWidget = self.window.list_widget
        list_widget.setCurrentRow(index)

        table_widget: QTableWidget = self.window.table_widget
        self.set_all_table_row(def_data)
        # if len(def_data) > 0:
        #     table_widget.selectRow(0)
        # 1行目は背景色がリセットされないので個別に指定してdefaultの色で上書き
        # self.window["-TABLE-"].update(row_colors=[(0, "", "")])
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
