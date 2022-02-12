# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessWatchedAllMylist(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "視聴済にする（全て）")

    def Run(self, mw):
        """すべてのマイリストに含まれる動画情報についてすべて"視聴済"にする

        Notes:
            "視聴済にする（全て）::-MR-"
            マイリスト右クリックで「視聴済にする（全て）」が選択された場合

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, エラー時-1
        """
        logger.info(f"WatchedAllMylist start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("WatchedAllMylist failed, argument error.")
            return -1

        m_list = self.mylist_db.Select()
        records = [m for m in m_list if m["is_include_new"]]

        all_num = len(records)
        for i, record in enumerate(records):
            mylist_url = record.get("url")

            # マイリストの新着フラグがFalseなら何もしない
            if not record.get("is_include_new"):
                continue

            # マイリスト情報内の視聴済フラグを更新
            self.mylist_info_db.UpdateStatusInMylist(mylist_url, "")
            # マイリストの新着フラグを更新
            self.mylist_db.UpdateIncludeFlag(mylist_url, False)

            logger.info(f'{mylist_url} -> all include videos status are marked "watched" ... ({i + 1}/{all_num}).')

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)
        # テーブル画面表示更新
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db)

        logger.info(f"WatchedAllMylist success.")
        return 0
   

if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
