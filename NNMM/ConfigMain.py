# coding: utf-8
import logging.config
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg


def GetConfigLayout():
    # ブラウザ再生時のブラウザパス
    # オートリロード間隔
    # RSS保存パス
    # マイリスト保存
    # マイリスト読込
    # 設定ファイル保存パス
    # 設定ファイル読込
    layout = [[
        sg.Frame("Config", [
            [sg.Input()]
        ], size=(1070, 100))
    ]]
    return layout


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
