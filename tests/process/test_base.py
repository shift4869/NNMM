import re
import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QDialog, QListWidget, QWidget

from nnmm.main_window import MainWindow
from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.base import NEW_MYLIST_COLOR, ProcessBase
from nnmm.process.value_objects.mylist_row import MylistRow, SelectedMylistRow
from nnmm.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from nnmm.process.value_objects.mylist_row_list import MylistRowList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row import TableRowTuple
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from nnmm.process.value_objects.table_row_list import SelectedTableRowList, TableRowList
from nnmm.process.value_objects.textbox_bottom import BottomTextbox
from nnmm.process.value_objects.textbox_upper import UpperTextbox
from nnmm.util import Result


# テスト用の具象クラス
class ConcreteProcess(ProcessBase):
    def create_component(self):
        return None

    def callback(self):
        return Result.success


class TestProcessBase(unittest.TestCase):
    def setUp(self):
        # logger 出力抑止
        # self.enterContext(patch("nnmm.process.base.logger.info"))

        # ProcessInfo のモック準備
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock()
        self.process_info.mylist_info_db = MagicMock()

        # インスタンス作成
        self.instance = ConcreteProcess(self.process_info)

    def _make_mylist_db(self) -> list[dict]:
        NUM = 5
        res = []
        col = [
            "id",
            "username",
            "mylistname",
            "type",
            "showname",
            "url",
            "created_at",
            "updated_at",
            "checked_at",
            "check_interval",
            "is_include_new",
        ]
        rows = [
            [
                i,
                f"投稿者{i + 1}",
                "投稿動画",
                "uploaded",
                f"投稿者{i + 1}さんの投稿動画",
                f"https://www.nicovideo.jp/user/1000000{i + 1}/video",
                "2025-11-01 02:30:00",
                "2025-11-01 02:30:00",
                "2025-11-01 02:30:00",
                "15分",
                False,
            ]
            for i in range(NUM)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_mylist_info_db(self, mylist_url) -> list[list[dict]]:
        NUM = 5
        res = []

        m = -1
        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        if re.search(pattern, mylist_url):
            m = int(re.search(pattern, mylist_url)[1])
        if m == -1:
            return []

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
            "作成日時",
        ]
        table_cols = [
            "no",
            "video_id",
            "title",
            "username",
            "status",
            "uploaded_at",
            "registered_at",
            "video_url",
            "mylist_url",
            "created_at",
        ]
        table_rows = [
            [
                i,
                f"sm{m}000000{i + 1}",
                f"動画タイトル{m}_{i + 1}",
                f"投稿者{m}",
                "",
                "2025-11-01 02:30:00",
                "2025-11-02 02:30:00",
                f"https://www.nicovideo.jp/watch/sm{m}000000{i + 1}",
                f"https://www.nicovideo.jp/user/1000000{m}/video",
                "2025-11-03 02:30:00",
            ]
            for i in range(NUM)
        ]

        for rows in table_rows:
            d = {}
            for r, c in zip(rows, table_cols):
                d[c] = r
            res.append(d)
        return res

    def _make_table_row(self) -> tuple[list[str], int, int]:
        NUM = 5
        m = 1
        res = []
        table_row_list = [
            [
                i + 1,  # 行番号は1ベース
                f"sm{m}000000{i + 1}",
                f"動画タイトル{m}_{i + 1}",
                f"投稿者{m}",
                "",
                "2025-11-01 02:30:00",
                "2025-11-02 02:30:00",
                f"https://www.nicovideo.jp/watch/sm{m}000000{i + 1}",
                f"https://www.nicovideo.jp/user/1000000{m}/video",
                # "2025-11-03 02:30:00",
            ]
            for i in range(NUM)
        ]

        def make_text_mock(text: str) -> MagicMock:
            m = MagicMock()
            m.text.return_value = text
            return m

        for table_row in table_row_list:
            for cell in table_row:
                res.append(make_text_mock(str(cell)))
        row = len(table_row_list)
        col = len(table_row_list[0])
        return res, row, col

    def test_init(self):
        process_name = "-TEST_PROCESS-"
        instance = ConcreteProcess(self.process_info)

        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(process_name, instance.name)
        self.assertEqual(self.process_info.window, instance.window)
        self.assertEqual(self.process_info.mylist_db, instance.mylist_db)
        self.assertEqual(self.process_info.mylist_info_db, instance.mylist_info_db)

        with self.assertRaises(ValueError):
            instance = ConcreteProcess("invalid_process_info")

    def test_create_component(self):
        instance = ConcreteProcess(self.process_info)
        actual = instance.create_component()
        self.assertIsNone(actual)

    def test_callback(self):
        instance = ConcreteProcess(self.process_info)
        actual = instance.callback()
        self.assertIs(Result.success, actual)

    def test_get_selected_mylist_row_index(self):
        """get_selected_mylist_row_index の挙動（選択あり・未選択・属性なし・例外発生）"""
        instance = ConcreteProcess(self.process_info)

        # 選択あり（row を返すモック）
        lw = MagicMock()
        idx = MagicMock()
        idx.row.return_value = 4  # 単数想定
        lw.selectedIndexes.return_value = [idx]
        instance.window.list_widget = lw

        actual = instance.get_selected_mylist_row_index()
        self.assertIsInstance(actual, SelectedMylistRowIndex)
        self.assertEqual(int(actual), 4)

        # 未選択時は SelectedMylistRowIndex(0) を返す
        lw = MagicMock()
        lw.selectedIndexes.return_value = []
        instance.window.list_widget = lw

        actual = instance.get_selected_mylist_row_index()
        self.assertIsInstance(actual, SelectedMylistRowIndex)
        self.assertEqual(int(actual), 0)

        # selectedIndexes が例外を投げたら None
        lw = MagicMock()
        lw.selectedIndexes.side_effect = Exception("selectedIndexes error")
        instance.window.list_widget = lw

        actual = instance.get_selected_mylist_row_index()
        self.assertIsNone(actual)

        # list_widget 属性が無ければ None
        del instance.window.list_widget
        actual = instance.get_selected_mylist_row_index()
        self.assertIsNone(actual)

    def test_get_selected_mylist_row(self):
        """get_selected_mylist_row の挙動（選択あり・選択なし・属性なし）"""
        instance = ConcreteProcess(self.process_info)

        # 選択あり -> SelectedMylistRow.create
        mylist_showname = "testさんの投稿動画"
        selected_mylist_row = SelectedMylistRow.create(mylist_showname)
        lw = MagicMock()
        item = MagicMock()
        item.text.return_value = mylist_showname
        lw.selectedItems.return_value = [item]
        instance.window.list_widget = lw

        actual = instance.get_selected_mylist_row()
        self.assertIsInstance(actual, SelectedMylistRow)
        self.assertEqual(selected_mylist_row, actual)

        # 選択なし -> None
        lw = MagicMock()
        lw.selectedItems.return_value = []
        instance.window.list_widget = lw
        actual = instance.get_selected_mylist_row()
        self.assertIsNone(actual)

        # list_widget 属性が無い -> None
        del instance.window.list_widget
        actual = instance.get_selected_mylist_row()
        self.assertIsNone(actual)

    def test_get_all_mylist_row(self):
        """get_all_mylist_row の挙動"""

        # 正常系: get_all_mylist_row が list_widget.findItems の結果を MylistRowList.create に渡して返すこと
        instance = ConcreteProcess(self.process_info)

        mylist_row_list = MylistRowList.create(["test1さんの投稿動画", "test2さんの投稿動画"])
        lw = MagicMock()
        item1 = MagicMock()
        item1.text.return_value = "test1さんの投稿動画"
        item2 = MagicMock()
        item2.text.return_value = "test2さんの投稿動画"
        lw.findItems.return_value = [item1, item2]
        instance.window.list_widget = lw

        actual = instance.get_all_mylist_row()
        self.assertIsInstance(actual, MylistRowList)
        self.assertEqual(mylist_row_list, actual)

        # 異常系: 例外発生
        lw = MagicMock()
        lw.findItems.side_effect = Exception("findItems error")
        instance.window.list_widget = lw

        actual = instance.get_all_mylist_row()
        self.assertIsNone(actual)

    def test_get_selected_table_row_index_list(self):
        # 正常系: selectedIndexes の結果を SelectedTableRowIndexList.create に渡すこと
        instance = ConcreteProcess(self.process_info)

        selected_table_row_index_list = SelectedTableRowIndexList.create([1, 2])
        tw = MagicMock()
        idx1 = MagicMock()
        idx1.row.return_value = 1
        idx2 = MagicMock()
        idx2.row.return_value = 1
        idx3 = MagicMock()
        idx3.row.return_value = 2
        tw.selectedIndexes.return_value = [idx1, idx2, idx3]
        instance.window.table_widget = tw

        actual = instance.get_selected_table_row_index_list()
        self.assertIsInstance(actual, SelectedTableRowIndexList)
        self.assertEqual(selected_table_row_index_list, actual)

        # 異常系: 例外発生
        tw = MagicMock()
        tw.selectedIndexes.side_effect = Exception("findItems error")
        instance.window.table_widget = tw

        actual = instance.get_selected_table_row_index_list()
        self.assertIsNone(actual)

    def test_get_selected_table_row_list(self):
        """get_selected_table_row_list が選択セルの配列を列数で分割して SelectedTableRowList.create に渡すこと"""
        instance = ConcreteProcess(self.process_info)
        table_row, row, col = self._make_table_row()

        # 正常系: 選択されているテーブル行を取得する
        selected_table_row_list = []
        selected_items = [items.text() for items in table_row]
        for i in range(row):
            selected_table_row = list(selected_items[i * col : (i + 1) * col])
            selected_table_row_list.append(selected_table_row)

        expect = SelectedTableRowList.create(selected_table_row_list)
        tw = MagicMock()
        tw.selectedItems.return_value = table_row
        tw.columnCount.return_value = col
        instance.window.table_widget = tw

        actual = instance.get_selected_table_row_list()
        self.assertIsInstance(actual, SelectedTableRowList)
        self.assertEqual(expect, actual)

        # 正常系: 選択されているテーブル行が無い場合は空の SelectedTableRowList を返す
        tw = MagicMock()
        tw.selectedItems.return_value = []
        tw.columnCount.return_value = col
        instance.window.table_widget = tw

        actual = instance.get_selected_table_row_list()
        self.assertIsInstance(actual, SelectedTableRowList)
        self.assertEqual(SelectedTableRowList([]), actual)

        # 異常系: テーブル列が0の場合は None を返す
        tw = MagicMock()
        tw.selectedItems.return_value = []
        tw.columnCount.return_value = 0
        instance.window.table_widget = tw

        actual = instance.get_selected_table_row_list()
        self.assertIsNone(actual)

    def test_get_all_table_row(self):
        """get_all_table_row がウィンドウのテーブル値を TableRowList.create に渡して返すこと"""
        instance = ConcreteProcess(self.process_info)
        table_row, row, col = self._make_table_row()

        # 正常系: すべてのテーブル行を取得する
        table_row_list = []
        cell_list = [items.text() for items in table_row]
        for i in range(row):
            row_list = []
            for j in range(col):
                row_list.append(cell_list[i * col + j])
            table_row_list.append(row_list)

        expect = TableRowList.create(table_row_list)
        tw = MagicMock()
        tw.rowCount.return_value = row
        tw.columnCount.return_value = col
        tw.item.side_effect = lambda i, j: table_row[i * col + j]
        instance.window.table_widget = tw

        actual = instance.get_all_table_row()
        self.assertIsInstance(actual, TableRowList)
        self.assertEqual(expect, actual)

        # 正常系: テーブル行が無い場合は空の TableRowList を返す
        tw = MagicMock()
        tw.rowCount.return_value = 0
        tw.columnCount.return_value = 0
        tw.item.side_effect = lambda i, j: None
        instance.window.table_widget = tw

        actual = instance.get_all_table_row()
        self.assertIsInstance(actual, TableRowList)
        self.assertEqual(TableRowList([]), actual)

        # 異常系: テーブルのアイテム取得に失敗した場合は None を返す
        tw = MagicMock()
        tw.rowCount.return_value = 1
        tw.columnCount.return_value = col
        tw.item.side_effect = Exception("item error")
        instance.window.table_widget = tw

        actual = instance.get_all_table_row()
        self.assertIsNone(actual)

    def test_set_all_table_row(self):
        """set_all_table_row がテーブルウィジェットを操作してセルを設定し更新すること"""
        self.enterContext(patch("nnmm.process.base.time.sleep"))
        instance = ConcreteProcess(self.process_info)
        table_row, row, col = self._make_table_row()

        table_row_list = []
        item_list = [items.text() for items in table_row]
        for i in range(row):
            row_list = list(item_list[i * col : (i + 1) * col])
            table_row_list.append(row_list)
        table_row_list = TableRowList.create(table_row_list)

        # 正常系
        table_widget = MagicMock()
        table_widget.clearContents = MagicMock()
        table_widget.setRowCount = MagicMock()
        table_widget.setColumnCount = MagicMock()
        table_widget.setHorizontalHeaderLabels = MagicMock()
        vh = MagicMock()
        vh.hide = MagicMock()
        table_widget.verticalHeader.return_value = vh

        hh = MagicMock()
        hh.setSectionResizeMode = MagicMock()
        hh.resizeSection = MagicMock()
        table_widget.horizontalHeader.return_value = hh

        table_widget.setItem = MagicMock()
        table_widget.update = MagicMock()

        instance.window.table_widget = table_widget

        actual = instance.set_all_table_row(table_row_list)

        self.assertEqual(table_row_list, actual)
        self.assertEqual(table_widget.setRowCount.mock_calls, [call(0), call(row)])
        self.assertEqual(table_widget.setColumnCount.mock_calls, [call(0), call(col)])
        self.assertEqual(table_widget.setItem.call_count, row * col)
        table_widget.update.assert_called()

        table_widget.setRowCount.reset_mock()
        table_widget.setColumnCount.reset_mock()
        table_widget.setItem.reset_mock()
        table_widget.update.reset_mock()

        # 異常系: table_row_list の row が不正
        actual = instance.set_all_table_row([])

        self.assertIsNone(actual)
        self.assertEqual(table_widget.setRowCount.mock_calls, [call(0)])
        self.assertEqual(table_widget.setColumnCount.mock_calls, [call(0)])
        table_widget.setItem.assert_not_called()
        table_widget.update.assert_not_called()

        table_widget.setRowCount.reset_mock()
        table_widget.setColumnCount.reset_mock()
        table_widget.setItem.reset_mock()
        table_widget.update.reset_mock()

        # 異常系: table_row_list の col が不正
        mock_table_row = MagicMock()
        mock_table_row.to_row.return_value = ["only_one_column"]
        actual = instance.set_all_table_row([mock_table_row])

        self.assertIsNone(actual)
        self.assertEqual(table_widget.setRowCount.mock_calls, [call(0)])
        self.assertEqual(table_widget.setColumnCount.mock_calls, [call(0)])
        table_widget.setItem.assert_not_called()
        table_widget.update.assert_not_called()

        table_widget.setRowCount.reset_mock()
        table_widget.setColumnCount.reset_mock()
        table_widget.setItem.reset_mock()
        table_widget.update.reset_mock()

        # 異常系: 例外発生
        table_widget.clearContents.side_effect = Exception("error")
        actual = instance.set_all_table_row([])

        self.assertIsNone(actual)
        table_widget.setRowCount.assert_not_called()
        table_widget.setColumnCount.assert_not_called()
        table_widget.setItem.assert_not_called()
        table_widget.update.assert_not_called()

        table_widget.setRowCount.reset_mock()
        table_widget.setColumnCount.reset_mock()
        table_widget.setItem.reset_mock()
        table_widget.update.reset_mock()

    def test_get_upper_textbox(self):
        """get_upper_textbox が tbox_mylist_url の値を UpperTextbox に渡して返すこと"""
        instance = ConcreteProcess(self.process_info)
        mylist_url = "http://example.com/mylist_url"
        expect = UpperTextbox(mylist_url)

        # 正常系
        tbox = MagicMock()
        tbox.text.return_value = mylist_url
        instance.window.tbox_mylist_url = tbox
        actual = instance.get_upper_textbox()
        self.assertEqual(expect, actual)

        # 異常系: 例外発生
        tbox = MagicMock()
        tbox.text.side_effect = Exception("text error")
        instance.window.tbox_mylist_url = tbox
        actual = instance.get_upper_textbox()
        self.assertIsNone(actual)

        # 異常系: 属性が無い
        del instance.window.tbox_mylist_url
        actual = instance.get_upper_textbox()
        self.assertIsNone(actual)

    def test_set_upper_textbox(self):
        """set_upper_textbox がテキストをセットし is_repaint=True のとき repaint を呼ぶこと"""
        text = "new_value"
        expect = UpperTextbox(text)

        # 正常系: is_repaint=True のとき
        instance = ConcreteProcess(self.process_info)
        tbox = MagicMock()
        tbox.setText = MagicMock()
        tbox.repaint = MagicMock()
        tbox.update = MagicMock()
        instance.window.tbox_mylist_url = tbox

        actual = instance.set_upper_textbox(text, is_repaint=True)
        tbox.setText.assert_called_with(text)
        tbox.repaint.assert_called_once()
        tbox.update.assert_not_called()
        self.assertEqual(expect, actual)

        # 正常系: is_repaint=False のとき
        instance = ConcreteProcess(self.process_info)
        tbox = MagicMock()
        tbox.setText = MagicMock()
        tbox.repaint = MagicMock()
        tbox.update = MagicMock()
        instance.window.tbox_mylist_url = tbox

        actual = instance.set_upper_textbox(text, is_repaint=False)
        tbox.setText.assert_called_with(text)
        tbox.repaint.assert_not_called()
        tbox.update.assert_called_once()
        self.assertEqual(expect, actual)

        # 異常系: 例外発生
        instance = ConcreteProcess(self.process_info)
        tbox = MagicMock()
        tbox.setText.side_effect = Exception("fail")
        instance.window.tbox_mylist_url = tbox

        actual = instance.set_upper_textbox(text)
        self.assertIsNone(actual)

        # 異常系: 属性が無い
        instance = ConcreteProcess(self.process_info)
        del instance.window.tbox_mylist_url

        actual = instance.set_upper_textbox(text)
        self.assertIsNone(actual)

    def test_get_bottom_textbox(self):
        """get_bottom_textbox が tbox_mylist_url の値を UpperTextbox に渡して返すこと"""
        instance = ConcreteProcess(self.process_info)
        mylist_url = "http://example.com/mylist_url"
        expect = BottomTextbox(mylist_url)

        # 正常系
        oneline_log = MagicMock()
        oneline_log.text.return_value = mylist_url
        instance.window.oneline_log = oneline_log
        actual = instance.get_bottom_textbox()
        self.assertEqual(expect, actual)

        # 異常系: 例外発生
        oneline_log = MagicMock()
        oneline_log.text.side_effect = Exception("text error")
        instance.window.oneline_log = oneline_log
        actual = instance.get_bottom_textbox()
        self.assertIsNone(actual)

        # 異常系: 属性が無い
        del instance.window.oneline_log
        actual = instance.get_bottom_textbox()
        self.assertIsNone(actual)

    def test_set_bottom_textbox(self):
        """set_bottom_textbox がテキストをセットし is_repaint=True のとき repaint を呼ぶこと"""
        text = "new_value"
        expect = BottomTextbox(text)

        # 正常系: is_repaint=True のとき
        instance = ConcreteProcess(self.process_info)
        oneline_log = MagicMock()
        oneline_log.setText = MagicMock()
        oneline_log.repaint = MagicMock()
        oneline_log.update = MagicMock()
        instance.window.oneline_log = oneline_log

        actual = instance.set_bottom_textbox(text, is_repaint=True)
        oneline_log.setText.assert_called_with(text)
        oneline_log.repaint.assert_called_once()
        oneline_log.update.assert_not_called()
        self.assertEqual(expect, actual)

        # 正常系: is_repaint=False のとき
        instance = ConcreteProcess(self.process_info)
        oneline_log = MagicMock()
        oneline_log.setText = MagicMock()
        oneline_log.repaint = MagicMock()
        oneline_log.update = MagicMock()
        instance.window.oneline_log = oneline_log

        actual = instance.set_bottom_textbox(text, is_repaint=False)
        oneline_log.setText.assert_called_with(text)
        oneline_log.repaint.assert_not_called()
        oneline_log.update.assert_called_once()
        self.assertEqual(expect, actual)

        # 異常系: 例外発生
        instance = ConcreteProcess(self.process_info)
        oneline_log = MagicMock()
        oneline_log.setText.side_effect = Exception("fail")
        instance.window.oneline_log = oneline_log

        actual = instance.set_bottom_textbox(text)
        self.assertIsNone(actual)

        # 異常系: 属性が無い
        instance = ConcreteProcess(self.process_info)
        del instance.window.oneline_log

        actual = instance.set_bottom_textbox(text)
        self.assertIsNone(actual)

    def test_update_mylist_pane(self):
        """update_mylist_pane のテスト"""

        Params = namedtuple("Params", ["s_index", "include_new", "empty_list"])

        def pre_run(params: Params):
            instance = ConcreteProcess(self.process_info)

            # selected index の挙動をセット
            if params.s_index >= 0:
                instance.get_selected_mylist_row_index = lambda: SelectedMylistRowIndex(params.s_index)
            else:
                instance.get_selected_mylist_row_index = lambda: None

            # mylist_db.select の戻り値を準備
            if params.empty_list:
                instance.mylist_db.select = MagicMock(return_value=[])
            else:
                mylist_rows = self._make_mylist_db()
                if params.include_new:
                    for row in mylist_rows:
                        row["is_include_new"] = True
                return_list = [dict(r) for r in mylist_rows]
                instance.mylist_db.select = MagicMock(return_value=return_list)

            # list_widget をモック化
            lw = MagicMock(spec=QListWidget)
            lw.clear = MagicMock()
            lw.addItem = MagicMock()
            lw.setCurrentRow = MagicMock()
            instance.window.list_widget = lw

            # QListWidgetItem をモックに置き換える
            qitem_mock = MagicMock()
            self.enterContext(patch("nnmm.process.base.QListWidgetItem", return_value=qitem_mock))

            return instance

        def post_run(actual, instance, params: Params):
            # 結果確認
            self.assertEqual(Result.success, actual)

            lw = instance.window.list_widget
            lw.clear.assert_called_once()

            # addItem の呼び出しは list の長さ分
            if params.empty_list:
                expected_list = []
            else:
                expected_list = self._make_mylist_db()
                if params.include_new:
                    for row in expected_list:
                        row["is_include_new"] = True
            self.assertEqual(lw.addItem.call_count, len(expected_list))

            # 各アイテムの引数をチェック：is_include_new True のとき QListWidgetItem が渡される
            calls = lw.addItem.call_args_list
            for idx, row in enumerate(expected_list):
                if row["is_include_new"]:
                    # addItem に渡されたのが qitem_mock（QListWidgetItem の return_value）
                    self.assertIsInstance(calls[idx][0][0], MagicMock)
                else:
                    # 文字列が渡される
                    self.assertEqual(calls[idx][0][0], row["showname"])

            # setCurrentRow の引数
            expected_index = (
                params.s_index
                if (params.s_index >= 0 and not params.empty_list and params.s_index < len(expected_list))
                else 0
            )
            lw.setCurrentRow.assert_called_once_with(expected_index)

        params_list = [
            Params(0, True, False),
            Params(1, True, False),
            Params(-1, True, False),
            Params(0, False, False),
            Params(1, False, False),
            Params(-1, False, False),
            Params(0, True, True),  # 空リスト
        ]

        for params in params_list:
            instance = pre_run(params)
            actual = instance.update_mylist_pane()
            post_run(actual, instance, params)

    def test_update_table_pane(self):
        """update_table_pane のテスト"""
        row_index = 2
        valid_mylist_url = f"https://www.nicovideo.jp/user/1000000{row_index + 1}/video"
        Params = namedtuple(
            "Params",
            [
                "mylist_url",
                "upper_text",
                "selected_mylist_row_index",
                "kind_mylist_db",
                "kind_mylist_info_db",
                "result",
            ],
        )

        def pre_run(params: Params) -> ConcreteProcess:
            instance = ConcreteProcess(self.process_info)
            mylist_url = params.mylist_url

            if mylist_url == "":
                mylist_url = params.upper_text

            # list_widget を用意
            lw = MagicMock()
            lw.setCurrentRow = MagicMock()
            instance.window.list_widget = lw

            # upper textbox の挙動を設定
            ut = MagicMock()
            ut.to_str.return_value = params.upper_text
            instance.get_upper_textbox = MagicMock(return_value=ut)

            # selected index の挙動
            if mylist_url == "":
                instance.get_selected_mylist_row_index = MagicMock(return_value=params.selected_mylist_row_index)
            else:
                instance.get_selected_mylist_row_index = MagicMock(return_value=None)

            # mylist_db と mylist_info_db の設定
            instance.mylist_db = MagicMock()
            if params.kind_mylist_db == "exist":
                mylist_rows = self._make_mylist_db()
                instance.mylist_db.select = MagicMock(return_value=mylist_rows)
            else:
                instance.mylist_db.select = MagicMock(return_value=[])

            instance.mylist_info_db = MagicMock()
            if params.kind_mylist_info_db == "exist":
                mylist_info_rows = self._make_mylist_info_db(mylist_url)
                instance.mylist_info_db.select_from_mylist_url = MagicMock(return_value=mylist_info_rows)
            else:
                instance.mylist_info_db.select_from_mylist_url = MagicMock(return_value=[])

            # get_all_table_row をモックに置き換える
            instance.get_all_table_row = MagicMock(return_value="get_all_table_row()_result")

            # set_all_table_row をモックに置き換える
            instance.set_all_table_row = MagicMock(return_value=None)

            return instance

        def post_run(actual: Result, instance: ConcreteProcess, params: Params):
            self.assertEqual(params.result, actual)
            mylist_url = params.mylist_url

            if mylist_url == "":
                instance.get_upper_textbox.assert_called_once()
                mylist_url = params.upper_text
            else:
                instance.get_upper_textbox.assert_not_called()

            index = 0
            if mylist_url == "":
                instance.get_all_table_row.assert_called_once()
                instance.get_selected_mylist_row_index.assert_called_once()
                instance.mylist_db.select.assert_not_called()
                instance.mylist_info_db.select_from_mylist_url.assert_not_called()

                if params.selected_mylist_row_index:
                    index = int(params.selected_mylist_row_index)
                def_data = "get_all_table_row()_result"
            else:
                instance.get_all_table_row.assert_not_called()
                instance.get_selected_mylist_row_index.assert_not_called()
                instance.mylist_db.select.assert_called_once()
                instance.mylist_info_db.select_from_mylist_url.assert_called_once()

                if params.kind_mylist_db == "exist":
                    m_list = self._make_mylist_db()
                else:
                    m_list = []
                mylist_url_list = [m["url"] for m in m_list]
                for i, url in enumerate(mylist_url_list):
                    if mylist_url == url:
                        index = i
                        break

                if params.kind_mylist_info_db == "exist":
                    records = self._make_mylist_info_db(mylist_url)
                else:
                    records = []
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

            # list_widget.setCurrentRow の呼び出し確認
            instance.window.list_widget.setCurrentRow.assert_called_once_with(index)

            # set_all_table_row が呼ばれ、期待する引数が渡されていることを確認
            instance.set_all_table_row.assert_called_once_with(def_data)

        params_list = [
            Params(valid_mylist_url, "", 0, "exist", "exist", Result.success),
            Params(valid_mylist_url, "", 0, "exist", "empty", Result.success),
            Params(valid_mylist_url, "", 0, "empty", "empty", Result.success),
            Params("", valid_mylist_url, row_index, "exist", "exist", Result.success),
            Params("", valid_mylist_url, row_index, "exist", "empty", Result.success),
            Params("", valid_mylist_url, row_index, "empty", "empty", Result.success),
            Params("", "", 0, "exist", "exist", Result.success),
            Params("", "", 0, "exist", "empty", Result.success),
            Params("", "", 0, "empty", "empty", Result.success),
            Params("", "", row_index, "exist", "exist", Result.success),
            Params("", "", row_index, "exist", "empty", Result.success),
            Params("", "", row_index, "empty", "empty", Result.success),
            Params("", "", None, "exist", "exist", Result.success),
        ]

        for params in params_list:
            instance = pre_run(params)
            actual = instance.update_table_pane(params.mylist_url)
            post_run(actual, instance, params)


if __name__ == "__main__":
    import sys

    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
