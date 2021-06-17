# coding: utf-8
import threading
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process.ProcessUpdateMylistInfo import *


logger = getLogger("root")
logger.setLevel(INFO)


def UpdateAllMylistInfoThread(window, mylist_db, mylist_info_db):
    # 全てのマイリストを更新する（マルチスレッド前提）
    m_list = mylist_db.Select()
    all_index_num = len(m_list)
    for i, record in enumerate(m_list):
        UpdateMylistInfo(window, mylist_db, mylist_info_db, record)
        p_str = f"更新中({i + 1}/{all_index_num})"
        window.write_event_value("-ALL_UPDATE_THREAD_PROGRESS-", p_str)

        mylist_url = record.get("url")
        logger.info(mylist_url + f" : update done ... ({i + 1}/{all_index_num}).")

    window.write_event_value("-ALL_UPDATE_THREAD_DONE-", "")


def ProcessUpdateAllMylistInfo(window, values, mylist_db, mylist_info_db):
    # 左下のすべて更新ボタンが押された場合
    window["-INPUT2-"].update(value="更新中")
    window.refresh()
    logger.info("All mylist update starting.")
    # 存在するすべてのマイリストから現在のマイリスト情報を取得する
    # AsyncHTMLSessionでページ情報をレンダリングして解釈する
    # マルチスレッド処理
    threading.Thread(target=UpdateAllMylistInfoThread,
                     args=(window, mylist_db, mylist_info_db), daemon=True).start()


def ProcessUpdateAllMylistInfoThreadProgress(window, values, mylist_db, mylist_info_db):
    # -ALL_UPDATE-処理中のプログレス
    p_str = values["-ALL_UPDATE_THREAD_PROGRESS-"]
    window["-INPUT2-"].update(value=p_str)


def ProcessUpdateAllMylistInfoThreadDone(window, values, mylist_db, mylist_info_db):
    # -ALL_UPDATE-のマルチスレッド処理が終わった後の処理
    # 左下の表示を戻す
    window["-INPUT2-"].update(value="更新完了！")

    # テーブルの表示を更新する
    mylist_url = values["-INPUT1-"]
    if mylist_url != "":
        UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)

    # マイリストの新着表示を表示するかどうか判定する
    m_list = mylist_db.Select()
    for m in m_list:
        username = m["username"]
        mylist_url = m["url"]
        video_list = mylist_info_db.SelectFromUsername(username)
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時"]
        def_data = []
        for i, t in enumerate(video_list):
            a = [i + 1, t["video_id"], t["title"], t["username"], t["status"], t["uploaded_at"]]
            def_data.append(a)

        # 左のマイリストlistboxの表示を更新する
        # 一つでも未視聴の動画が含まれる場合はマイリストに進捗マークを追加する
        if IsMylistIncludeNewVideo(def_data):
            # マイリストDB更新
            mylist_db.UpdateIncludeFlag(mylist_url, True)

    # マイリスト画面表示更新
    UpdateMylistShow(window, mylist_db)

    logger.info("All mylist update finished.")


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
