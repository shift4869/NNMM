# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.GuiFunction import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.Process import ProcessBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessWatchedAllMylist(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "視聴済にする（全て）")

    def run(self, mw):
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

        m_list = self.mylist_db.select()
        records = [m for m in m_list if m["is_include_new"]]

        all_num = len(records)
        for i, record in enumerate(records):
            mylist_url = record.get("url")

            # マイリストの新着フラグがFalseなら何もしない
            if not record.get("is_include_new"):
                continue

            # マイリスト情報内の視聴済フラグを更新
            self.mylist_info_db.update_status_in_mylist(mylist_url, "")
            # マイリストの新着フラグを更新
            self.mylist_db.update_include_flag(mylist_url, False)

            logger.info(f'{mylist_url} -> all include videos status are marked "watched" ... ({i + 1}/{all_num}).')

        # 右上のテキストボックスからマイリストURLを取得
        mylist_url = self.window["-INPUT1-"].get()
        # 空白の場合
        if mylist_url == "":
            # 現在表示しているテーブルの表示をすべて視聴済にする
            def_data = self.window["-TABLE-"].Values  # 現在のtableの全リスト

            for i, record in enumerate(def_data):
                table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
                def_data[i][4] = ""
            self.window["-TABLE-"].update(values=def_data)

        # マイリスト画面表示更新
        update_mylist_pane(self.window, self.mylist_db)
        # テーブル画面表示更新
        update_table_pane(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info(f"WatchedAllMylist success.")
        return 0
   

if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.run()
