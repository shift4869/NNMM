from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.gui_function import *
from NNMM.mylist_db_controller import *
from NNMM.mylist_info_db_controller import *
from NNMM.process.process_base import ProcessBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessMoveDown(ProcessBase):

    def __init__(self):
        super().__init__(True, True, "下に移動")

    def run(self, mw):
        """マイリストの並び順を一つ下に移動させる

        Notes:
            "下に移動::-MR-"
            マイリスト右クリックで「下に移動」が選択された場合

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 移動に成功した場合0,
                 一番下のマイリストが選択され下に移動できなかった場合1,
                 エラー時-1
        """
        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("MoveDown failed, argument error.")
            return -1

        if not self.values["-LIST-"]:
            logger.error("MoveDown failed, no mylist selected.")
            return -1

        src_index = 0
        if self.window["-LIST-"].get_indexes():
            src_index = self.window["-LIST-"].get_indexes()[0]
        src_v = self.values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値
        list_data = self.window["-LIST-"].Values  # 現在のマイリストテーブルの全リスト

        max_index = len(self.mylist_db.select()) - 1
        if src_index >= max_index:
            logger.info(f"{src_v} -> index is {max_index} , can't move down.")
            return 1

        if src_v[:2] == "*:":
            src_v = src_v[2:]
        src_record = self.mylist_db.select_from_showname(src_v)[0]

        dst_index = src_index + 1
        dst_v = list_data[dst_index]
        if dst_v[:2] == "*:":
            dst_v = dst_v[2:]
        dst_record = self.mylist_db.select_from_showname(dst_v)[0]

        self.mylist_db.swap_id(src_record["id"], dst_record["id"])

        # テーブル更新
        update_mylist_pane(self.window, self.mylist_db)
        self.window["-LIST-"].update(set_to_index=dst_index)

        logger.info(f"{src_v} -> index move down from {src_index} to {dst_index}.")
        return 0


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()()
    mw.run()
