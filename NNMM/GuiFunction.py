# coding: utf-8
import re
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

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


def IntervalTranslation(interval_str: str) -> int:
    """インターバルを解釈する関数

    Note:
        次のいずれかにが想定されている
        ["n分","n時間","n日","n週間","nヶ月"]

    Args:
        interval_str (str): インターバルを表す文字列

    Returns:
        int: 成功時 分[min]を表す数値、失敗時 -1
    """
    pattern = "^([0-9]+)分$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0])

    pattern = "^([0-9]+)時間$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0]) * 60

    pattern = "^([0-9]+)日$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0]) * 60 * 24

    pattern = "^([0-9]+)週間$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0]) * 60 * 24 * 7

    pattern = "^([0-9]+)ヶ月$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0]) * 60 * 24 * 31  # 月は正確ではない28,29,30,31
    return -1


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
            m["showname"] = NEW_MARK + m["showname"]
            include_new_index_list.append(i)
    list_data = [m["showname"] for m in m_list]
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
    window["-LIST-"].update(set_to_index=index)
    window["-TABLE-"].update(values=def_data)
    if len(def_data) > 0:
        window["-TABLE-"].update(select_rows=[0])
    # 1行目は背景色がリセットされないので個別に指定してdefaultの色で上書き
    window["-TABLE-"].update(row_colors=[(0, "", "")])


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
