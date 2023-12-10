from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.gui_function import *
from NNMM.mylist_db_controller import *
from NNMM.mylist_info_db_controller import *
from NNMM.process.process_base import ProcessBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessWatched(ProcessBase):

    def __init__(self):
        super().__init__(True, True, "視聴済にする")

    def run(self, mw):
        """動画の状況ステータスを""(視聴済)に設定する

        Notes:
            "視聴済にする::-TR-"
            テーブル右クリックで「視聴済にする」が選択された場合

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 処理成功した場合0, エラー時-1
        """
        logger.info("Watched start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("Watched failed, argument error.")
            return -1

        # 現在のtableの全リスト
        def_data = self.window["-TABLE-"].Values

        # 行が選択されていないなら何もしない
        if not self.values["-TABLE-"]:
            logger.error("Watched failed, no record selected.")
            return -1

        # 選択された行（複数可）についてすべて処理する
        all_num = len(self.values["-TABLE-"])
        row = 0
        for i, v in enumerate(self.values["-TABLE-"]):
            row = int(v)

            # マイリスト情報ステータスDB更新
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
            selected = def_data[row]
            res = self.mylist_info_db.update_status(selected[1], selected[8], "")
            if res == 0:
                logger.info(f'{selected[1]} ({i+1}/{all_num}) -> marked "watched".')
            else:
                logger.info(f"{selected[1]} ({i+1}/{all_num}) -> failed.")

            # テーブル更新
            def_data[row][4] = ""

            # 視聴済になったことでマイリストの新着表示を消すかどうか判定する
            m_list = self.mylist_info_db.select_from_mylist_url(selected[8])
            m_list = [list(m.values()) for m in m_list]
            if not is_mylist_include_new_video(m_list):
                # マイリストDB新着フラグ更新
                self.mylist_db.update_include_flag(selected[8], False)

        # テーブル更新を反映させる
        self.window["-TABLE-"].update(values=def_data)

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        update_table_pane(self.window, self.mylist_db, self.mylist_info_db, mylist_url)
        self.window["-TABLE-"].update(select_rows=[row])

        # マイリスト画面表示更新
        update_mylist_pane(self.window, self.mylist_db)

        logger.info("Watched success.")
        return 0


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()()
    mw.run()
