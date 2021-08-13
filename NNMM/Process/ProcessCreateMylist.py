# coding: utf-8
import asyncio
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase
from NNMM import GetMyListInfo


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessCreateMylist(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, False, "マイリスト追加")

    def Run(self, mw):
        # "-CREATE-"
        # 左下、マイリスト追加ボタンが押された場合
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # 現在のマイリストURL
        mylist_url = self.values["-INPUT1-"]

        # 右上のテキストボックスにも左下のテキストボックスにも
        # URLが入力されていない場合何もしない
        if mylist_url == "":
            mylist_url = self.values["-INPUT2-"]
            if mylist_url == "":
                return

        # 既存マイリストと重複していた場合何もしない
        prev_mylist = self.mylist_db.SelectFromURL(mylist_url)
        if prev_mylist:
            return

        # 入力されたurlが対応したタイプでない場合何もしない
        url_type = GetURLType(mylist_url)
        if url_type == "":
            return

        # 確認
        # res = sg.popup_ok_cancel(mylist_url + "\nマイリスト追加しますか？")
        # if res == "Cancel":
        #     return

        # マイリスト情報収集
        # 右ペインのテーブルに表示するマイリスト情報を取得
        self.window["-INPUT2-"].update(value="ロード中")
        self.window.refresh()
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url"]
        # async
        loop = asyncio.new_event_loop()
        now_video_list = loop.run_until_complete(GetMyListInfo.AsyncGetMyListInfo(mylist_url))
        s_record = now_video_list[0]
        self.window["-INPUT2-"].update(value="")

        # 新規マイリスト追加
        username = s_record["username"]
        showname = s_record["showname"]
        is_include_new = True

        td_format = "%Y/%m/%d %H:%M"
        dts_format = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now().strftime(dts_format)

        # id_index = len(mylist_db.Select()) + 1
        id_index = max([int(r["id"]) for r in self.mylist_db.Select()]) + 1
        self.mylist_db.Upsert(id_index, username, url_type, showname, mylist_url, dst, dst, is_include_new)

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
        self.mylist_info_db.UpsertFromList(records)

        # 後続処理へ
        self.window.write_event_value("-CREATE_THREAD_DONE-", "")


class ProcessCreateMylistThreadDone(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, True, "マイリスト追加")

    def Run(self, mw):
        # -CREATE-のマルチスレッド処理が終わった後の処理
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
