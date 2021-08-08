# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessWatched(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "視聴済にする")

    def Run(self, mw):
        # "視聴済にする::-TR-"
        # テーブル右クリックで「視聴済にする」が選択された場合
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # 現在のtableの全リスト
        def_data = self.window["-TABLE-"].Values
        # 現在のマイリストURL
        mylist_url = self.values["-INPUT1-"]

        # 行が選択されていないなら何もしない
        if not self.values["-TABLE-"]:
            return

        # 選択された行（複数可）についてすべて処理する
        all_num = len(self.values["-TABLE-"])
        for i, v in enumerate(self.values["-TABLE-"]):
            row = int(v)

            # マイリスト情報ステータスDB更新
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時"]
            selected = def_data[row]
            res = self.mylist_info_db.UpdateStatus(selected[1], mylist_url, "")
            if res == 0:
                logger.info(f'{selected[1]} ({i+1}/{all_num}) -> marked "watched".')
            else:
                logger.info(f"{selected[1]} ({i+1}/{all_num}) -> failed.")

            # テーブル更新
            def_data[row][4] = ""
        self.window["-TABLE-"].update(values=def_data)

        # テーブルの表示を更新する
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)
        self.window["-TABLE-"].update(select_rows=[row])

        # 視聴済になったことでマイリストの新着表示を消すかどうか判定する
        if not IsMylistIncludeNewVideo(self.window["-TABLE-"].Values):
            # マイリストDB新着フラグ更新
            self.mylist_db.UpdateIncludeFlag(mylist_url, False)

            # マイリスト画面表示更新
            UpdateMylistShow(self.window, self.mylist_db)


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
