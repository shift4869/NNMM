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


def IsMylistIncludeNewMovie(table_list):
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


def UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url):
    # 右上のテキストボックスにマイリストのURLがあるとき限定(window["-INPUT1-"])
    # mylist_url = window["-INPUT1-"].get()
    # MylistInfoからロード
    record = mylist_db.SelectFromURL(mylist_url)[0]

    # usernameだと重複するかも(TODO)
    username = record.get("username")
    m_list = mylist_info_db.SelectFromUsername(username)
    def_data = []
    for i, m in enumerate(m_list):
        a = [i + 1, m["video_id"], m["title"], m["username"], m["status"], m["uploaded_at"]]
        def_data.append(a)
    window["-TABLE-"].update(values=def_data)
    pass


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
