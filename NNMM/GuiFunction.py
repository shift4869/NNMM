# coding: utf-8
import asyncio
import logging.config
import time
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import GuiMain
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


def UpdateTableShow(window, mylist_db, mylist_info_db):
    # 右上のテキストボックスにマイリストのURLがあるとき限定(window["-INPUT1-"])
    mylist_url = window["-INPUT1-"].get()
    # MylistInfoからロード
    record = mylist_db.SelectFromURL(mylist_url)[0]

    # usernameだと重複するかも(TODO)
    username = record.get("username")
    m_list = mylist_info_db.SelectFromUsername(username)
    def_data = []
    for i, m in enumerate(m_list):
        a = [i + 1, m["movie_id"], m["title"], m["username"], m["status"], m["uploaded_at"]]
        def_data.append(a)
    window["-TABLE-"].update(values=def_data)
    pass


def UpdateAllMylistInfo(window, mylist_db, mylist_info_db):
    # 全てのマイリストを更新する（マルチスレッド前提）
    m_list = mylist_db.Select()
    now_show_table_data = []
    for record in m_list:
        mylist_url = record.get("url")
        print(mylist_url)

        # DBからロード
        username = record.get("username")
        prev_movie_list = mylist_info_db.SelectFromUsername(username)
        prev_movieid_list = [m["movie_id"] for m in prev_movie_list]

        # 右ペインのテーブルに表示するマイリスト情報を取得
        def_data = []
        table_cols = ["no", "id", "title", "username", "status", "uploaded", "url"]
        
        loop = asyncio.new_event_loop()
        now_movie_list = loop.run_until_complete(GetMyListInfo.AsyncGetMyListInfo(mylist_url))
        now_movieid_list = [m["movie_id"] for m in now_movie_list]

        # window["-INPUT2-"].update(value="")

        # 状況ステータスを調べる
        status_check_list = []
        for i, n in enumerate(now_movieid_list):
            if n in prev_movieid_list:
                s = [p["status"] for p in prev_movie_list if p["movie_id"] == n]
                status_check_list.append(s[0])
            else:
                status_check_list.append("未視聴")

        # 右ペインのテーブルにマイリスト情報を表示
        for m, s in zip(now_movie_list, status_check_list):
            m["status"] = s
            a = [m["no"], m["movie_id"], m["title"], m["username"], m["status"], m["uploaded"]]
            def_data.append(a)
        if window["-INPUT1-"].get() == mylist_url:
            now_show_table_data = list[def_data]

        # DBに格納
        for m in now_movie_list:
            movie_id = m["movie_id"]
            title = m["title"]
            username = m["username"]
            status = m["status"]
            uploaded_at = m["uploaded"]
            url = m["url"]

            td_format = "%Y/%m/%d %H:%M"
            dts_format = "%Y-%m-%d %H:%M:%S"
            dst = datetime.now().strftime(dts_format)
            created_at = dst
            mylist_info_db.Upsert(movie_id, title, username, status, uploaded_at, url, created_at)

        # 左のマイリストlistboxの表示を更新する
        # 一つでも未視聴の動画が含まれる場合はマイリストに進捗マークを追加する
        if IsMylistIncludeNewMovie(def_data):
            # マイリストDB更新
            record["is_include_new"] = True  # 新着マークを更新
            # record["listname"] = record["listname"][2:]  # *:を削除
            mylist_db.Upsert(record["username"], record["type"], record["listname"],
                             record["url"], record["created_at"], record["is_include_new"])

            # マイリスト画面表示更新
            UpdateMylistShow(window, mylist_db)
            pass
        pass

    # if now_show_table_data:
    #     window["-TABLE-"].update(values=now_show_table_data)
    window.write_event_value("-THREAD_DONE-", "")


if __name__ == "__main__":
    GuiMain.GuiMain()
