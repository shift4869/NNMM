# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.GuiFunction import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.Process import ProcessBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessNotWatched(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "未視聴にする")

    def run(self, mw):
        """動画の状況ステータスを"未視聴"に設定する

        Notes:
            "未視聴にする::-TR-"
            テーブル右クリックで「未視聴にする」が選択された場合

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 処理成功した場合0, エラー時-1
        """
        logger.info("NotWatched start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("NotWatched failed, argument error.")
            return -1

        # 現在のtableの全リスト
        def_data = self.window["-TABLE-"].Values

        # 行が選択されていないなら何もしない
        if not self.values["-TABLE-"]:
            logger.error("NotWatched failed, no record selected.")
            return -1

        # 選択された行（複数可）についてすべて処理する
        all_num = len(self.values["-TABLE-"])
        row = 0
        for i, v in enumerate(self.values["-TABLE-"]):
            row = int(v)

            # マイリスト情報ステータスDB更新
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
            selected = def_data[row]
            res = self.mylist_info_db.update_status(selected[1], selected[8], "未視聴")
            if res == 0:
                logger.info(f'{selected[1]} ({i+1}/{all_num}) -> marked "non-watched".')
            else:
                logger.info(f"{selected[1]} ({i+1}/{all_num}) -> failed.")

            # テーブル更新
            def_data[row][4] = "未視聴"

            # 未視聴になったことでマイリストの新着表示を表示する
            # 未視聴にしたので必ず新着あり扱いになる
            # マイリストDB新着フラグ更新
            self.mylist_db.update_include_flag(selected[8], True)

        # テーブル更新を反映させる
        self.window["-TABLE-"].update(values=def_data)

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)
        self.window["-TABLE-"].update(select_rows=[row])

        # マイリスト画面表示更新
        update_mylist_pane(self.window, self.mylist_db)

        logger.info("NotWatched success.")
        return 0


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.run()
