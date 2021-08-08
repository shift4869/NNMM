# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessDeleteMylist(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト削除")

    def Run(self, mw):
        # "-DELETE-"
        # 左下、マイリスト追加ボタンが押された場合
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # 現在のマイリストURL
        mylist_url = self.values["-INPUT1-"]

        # 右上のテキストボックスにも左下のテキストボックスにも
        # URLが入力されていない場合何もしない
        if mylist_url == "":
            mylist_url = self.values["-INPUT2-"]
            if mylist_url == "":
                return

        # 既存マイリストと重複していない場合何もしない
        prev_mylist = self.mylist_db.SelectFromURL(mylist_url)[0]
        if not prev_mylist:
            return

        # 確認
        # res = sg.popup_ok_cancel(mylist_url + "\nマイリスト削除しますか？")
        # if res == "Cancel":
        #     return

        # マイリスト情報から対象動画の情報を削除する
        self.mylist_info_db.DeleteFromMylistURL(mylist_url)

        # マイリストからも削除する
        self.mylist_db.DeleteFromURL(mylist_url)

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)

        # マイリスト情報テーブルの表示を初期化する
        self.window["-TABLE-"].update(values=[[]])


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
