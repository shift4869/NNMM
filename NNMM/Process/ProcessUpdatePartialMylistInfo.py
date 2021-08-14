# coding: utf-8
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process.ProcessUpdateMylistInfo import *
from NNMM.Process.ProcessUpdateAllMylistInfo import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessUpdatePartialMylistInfo(ProcessUpdateAllMylistInfo):

    def __init__(self):
        super().__init__()

        # ログメッセージ
        self.L_START = "Partial mylist update starting."
        self.L_GETTING_ELAPSED_TIME = "Partial getting done elapsed time"
        self.L_UPDATE_ELAPSED_TIME = "Partial update done elapsed time"

        # イベントキー
        self.E_PROGRESS = "-PARTIAL_UPDATE_THREAD_PROGRESS-"
        self.E_DONE = "-PARTIAL_UPDATE_THREAD_DONE-"

    def GetTargetMylist(self):
        """更新対象のマイリストを返す

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト
        """
        m_list = self.mylist_db.Select()[0:16]
        return m_list


class ProcessUpdatePartialMylistInfoThreadProgress(ProcessUpdateAllMylistInfoThreadProgress):

    def __init__(self):
        super().__init__()

        # イベントキー
        self.E_PROGRESS = "-PARTIAL_UPDATE_THREAD_PROGRESS-"


class ProcessUpdatePartialMylistInfoThreadDone(ProcessUpdateAllMylistInfoThreadDone):

    def __init__(self):
        super().__init__()

        # ログメッセージ
        self.L_FINISH = "Partial mylist update finished."


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
