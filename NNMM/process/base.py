from abc import ABC, abstractmethod

import PySimpleGUI as sg

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.value_objects.mylist_row import MylistRow
from NNMM.process.value_objects.mylist_row_index_list import SelectedMylistRowIndexList
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.process.value_objects.table_row import TableRowTuple
from NNMM.process.value_objects.table_row_list import TableRowList
from NNMM.process.value_objects.textbox_upper import UpperTextbox
from NNMM.util import Result


class ProcessBase(ABC):
    process_info: ProcessInfo
    name: str
    window: sg.Window
    values: dict
    mylist_db: MylistDBController
    mylist_info_db: MylistInfoDBController

    def __init__(self, process_info: ProcessInfo) -> None:
        if not isinstance(process_info, ProcessInfo):
            raise ValueError("process_info must be ProcessInfo.")
        self.process_info = process_info
        self.name = process_info.name
        self.window = process_info.window
        self.values = process_info.values
        self.mylist_db = process_info.mylist_db
        self.mylist_info_db = process_info.mylist_info_db

    @abstractmethod
    def run(self) -> Result:
        raise NotImplementedError

    def update_mylist_pane(self) -> Result:
        """マイリストペインの表示を更新する

        Returns:
            Result: 成功時success
        """
        # 現在選択中のマイリストがある場合そのindexを保存
        index = 0
        selected_index_list = SelectedMylistRowIndexList.create(self.window["-LIST-"].get_indexes())
        if selected_index_list:
            index = int(selected_index_list[0])

        # マイリスト画面表示更新
        # NEW_MARK = "*:"
        m_list = self.mylist_db.select()
        include_new_index_list = []
        for i, m in enumerate(m_list):
            if m["is_include_new"]:
                mylist_row = MylistRow.create([m["showname"]])
                m["showname"] = mylist_row.with_new_mark_name()
                include_new_index_list.append(i)
        list_data = [m["showname"] for m in m_list]
        self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        # update(values=list_data)で更新されるとデフォルトに戻る？
        # 強調したいindexのみ適用すればそれ以外はデフォルトになる
        for i in include_new_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # indexをセットしてスクロール
        # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
        # list_data が空のときにindexを設定しても問題ない
        # self.window["-LIST-"].update(scroll_to_index=index)
        self.window["-LIST-"].Widget.see(index)
        self.window["-LIST-"].update(set_to_index=index)
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
        # 右上のテキストボックスに表示されている現在のマイリストURLを設定する(window["-INPUT1-"])
        if mylist_url == "":
            mylist_url = UpperTextbox.create(self.window["-INPUT1-"].get()).to_str()

        index = 0
        def_data: TableRowList = []
        if mylist_url == "":
            # 引数も右上のテキストボックスも空白の場合
            # 現在表示しているテーブルの表示をリフレッシュする処理のみ行う
            def_data = TableRowList.create(self.window["-TABLE-"].Values)

            # 現在選択中のマイリストがある場合そのindexを保存
            selected_index_list = SelectedMylistRowIndexList.create(list(self.window["-LIST-"].get_indexes()))
            if selected_index_list:
                index = int(selected_index_list[0])
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
                record = TableRowTuple._make(
                    [i + 1] + list(r.values())[1:-1]
                )
                table_row = [
                    record.row_index,
                    record.video_id,
                    record.title,
                    record.username,
                    record.status,
                    record.uploaded_at,
                    record.registered_at,
                    record.video_url,
                    record.mylist_url
                ]
                table_row_list.append(table_row)
            def_data = TableRowList.create(table_row_list)

        # 画面更新
        # LIST は空のときにindexを設定しても問題ないが、
        # TABLE は空のときにselect_rowsしてはいけない
        # self.window["-LIST-"].update(set_to_index=index)
        self.window["-LIST-"].Widget.see(index)
        self.window["-TABLE-"].update(values=def_data.to_table_data())
        if len(def_data) > 0:
            self.window["-TABLE-"].update(select_rows=[0])
        # 1行目は背景色がリセットされないので個別に指定してdefaultの色で上書き
        self.window["-TABLE-"].update(row_colors=[(0, "", "")])
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
