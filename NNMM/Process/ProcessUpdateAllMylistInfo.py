# coding: utf-8
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.MultiDBController import *
from NNMM.GuiFunction import *
from NNMM.Process.ProcessUpdateMylistInfo import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessUpdateAllMylistInfo(ProcessUpdateMylistInfo):

    def __init__(self):
        super().__init__(True, False, "全マイリスト内容更新")

    def Run(self, mw):
        # -ALL_UPDATE-
        # 左下のすべて更新ボタンが押された場合
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        self.done_count = 0

        self.window["-INPUT2-"].update(value="更新中")
        self.window.refresh()
        logger.info("All mylist update starting.")
        # 登録されたすべてのマイリストから現在のマイリスト情報を取得する
        # マルチスレッド処理
        threading.Thread(target=self.UpdateAllMylistInfoThread,
                         args=(), daemon=True).start()

    def GetMylistInfoExecute(self, func, url, all_index_num):
        # logger.info(url + ":start")
        self.done_count = self.done_count + 1

        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(func(url))

        p_str = f"取得中({self.done_count}/{all_index_num})"
        self.window.write_event_value("-ALL_UPDATE_THREAD_PROGRESS-", p_str)
        logger.info(url + f" : getting done ... ({self.done_count}/{all_index_num}).")
        # logger.info(url + ":end")
        return res

    def UpdateAllMylistInfoThread(self):
        # 全てのマイリストを更新する（マルチスレッド前提）

        # それぞれのマイリストごとに初回ロードか確認し、
        # 簡易版かレンダリングかどちらで更新するかを保持する
        m_list = self.mylist_db.Select()
        all_index_num = len(m_list)
        func_list = []
        prev_video_lists = []
        for i, record in enumerate(m_list):
            mylist_url = record.get("url")
            prev_video_list = self.mylist_info_db.SelectFromMylistURL(mylist_url)
            if not prev_video_list:
                # func_list.append(GetMyListInfo.GetMyListInfo)  # 失敗する・・？
                func_list.append(GetMyListInfo.AsyncGetMyListInfo)
            else:
                func_list.append(GetMyListInfo.AsyncGetMyListInfoLightWeight)
            prev_video_lists.append(prev_video_list)

        # マルチスレッドですべてのマイリストの情報を取得する
        # resultにすべてのthreadの結果を格納して以下で利用する
        result = []
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="ap_thread") as executor:
            futures = []
            for func, record in zip(func_list, m_list):
                mylist_url = record.get("url")
                future = executor.submit(self.GetMylistInfoExecute, func, mylist_url, all_index_num)
                futures.append((mylist_url, future))
            result = [(f[0], f[1].result()) for f in futures]

        # すべてのマイリストの情報を更新する
        self.done_count = 0
        self.old_mylist_db = self.mylist_db
        self.old_mylist_info_db = self.mylist_info_db
        self.mylist_db = MylistDBCM(self.mylist_db.dbname)
        self.mylist_info_db = MylistInfoDBCM(self.mylist_info_db.dbname)

        for m, prev_video_list in zip(m_list, prev_video_lists):
            self.Working(m, prev_video_list, result)

        self.mylist_db = self.old_mylist_db
        self.mylist_info_db = self.old_mylist_info_db

        self.window.write_event_value("-ALL_UPDATE_THREAD_DONE-", "")

    def Working(self, m, prev_video_list, now_video_lists):
        mylist_url = m.get("url")
        records = [r[1] for r in now_video_lists if r[0] == mylist_url]
        if len(records) == 1:
            records = records[0]
        else:
            # error
            return

        if len(records) == 0:
            # error
            # 新規マイリスト取得でレンダリングが失敗した場合など
            return

        # prev_video_list = self.mylist_info_db.SelectFromMylistURL(mylist_url)
        prev_videoid_list = [m["video_id"] for m in prev_video_list]
        prev_username = ""
        if prev_video_list:
            prev_username = prev_video_list[0].get("username")
        now_video_list = records
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

        # 右ペインのテーブルに表示するマイリスト情報を取得
        def_data = []
        table_cols = ["no", "id", "title", "username", "status", "uploaded", "video_url"]

        # 右ペインのテーブルにマイリスト情報を表示
        for m, s in zip(now_video_list, status_check_list):
            m["status"] = s
            a = [m["no"], m["video_id"], m["title"], m["username"], m["status"], m["uploaded"]]
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

        # マイリストの更新日時更新
        if add_new_video_flag:
            dst = GetNowDatetime()
            self.mylist_db.UpdateUpdatedAt(mylist_url, dst)

        self.done_count = self.done_count + 1
        all_index_num = len(now_video_lists)
        p_str = f"更新中({self.done_count}/{all_index_num})"
        self.window.write_event_value("-ALL_UPDATE_THREAD_PROGRESS-", p_str)
        logger.info(mylist_url + f" : update done ... ({self.done_count}/{all_index_num}).")
        return 0


class ProcessUpdateAllMylistInfoThreadProgress(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, False, "全マイリスト内容更新")

    def Run(self, mw):
        # -ALL_UPDATE_THREAD_PROGRESS-
        # -ALL_UPDATE-処理中のプログレス
        self.window = mw.window
        self.values = mw.values
        p_str = self.values["-ALL_UPDATE_THREAD_PROGRESS-"]
        self.window["-INPUT2-"].update(value=p_str)


class ProcessUpdateAllMylistInfoThreadDone(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, True, "全マイリスト内容更新")

    def Run(self, mw):
        # -ALL_UPDATE_THREAD_DONE-
        # -ALL_UPDATE-のマルチスレッド処理が終わった後の処理
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # 左下の表示を戻す
        self.window["-INPUT2-"].update(value="更新完了！")

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        if mylist_url != "":
            UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        # マイリストの新着表示を表示するかどうか判定する
        m_list = self.mylist_db.Select()
        for m in m_list:
            username = m["username"]
            mylist_url = m["url"]
            video_list = self.mylist_info_db.SelectFromMylistURL(mylist_url)
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時"]
            def_data = []
            for i, t in enumerate(video_list):
                a = [i + 1, t["video_id"], t["title"], t["username"], t["status"], t["uploaded_at"]]
                def_data.append(a)

            # 左のマイリストlistboxの表示を更新する
            # 一つでも未視聴の動画が含まれる場合はマイリストに進捗マークを追加する
            if IsMylistIncludeNewVideo(def_data):
                # マイリストDB更新
                self.mylist_db.UpdateIncludeFlag(mylist_url, True)

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)

        logger.info("All mylist update finished.")


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
