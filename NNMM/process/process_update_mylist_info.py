from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.gui_function import *
from NNMM.mylist_db_controller import *
from NNMM.mylist_info_db_controller import *
from NNMM.process.process_update_mylist_info_base import ProcessUpdateMylistInfoBase, ProcessUpdateMylistInfoThreadDoneBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessUpdateMylistInfo(ProcessUpdateMylistInfoBase):

    def __init__(self):
        """マイリスト情報を更新する

        Notes:
            "-UPDATE-"
            右上の更新ボタンが押された場合
            ProcessUpdateMylistInfoは現在表示されている単一のマイリストについて動画情報を更新する
        """
        super().__init__(True, False, "マイリスト内容更新")

        # ログメッセージ
        self.L_KIND = "Mylist"

        # イベントキー
        self.E_DONE = "-UPDATE_THREAD_DONE-"

    def get_target_mylist(self) -> list[Mylist]:
        """更新対象のマイリストを返す

        Notes:
            ProcessUpdateMylistInfoにおいては対象は単一のマイリストとなる

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        # 属性チェック
        if not hasattr(self, "mylist_db") or not hasattr(self, "values"):
            logger.error(f"{self.L_KIND} GetTargetMylist failed, attribute error.")
            return []

        mylist_url = self.values["-INPUT1-"]
        if mylist_url == "":
            return []

        m_list = self.mylist_db.select_from_url(mylist_url)
        return m_list


class ProcessUpdateMylistInfoThreadDone(ProcessUpdateMylistInfoThreadDoneBase):

    def __init__(self):
        super().__init__(False, True, "マイリスト内容更新")
        self.L_KIND = "Mylist"


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()()
    mw.run()
