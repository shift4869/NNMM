from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.gui_function import *
from NNMM.mylist_db_controller import *
from NNMM.mylist_info_db_controller import *
from NNMM.process.process_update_mylist_info_base import ProcessUpdateMylistInfoBase, ProcessUpdateMylistInfoThreadDoneBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessUpdateAllMylistInfo(ProcessUpdateMylistInfoBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        """すべてのマイリストのマイリスト情報を更新するクラス

        Attributes:
            L_KIND (str): ログ出力用のメッセージベース
            E_DONE (str): 後続処理へのイベントキー
        """
        super().__init__(True, False, "全マイリスト内容更新")

        self.POST_PROCESS = ProcessUpdateAllMylistInfoThreadDone
        self.L_KIND = "All mylist"
        self.E_DONE = "-ALL_UPDATE_THREAD_DONE-"

    def get_target_mylist(self) -> list[Mylist]:
        """更新対象のマイリストを返す

        Note:
            ProcessUpdateAllMylistInfoにおいては対象はすべてのマイリストとなる

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        # 属性チェック
        if not hasattr(self, "mylist_db"):
            logger.error(f"{self.L_KIND} GetTargetMylist failed, attribute error.")
            return []

        m_list = self.mylist_db.select()
        return m_list


class ProcessUpdateAllMylistInfoThreadDone(ProcessUpdateMylistInfoThreadDoneBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        super().__init__(False, True, "全マイリスト内容更新")
        self.L_KIND = "All mylist"


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()()
    mw.run()
