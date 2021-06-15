# coding: utf-8
import logging.config
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def ProcessWatchedAllMylist(window: sg.Window, values: dict, mylist_db: MylistDBController, mylist_info_db: MylistInfoDBController):
    # マイリスト右クリックで「視聴済にする（全て）」が選択された場合
    pass
    

if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
