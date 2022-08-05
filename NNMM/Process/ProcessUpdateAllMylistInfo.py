# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg
from NNMM.GuiFunction import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.Process import ProcessUpdateMylistInfoBase

logger = getLogger("root")
logger.setLevel(INFO)


class ProcessUpdateAllMylistInfo(ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase):

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

    def GetTargetMylist(self) -> list[Mylist]:
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

        m_list = self.mylist_db.Select()
        return m_list


class ProcessUpdateAllMylistInfoThreadDone(ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoThreadDoneBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        super().__init__(False, True, "全マイリスト内容更新")
        self.L_KIND = "All mylist"


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
