import re
import time
from logging import INFO, getLogger

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QDialog, QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.mylist_row import MylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result, popup_get_text

logger = getLogger(__name__)
logger.setLevel(INFO)


class MylistSearch(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト名でマイリストを検索

        Notes:
            "検索（マイリスト）::-MR-"
            マイリスト右クリックで「検索（マイリスト）」が選択された場合
            入力されたマイリスト名を持つマイリストをハイライト表示する

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("MylistSearch start.")

        pattern = popup_get_text("マイリスト名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("MylistSearch is canceled or target word is empty.")
            return Result.failed

        logger.info(f"search word -> {pattern}.")

        # 現在マイリストが選択中の場合indexを保存
        selected_mylist_row_index = self.get_selected_mylist_row_index()
        index = 0
        if selected_mylist_row_index:
            index = int(selected_mylist_row_index)

        # マイリスト画面表示更新
        m_list = self.mylist_db.select()
        include_new_index_list = []
        match_index_list = []
        for i, m in enumerate(m_list):
            if m["is_include_new"]:
                mylist_row = MylistRow.create(m["showname"])
                m["showname"] = mylist_row.with_new_mark_name()
                include_new_index_list.append(i)
            if re.findall(pattern, m["showname"]):
                match_index_list.append(i)
                index = i  # 更新後にスクロールするインデックスを更新
        list_data = [m["showname"] for m in m_list]
        self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        # 強調したいindexのみ適用すればそれ以外はデフォルトになる
        for i in include_new_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # 検索でヒットした項目の背景色とテキスト色を変更する
        for i in match_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light goldenrod")

        # indexをセットしてスクロール
        # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
        # window["-LIST-"].update(scroll_to_index=index)
        self.window["-LIST-"].Widget.see(index)
        self.window["-LIST-"].update(set_to_index=index)

        # 検索結果表示
        if len(match_index_list) > 0:
            logger.info(f"search result -> {len(match_index_list)} mylist(s) found.")
            self.window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing mylist(s) found.")
            self.window["-INPUT2-"].update(value="該当なし")

        logger.info("MylistSearch success.")
        return Result.success


class MylistSearchFromVideo(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリストの中に含んでいる動画名でマイリストを検索

        Notes:
            "検索（動画名）::-MR-"
            マイリスト右クリックで「検索（動画名）」が選択された場合
            入力された動画名を持つ動画を含むマイリストをハイライト表示する

        Todo:
            動画テーブルを表示させて動画レコードまでハイライトする

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("MylistSearchFromVideo start.")

        pattern = popup_get_text("動画名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("MylistSearchFromVideo is canceled or target word is empty.")
            return Result.failed

        logger.info(f"search word -> {pattern}.")

        # 現在マイリストが選択中の場合indexを保存
        selected_mylist_row_index = self.get_selected_mylist_row_index()
        index = 0
        if selected_mylist_row_index:
            index = int(selected_mylist_row_index)

        # マイリスト画面表示更新
        m_list = self.mylist_db.select()
        include_new_index_list = []
        match_index_list = []
        for i, m in enumerate(m_list):
            # 新着マイリストチェック
            if m["is_include_new"]:
                mylist_row = MylistRow.create(m["showname"])
                m["showname"] = mylist_row.with_new_mark_name()
                include_new_index_list.append(i)

            # マイリスト内の動画情報を探索
            mylist_url = m["url"]
            records = self.mylist_info_db.select_from_mylist_url(mylist_url)
            for r in records:
                if re.findall(pattern, r["title"]):
                    match_index_list.append(i)
                    index = i  # 更新後にスクロールするインデックスを更新
        list_data = [m["showname"] for m in m_list]
        self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        # update(values=list_data)で更新されるとデフォルトに戻る？
        # 強調したいindexのみ適用すればそれ以外はデフォルトになる
        for i in include_new_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # 検索でヒットした項目の背景色とテキスト色を変更する
        for i in match_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light goldenrod")

        # indexをセットしてスクロール
        # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
        # window["-LIST-"].update(scroll_to_index=index)
        self.window["-LIST-"].Widget.see(index)
        self.window["-LIST-"].update(set_to_index=index)

        # 検索結果表示
        if len(match_index_list) > 0:
            logger.info(f"search result -> {len(match_index_list)} mylist(s) found.")
            self.window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing mylist(s) found.")
            self.window["-INPUT2-"].update(value="該当なし")

        logger.info("MylistSearchFromVideo success.")
        return Result.success


class MylistSearchFromMylistURL(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリストURLでマイリストを検索

        Notes:
            "検索（URL）::-MR-"
            マイリスト右クリックで「検索（URL）」が選択された場合
            入力されたURLをマイリストURLとして持つマイリストをハイライト表示する

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("MylistSearchFromMylistURL start.")

        search_mylist_url = popup_get_text("マイリストURL入力（完全一致）")
        if search_mylist_url is None or search_mylist_url == "":
            logger.info("MylistSearchFromMylistURL is canceled or target word is empty.")
            return Result.failed

        logger.info(f"search word -> {search_mylist_url}.")

        # 現在マイリストが選択中の場合indexを保存
        selected_mylist_row_index = self.get_selected_mylist_row_index()
        index = 0
        if selected_mylist_row_index:
            index = int(selected_mylist_row_index)

        # マイリスト画面表示更新
        m_list = self.mylist_db.select()
        include_new_index_list = []
        match_index_list = []
        for i, m in enumerate(m_list):
            # 新着マイリストチェック
            if m["is_include_new"]:
                mylist_row = MylistRow.create(m["showname"])
                m["showname"] = mylist_row.with_new_mark_name()
                include_new_index_list.append(i)

            # マイリスト内の動画情報を探索
            if search_mylist_url == m["url"]:
                match_index_list.append(i)
                index = i  # 更新後にスクロールするインデックスを更新
        list_data = [m["showname"] for m in m_list]
        self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        # update(values=list_data)で更新されるとデフォルトに戻る？
        # 強調したいindexのみ適用すればそれ以外はデフォルトになる
        for i in include_new_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # 検索でヒットした項目の背景色とテキスト色を変更する
        for i in match_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light goldenrod")

        # indexをセットしてスクロール
        # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
        # window["-LIST-"].update(scroll_to_index=index)
        self.window["-LIST-"].Widget.see(index)
        self.window["-LIST-"].update(set_to_index=index)

        # 検索結果表示
        if len(match_index_list) > 0:
            logger.info(f"search result -> {len(match_index_list)} mylist(s) found.")
            self.window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing mylist(s) found.")
            self.window["-INPUT2-"].update(value="該当なし")

        logger.info("MylistSearchFromMylistURL success.")
        return Result.success


class VideoSearch(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        """QTableWidgetの右クリックメニューから起動するためコンポーネントは作成しない"""
        return None

    @Slot()
    def callback(self) -> Result:
        """マイリストの中に含んでいる動画名でマイリストを検索

        Notes:
            "検索（動画名）::-TR-"
            動画テーブル右クリックで「検索（動画名）」が選択された場合
            現在表示中の動画テーブルから入力された動画名を持つ動画をハイライト表示する

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("VideoSearch start.")

        # 検索対象ワードをユーザーに問い合わせる
        pattern = popup_get_text("動画名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("VideoSearch is canceled or target word is empty.")
            return Result.failed

        logger.info(f"search word -> {pattern}.")

        # 現在動画テーブルが選択中の場合indexを保存
        selected_table_row_index_list = self.get_selected_table_row_index_list()
        index = 0
        if selected_table_row_index_list:
            index = min([int(v) for v in selected_table_row_index_list.to_int_list()])

        # 既存のテーブルの内容を取得
        table_row_list = self.get_all_table_row()

        # 既存テーブルが空の場合は何もせず返す
        # window: QDialog = self.window
        n = len(table_row_list)
        if n == 0:
            self.set_bottom_textbox("該当なし")
            return Result.failed
        m = len(table_row_list[0].to_row())
        if m == 0:
            self.set_bottom_textbox("該当なし")
            return Result.failed

        # マイリスト内の動画情報を探索
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
        table_widget: QTableWidget = self.window.table_widget
        table_widget.clearContents()
        table_widget.setRowCount(0)
        table_widget.setColumnCount(0)

        table_widget.setRowCount(n)
        table_widget.setColumnCount(m)
        table_widget.setHorizontalHeaderLabels(table_cols_name)
        table_widget.verticalHeader().hide()

        # ヘッダーの列幅調整を確実に反映させるために少し遅延させる
        time.sleep(0.1)

        cols_width = [35, 100, 350, 100, 60, 120, 120, 30, 30]
        for i, section_size in enumerate(cols_width):
            table_widget.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            table_widget.horizontalHeader().resizeSection(i, section_size)

        # 検索しながらテーブルに値を戻していく
        match_index_list = []
        for i, table_row in enumerate(table_row_list):
            # 動画タイトルが検索条件にヒットするか
            if is_hit := re.findall(pattern, table_row.title.name):
                match_index_list.append(i)
            row = table_row.to_row()
            for j, text in enumerate(row):
                if is_hit:
                    # 背景色を変える
                    item = QTableWidgetItem(text)
                    item.setBackground(QColor.fromRgb(96, 96, 0))
                    table_widget.setItem(i, j, item)
                else:
                    # そのまま追加
                    table_widget.setItem(i, j, QTableWidgetItem(text))

        # indexをセットしてスクロール
        if match_index_list:
            for match_index in match_index_list:
                table_widget.selectRow(match_index)
        # else:
        #     table_widget.selectRow(index)

        # 検索結果表示
        if len(match_index_list) > 0:
            logger.info(f"search result -> {len(match_index_list)} record(s) found.")
            self.set_bottom_textbox(f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing record found.")
            self.set_bottom_textbox("該当なし")

        logger.info("VideoSearch done.")
        return Result.success


class MylistSearchClear(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト表示のハイライトを解除する

        Notes:
            "強調表示を解除::-MR-"
            マイリスト右クリックで「強調表示を解除」が選択された場合
            現在表示中のマイリストの表示をもとに戻す

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("MylistSearchClear start.")

        self.update_mylist_pane()

        logger.info("MylistSearchClear success.")
        return Result.success


class VideoSearchClear(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        """QTableWidgetの右クリックメニューから起動するためコンポーネントは作成しない"""
        return None

    @Slot()
    def callback(self) -> Result:
        """テーブル表示のハイライトを解除する

        Notes:
            "強調表示を解除::-TR-"
            動画テーブル右クリックで「強調表示を解除」が選択された場合
            現在表示中の動画テーブルの表示をもとに戻す

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("VideoSearchClear start.")

        # マイリストURL取得
        # 右上のテキストボックスから取得する
        # 「動画をすべて表示」している場合は空文字列になる可能性がある
        # update_table_paneはmylist_urlが空文字列でも処理が可能
        mylist_url = self.get_upper_textbox().to_str()
        self.update_table_pane(mylist_url)

        logger.info("VideoSearchClear done.")
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
