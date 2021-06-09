# coding: utf-8
import asyncio
import logging.config
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def ProcessCreateMylist(window, values, mylist_db, mylist_info_db):
    # 左下、マイリスト追加ボタンが押された場合
    # 現在のマイリストURL
    mylist_url = values["-INPUT1-"]

    # 右上のテキストボックスにも左下のテキストボックスにも
    # URLが入力されていない場合何もしない
    if mylist_url == "":
        mylist_url = values["-INPUT2-"]
        if mylist_url == "":
            return

    # 既存マイリストと重複していた場合何もしない
    prev_mylist = mylist_db.SelectFromURL(mylist_url)
    if prev_mylist:
        return

    # 確認
    # res = sg.popup_ok_cancel(mylist_url + "\nマイリスト追加しますか？")
    # if res == "Cancel":
    #     return

    # マイリスト情報収集
    # 右ペインのテーブルに表示するマイリスト情報を取得
    window["-INPUT2-"].update(value="ロード中")
    window.refresh()
    table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url"]
    # async
    loop = asyncio.new_event_loop()
    now_video_list = loop.run_until_complete(GetMyListInfo.AsyncGetMyListInfo(mylist_url))
    s_record = now_video_list[0]
    window["-INPUT2-"].update(value="")

    # 新規マイリスト追加
    username = s_record["username"]
    type = "uploaded"  # タイプは投稿動画固定（TODO）
    listname = f"{username}さんの投稿動画"
    is_include_new = True

    td_format = "%Y/%m/%d %H:%M"
    dts_format = "%Y-%m-%d %H:%M:%S"
    dst = datetime.now().strftime(dts_format)

    mylist_db.Upsert(username, type, listname, mylist_url, dst, is_include_new)

    # DBに格納
    records = []
    td_format = "%Y/%m/%d %H:%M"
    dts_format = "%Y-%m-%d %H:%M:%S"
    for m in now_video_list:
        dst = datetime.now().strftime(dts_format)
        r = {
            "video_id": m["video_id"],
            "title": m["title"],
            "username": m["username"],
            "status": "未視聴",  # 初追加時はすべて未視聴扱い
            "uploaded_at": m["uploaded"],
            "video_url": m["video_url"],
            "mylist_url": m["mylist_url"],
            "created_at": dst,
        }
        records.append(r)
    mylist_info_db.UpsertFromList(records)

    # 後続処理へ
    window.write_event_value("-CREATE_THREAD_DONE-", "")


def ProcessCreateMylistThreadDone(window, values, mylist_db, mylist_info_db):
    # -CREATE-のマルチスレッド処理が終わった後の処理
    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)

    # テーブルの表示を更新する
    mylist_url = values["-INPUT1-"]
    UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
