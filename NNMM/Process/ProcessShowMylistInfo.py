# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessShowMylistInfo(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト内容表示")

    def Run(self, mw):
        # "-LIST-+DOUBLE CLICK+"
        # リストボックスの項目がダブルクリックされた場合（単一）
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        v = self.values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値
        def_data = self.window["-TABLE-"].Values  # 現在のtableの全リスト

        if v[:2] == "*:":
            v = v[2:]
        record = self.mylist_db.SelectFromListname(v)[0]
        username = record.get("username")
        mylist_url = record.get("url")
        self.window["-INPUT1-"].update(value=mylist_url)  # 対象マイリスのアドレスをテキストボックスに表示

        # テーブル更新
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info(f"{mylist_url} -> mylist info shown.")


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
