# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessShowMylistInfoAll(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "最近追加された動画を一覧表示")

    def Run(self, mw):
        # "全動画表示::-MR-"
        # リストボックスの項目がダブルクリックされた場合（単一）
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # 現在選択中のマイリストがある場合そのindexを保存
        index = 0
        if self.window["-LIST-"].get_indexes():
            index = self.window["-LIST-"].get_indexes()[0]

        # 全動画情報を取得
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded"]
        def_data = self.window["-TABLE-"].Values  # 現在のtableの全リスト
        m_list = self.mylist_info_db.Select()  # DB内にある全ての動画情報を取得
        records = sorted(m_list, key=lambda x: x["uploaded_at"], reverse=True)[0:100]  # 最大100要素までのスライス
        def_data = []
        for i, r in enumerate(records):
            a = [i + 1, r["video_id"], r["title"], r["username"], r["status"], r["uploaded_at"]]
            def_data.append(a)

        # 右上のマイリストURLは空白にする
        self.window["-INPUT1-"].update(value="")

        # テーブル更新
        # UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        # 画面更新
        self.window["-LIST-"].update(set_to_index=index)
        self.window["-TABLE-"].update(values=def_data)
        if len(def_data) > 0:
            self.window["-TABLE-"].update(select_rows=[0])
        # 1行目は背景色がリセットされないので個別に指定してdefaultの色で上書き
        self.window["-TABLE-"].update(row_colors=[(0, "", "")])

        logger.info(f"all mylist info shown.")


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
