# coding: utf-8
import asyncio
import logging.config
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import GetMyListInfo
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *


def IsMylistIncludeNewVideo(table_list):
    """現在のテーブルリスト内に状況が未視聴のものが一つでも含まれているかを返す

    Args:
        table_list (list[list]): 現在のテーブルリスト

    Returns:
        boolean: 一つでも未視聴のものがあればTrue, そうでないならFalse
    """
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "URL"]
    for t in table_list:
        if t[4] == "未視聴":
            return True
    return False


def UpdateMylistShow(window, mylist_db):
    # マイリスト画面表示更新
    list_data = window["-LIST-"].Values
    m_list = mylist_db.Select()
    for m in m_list:
        if m["is_include_new"]:
            m["listname"] = "*:" + m["listname"]
    list_data = [m["listname"] for m in m_list]
    window["-LIST-"].update(values=list_data)
    return 0


def UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url=""):
    # 右上のテキストボックスにマイリストのURLがあるとき限定(window["-INPUT1-"])
    # 現在のマイリストURL
    if mylist_url == "":
        mylist_url = window["-INPUT1-"].get()
    
    if mylist_url == "":
        return -1

    # 現在のマイリストURLからlistboxのindexを求める
    index = 0
    m_list = mylist_db.Select()
    mylist_url_list = [m["url"] for m in m_list]
    for i, url in enumerate(mylist_url_list):
        if mylist_url == url:
            index = i
            break

    # 現在のマイリストURLからテーブル情報を求める
    records = mylist_info_db.SelectFromMylistURL(mylist_url)
    def_data = []
    for i, m in enumerate(records):
        a = [i + 1, m["video_id"], m["title"], m["username"], m["status"], m["uploaded_at"]]
        def_data.append(a)

    # 画面更新
    window["-TABLE-"].update(values=def_data)
    window["-LIST-"].update(set_to_index=index)
    pass


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
