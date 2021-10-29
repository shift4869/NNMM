# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessWatchedMylist(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "視聴済にする（選択）")

    def Run(self, mw):
        # "視聴済にする（選択）::-MR-""
        # マイリスト右クリックで「視聴済にする（選択）」が選択された場合
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # マイリストが選択されていない場合は何もしない
        if not self.values["-LIST-"]:
            return

        v = self.values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値

        if v[:2] == "*:":
            v = v[2:]
        record = self.mylist_db.SelectFromShowname(v)[0]
        mylist_url = record.get("url")

        # マイリストの新着フラグがFalseなら何もしない
        if not record.get("is_include_new"):
            return

        # マイリスト情報内の視聴済フラグを更新
        self.mylist_info_db.UpdateStatusInMylist(mylist_url, "")
        # マイリストの新着フラグを更新
        self.mylist_db.UpdateIncludeFlag(mylist_url, False)

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)
        # テーブル画面表示更新
        # 現在表示されているマイリストの内容で更新する
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db)
        # 選択されているマイリストの内容を表示する
        # UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info(f'{mylist_url} -> all include videos status are marked "watched".')
    

if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
