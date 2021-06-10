# coding: utf-8
import logging.config
import threading
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


def UpdateMylistInfo(window, mylist_db, mylist_info_db, record):
    # マイリストを更新する（マルチスレッド前提）
    mylist_url = record.get("url")
    print(mylist_url)

    # DBからロード
    prev_video_list = mylist_info_db.SelectFromMylistURL(mylist_url)
    prev_videoid_list = [m["video_id"] for m in prev_video_list]

    func = None
    if not prev_videoid_list:
        # 初回読み込みなら最大100件取れる代わりに遅いこちら
        func = GetMyListInfo.AsyncGetMyListInfo
    else:
        # 既に動画情報が存在しているなら速い代わりに最大30件まで取れるこちら
        func = GetMyListInfo.AsyncGetMyListInfoLightWeight

    # 右ペインのテーブルに表示するマイリスト情報を取得
    def_data = []
    table_cols = ["no", "id", "title", "username", "status", "uploaded", "video_url"]

    # マルチスレッド開始
    loop = asyncio.new_event_loop()
    now_video_list = loop.run_until_complete(func(mylist_url))
    now_videoid_list = [m["video_id"] for m in now_video_list]

    # window["-INPUT2-"].update(value="")

    # 状況ステータスを調べる
    status_check_list = []
    for i, n in enumerate(now_videoid_list):
        if n in prev_videoid_list:
            s = [p["status"] for p in prev_video_list if p["video_id"] == n]
            status_check_list.append(s[0])
        else:
            status_check_list.append("未視聴")

    # 右ペインのテーブルにマイリスト情報を表示
    for m, s in zip(now_video_list, status_check_list):
        m["status"] = s
        a = [m["no"], m["video_id"], m["title"], m["username"], m["status"], m["uploaded"]]
        def_data.append(a)
    if window["-INPUT1-"].get() == mylist_url:
        now_show_table_data = list[def_data]

    # DBに格納
    records = []
    for m in now_video_list:
        td_format = "%Y/%m/%d %H:%M"
        dts_format = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now().strftime(dts_format)

        # usernameが変更されていた場合、既存のレコードも含めてすべて更新する必要がある(TODO)
        r = {
            "video_id": m["video_id"],
            "title": m["title"],
            "username": m["username"],
            "status": m["status"],
            "uploaded_at": m["uploaded"],
            "video_url": m["video_url"],
            "mylist_url": m["mylist_url"],
            "created_at": dst
        }
        records.append(r)
    mylist_info_db.UpsertFromList(records)


def UpdateMylistInfoThread(window, mylist_db, mylist_info_db, record):
    # マイリストを更新する（マルチスレッド前提）
    UpdateMylistInfo(window, mylist_db, mylist_info_db, record)
    window.write_event_value("-UPDATE_THREAD_DONE-", "")


def ProcessUpdateMylistInfo(window, values, mylist_db, mylist_info_db):
    # 右上の更新ボタンが押された場合
    mylist_url = values["-INPUT1-"]

    # 左下の表示変更
    window["-INPUT2-"].update(value="更新中")
    window.refresh()

    # マイリストレコードから現在のマイリスト情報を取得する
    # AsyncHTMLSessionでページ情報をレンダリングして解釈する
    # マルチスレッド処理
    record = mylist_db.SelectFromURL(mylist_url)[0]
    threading.Thread(target=UpdateMylistInfoThread, args=(window, mylist_db, mylist_info_db, record), daemon=True).start()


def ProcessUpdateMylistInfoThreadDone(window, values, mylist_db, mylist_info_db):
    # -UPDATE-のマルチスレッド処理が終わった後の処理
    # 左下の表示を戻す
    window["-INPUT2-"].update(value="更新完了！")

    # テーブルの表示を更新する
    mylist_url = values["-INPUT1-"]
    if mylist_url != "":
        UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)
    window.refresh()
    
    # マイリストの新着表示を表示するかどうか判定する
    def_data = window["-TABLE-"].Values  # 現在のtableの全リスト

    # 左のマイリストlistboxの表示を更新する
    # 一つでも未視聴の動画が含まれる場合はマイリストの進捗フラグを立てる
    if IsMylistIncludeNewVideo(def_data):
        # 新着フラグを更新
        mylist_db.UpdateIncludeFlag(mylist_url, True)

    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
