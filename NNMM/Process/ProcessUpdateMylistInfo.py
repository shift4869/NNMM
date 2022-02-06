# coding: utf-8
import asyncio
import threading
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM import GetMyListInfo
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessUpdateMylistInfo(ProcessBase.ProcessBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        # 派生クラス（すべて更新時）の生成時は引数ありで呼び出される
        if process_name:
            super().__init__(log_sflag, log_eflag, process_name)
        else:
            super().__init__(True, False, "マイリスト内容更新")

    def Run(self, mw):
        # "-UPDATE-"
        # 右上の更新ボタンが押された場合
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db
        mylist_url = self.values["-INPUT1-"]

        # TODO::入力チェック
        if mylist_url == "":
            return

        # 左下の表示変更
        self.window["-INPUT2-"].update(value="更新中")
        self.window.refresh()

        # マイリストレコードから現在のマイリスト情報を取得する
        # AsyncHTMLSessionでページ情報をレンダリングして解釈する
        # マルチスレッド処理
        record = self.mylist_db.SelectFromURL(mylist_url)[0]
        threading.Thread(target=self.UpdateMylistInfoThread, args=(record, ), daemon=True).start()

    def UpdateMylistInfoThread(self, record):
        # マイリストを更新する（マルチスレッド前提）
        self.UpdateMylistInfo(record)
        self.window.write_event_value("-UPDATE_THREAD_DONE-", "")

    def UpdateMylistInfo(self, record: Mylist):
        # マイリストを更新する（マルチスレッド前提）
        mylist_url = record.get("url")

        # DBからロード
        prev_video_list = self.mylist_info_db.SelectFromMylistURL(mylist_url)
        prev_videoid_list = [m["video_id"] for m in prev_video_list]
        prev_username = ""
        if prev_video_list:
            prev_username = prev_video_list[0].get("username")

        func = None
        if not prev_videoid_list:
            # 初回読み込みなら最大100件取れる代わりに遅いこちら
            func = GetMyListInfo.AsyncGetMyListInfo
        else:
            # 既に動画情報が存在しているなら速い代わりに最大30件まで取れるこちら
            func = GetMyListInfo.AsyncGetMyListInfoLightWeight

        # 右ペインのテーブルに表示するマイリスト情報を取得
        def_data = []
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "id", "title", "username", "status", "uploaded", "video_url", "mylist_url"]

        # マルチスレッド開始
        loop = asyncio.new_event_loop()
        now_video_list = loop.run_until_complete(func(mylist_url))
        now_videoid_list = [m["video_id"] for m in now_video_list]

        # 状況ステータスを調べる
        status_check_list = []
        add_new_video_flag = False
        for i, n in enumerate(now_videoid_list):
            if n in prev_videoid_list:
                # 以前から保持していた動画が取得された場合
                s = [p["status"] for p in prev_video_list if p["video_id"] == n]
                status_check_list.append(s[0])
            else:
                # 新規に動画が追加された場合
                status_check_list.append("未視聴")
                add_new_video_flag = True

        # 右ペインのテーブルにマイリスト情報を表示
        for m, s in zip(now_video_list, status_check_list):
            m["status"] = s
            a = [m["no"], m["video_id"], m["title"], m["username"], m["status"], m["uploaded"], m["video_url"], m["mylist_url"]]
            def_data.append(a)
        if self.window["-INPUT1-"].get() == mylist_url:
            now_show_table_data = list[def_data]

        # usernameが変更されていた場合
        if now_video_list:
            now_username = now_video_list[0].get("username")
            if prev_username != now_username:
                # マイリストの名前を更新する
                self.mylist_db.UpdateUsername(mylist_url, now_username)
                # 格納済の動画情報の投稿者名を更新する
                self.mylist_info_db.UpdateUsernameInMylist(mylist_url, now_username)

        # DBに格納
        records = []
        for m in now_video_list:
            dst = GetNowDatetime()
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
        self.mylist_info_db.UpsertFromList(records)

        # マイリストの更新確認日時更新
        # 新しい動画情報が追加されたかに関わらずchecked_atを更新する
        dst = GetNowDatetime()
        self.mylist_db.UpdateCheckedAt(mylist_url, dst)

        # マイリストの更新日時更新
        # 新しい動画情報が追加されたときにupdated_atを更新する
        if add_new_video_flag:
            dst = GetNowDatetime()
            self.mylist_db.UpdateUpdatedAt(mylist_url, dst)


class ProcessUpdateMylistInfoThreadDone(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, True, "マイリスト内容更新")

    def Run(self, mw):
        # -UPDATE-のマルチスレッド処理が終わった後の処理
        window = mw.window
        values = mw.values
        mylist_db = mw.mylist_db
        mylist_info_db = mw.mylist_info_db
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

        logger.info(mylist_url + " : update done.")


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
