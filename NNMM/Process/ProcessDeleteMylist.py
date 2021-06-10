# coding: utf-8
import asyncio
import logging.config
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def ProcessDeleteMylist(window, values, mylist_db, mylist_info_db):
    # 左下、マイリスト追加ボタンが押された場合
    # 現在のマイリストURL
    mylist_url = values["-INPUT1-"]

    # 右上のテキストボックスにも左下のテキストボックスにも
    # URLが入力されていない場合何もしない
    if mylist_url == "":
        mylist_url = values["-INPUT2-"]
        if mylist_url == "":
            return

    # 既存マイリストと重複していない場合何もしない
    prev_mylist = mylist_db.SelectFromURL(mylist_url)[0]
    if not prev_mylist:
        return

    # 確認
    # res = sg.popup_ok_cancel(mylist_url + "\nマイリスト削除しますか？")
    # if res == "Cancel":
    #     return

    # マイリスト情報から対象動画の情報を削除する
    mylist_info_db.DeleteFromMylistURL(mylist_url)

    # マイリストからも削除する
    mylist_db.DeleteFromURL(mylist_url)

    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)

    # マイリスト情報テーブルの表示を初期化する
    window["-TABLE-"].update(values=[[]])

    # 後続処理へ
    # window.write_event_value("-DELETE_THREAD_DONE-", "")


def ProcessDeleteMylistThreadDone(window, values, mylist_db, mylist_info_db):
    # -CREATE-のマルチスレッド処理が終わった後の処理
    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)

    # テーブルの表示を更新する
    mylist_url = ""
    window["-TABLE-"].update(values=[[]])


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
