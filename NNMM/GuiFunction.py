# coding: utf-8
import re
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import GetMyListInfo
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *


logger = getLogger("root")
logger.setLevel(INFO)


def GetURLType(url: str) -> str:
    """マイリストのタイプを返す

    Args:
        url (str): 判定対象URL

    Returns:
        str: マイリストのタイプ
             "uploaded": 投稿動画
             "mylist": 通常のマイリスト
    """
    url_type = ""
    p_uploaded = "^https://www.nicovideo.jp/user/[0-9]+/video$"
    p_mylist = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
    if re.search(p_uploaded, url):
        url_type = "uploaded"
    elif re.search(p_mylist, url):
        url_type = "mylist"

    return url_type


def GetNowDatetime() -> str:
    """タイムスタンプを返す

    Returns:
        str: 現在日時 "%Y-%m-%d %H:%M:%S" 形式
    """
    td_format = "%Y/%m/%d %H:%M"
    dts_format = "%Y-%m-%d %H:%M:%S"
    dst = datetime.now().strftime(dts_format)
    return dst


def IsMylistIncludeNewVideo(table_list: list):
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


def UpdateMylistShow(window: sg.Window, mylist_db: MylistDBController):
    # 現在マイリストが選択中の場合indexを保存
    index = 0
    if window["-LIST-"].get_indexes():
        index = window["-LIST-"].get_indexes()[0]

    # マイリスト画面表示更新
    NEW_MARK = "*:"
    list_data = window["-LIST-"].Values
    m_list = mylist_db.Select()
    include_new_index_list = []
    for i, m in enumerate(m_list):
        if m["is_include_new"]:
            m["listname"] = NEW_MARK + m["listname"]
            include_new_index_list.append(i)
    list_data = [m["listname"] for m in m_list]
    window["-LIST-"].update(values=list_data)

    # 新着マイリストの背景色とテキスト色を変更する
    # update(values=list_data)で更新されるとデフォルトに戻る？
    # 強調したいindexのみ適用すればそれ以外はデフォルトになる
    for i in include_new_index_list:
        window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

    # indexをセットしてスクロール
    # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
    # window["-LIST-"].update(scroll_to_index=index)
    window["-LIST-"].Widget.see(index)
    window["-LIST-"].update(set_to_index=index)
    return 0


def UpdateTableShow(window: sg.Window, mylist_db: MylistDBController, mylist_info_db: MylistInfoDBController, mylist_url: str = ""):
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
    window["-TABLE-"].update(select_rows=[0])
    window["-LIST-"].update(set_to_index=index)
    pass


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
