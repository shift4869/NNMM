# coding: utf-8
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process.ProcessUpdateMylistInfo import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessUpdateAllMylistInfo(ProcessUpdateMylistInfo):

    def __init__(self):
        super().__init__(True, False, "全マイリスト内容更新")

        # ログメッセージ
        self.L_START = "All mylist update starting."
        self.L_GETTING_ELAPSED_TIME = "All getting done elapsed time"
        self.L_UPDATE_ELAPSED_TIME = "All update done elapsed time"

        # イベントキー
        self.E_PROGRESS = "-ALL_UPDATE_THREAD_PROGRESS-"
        self.E_DONE = "-ALL_UPDATE_THREAD_DONE-"

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
        logger.info(self.L_START)

        # 登録されたすべてのマイリストから現在のマイリスト情報を取得する
        # 処理中もGUIイベントを処理するため別スレッドで起動
        threading.Thread(target=self.UpdateMylistInfoThread,
                         args=(), daemon=True).start()

    def GetTargetMylist(self):
        """更新対象のマイリストを返す

        Note:
            ProcessUpdateAllMylistInfoにおいては対象はすべてのマイリストとなる
            派生クラスでこのメソッドをオーバーライドして対象を調整する

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト
        """
        m_list = self.mylist_db.Select()
        return m_list

    def GetFunctionList(self, m_list):
        """それぞれのマイリストごとに初回ロードか確認し、
           簡易版かレンダリング版かどちらで更新するかをリストで返す

        Args:
            m_list (list[Mylist]): マイリストレコードオブジェクトのリスト
                                   mylist_db.Select系の返り値

        Returns:
            list[Function]: それぞれのマイリストを更新するためのメソッドリスト
        """
        func_list = []
        for record in m_list:
            mylist_url = record.get("url")
            prev_video_list = self.mylist_info_db.SelectFromMylistURL(mylist_url)
            if not prev_video_list:
                # 初めての動画情報取得ならページをレンダリングして取得
                func_list.append(GetMyListInfo.AsyncGetMyListInfo)
            else:
                # 既に動画情報が存在するならRSSから取得
                func_list.append(GetMyListInfo.AsyncGetMyListInfoLightWeight)
        return func_list

    def GetPrevVideoLists(self, m_list):
        """それぞれのマイリストごとに既存のレコードを取得する

        Args:
            m_list (list[Mylist]): マイリストレコードオブジェクトのリスト
                                   mylist_db.Select系の返り値

        Returns:
            list[list[MylistInfo]]: それぞれのマイリストに含まれる動画情報のリストのリスト
        """
        prev_video_lists = []
        for record in m_list:
            mylist_url = record.get("url")
            prev_video_list = self.mylist_info_db.SelectFromMylistURL(mylist_url)
            prev_video_lists.append(prev_video_list)
        return prev_video_lists

    def GetMylistInfoExecute(self, func_list, m_list):
        """それぞれのマイリストを引数に動画情報を取得する

        Args:
            func_list (list[Function]): それぞれのマイリストを更新するためのメソッドリスト
            m_list (list[Mylist]): マイリストレコードオブジェクトのリスト
                                   mylist_db.Select系の返り値

        Returns:
            list[list[MylistInfo]]: それぞれのマイリストについて取得した動画情報のリストのリスト
        """
        result = []
        all_index_num = len(m_list)
        with ThreadPoolExecutor(max_workers=4, thread_name_prefix="ap_thread") as executor:
            futures = []
            for func, record in zip(func_list, m_list):
                mylist_url = record.get("url")
                future = executor.submit(self.GetMylistInfoWorker, func, mylist_url, all_index_num)
                futures.append((mylist_url, future))
            result = [(f[0], f[1].result()) for f in futures]
        return result

    def GetMylistInfoWorker(self, func, url, all_index_num):
        self.done_count = self.done_count + 1

        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(func(url))

        p_str = f"取得中({self.done_count}/{all_index_num})"
        self.window.write_event_value(self.E_PROGRESS, p_str)
        logger.info(url + f" : getting done ... ({self.done_count}/{all_index_num}).")
        return res

    def UpdateMylistInfoExecute(self, m_list, prev_video_lists, now_video_lists):
        """それぞれのマイリスト情報を更新する

        Args:
            m_list (list[Mylist]): マイリストレコードオブジェクトのリスト
                                   mylist_db.Select系の返り値
            prev_video_lists (list[list[MylistInfo]]): それぞれのマイリストに含まれる動画情報のリストのリスト
            now_video_lists (list[list[MylistInfo]]): それぞれのマイリストについて取得した動画情報のリストのリスト

        Returns:
            list[int]: それぞれのマイリストについて動画情報を更新した際の結果のリスト
                       成功で0, 失敗で-1が格納される
        """
        result_buf = []
        with ThreadPoolExecutor(max_workers=8, thread_name_prefix="np_thread") as executor:
            futures = []
            for m, prev_video_list in zip(m_list, prev_video_lists):
                future = executor.submit(self.UpdateMylistInfoWorker, m, prev_video_list, now_video_lists)
                futures.append((m.get("url"), future))
            result_buf = [(f[0], f[1].result()) for f in futures]
        return result_buf

    def UpdateMylistInfoWorker(self, m, prev_video_list, now_video_lists):
        # マルチスレッド内では各々のスレッドごとに新しくDBセッションを張る
        mylist_db = MylistDBController(self.mylist_db.dbname)
        mylist_info_db = MylistInfoDBController(self.mylist_info_db.dbname)
        self.done_count = self.done_count + 1

        mylist_url = m.get("url")
        records = [r[1] for r in now_video_lists if r[0] == mylist_url]
        if len(records) == 1:
            records = records[0]
        else:
            # error
            return -1

        if len(records) == 0:
            # error
            # 新規マイリスト取得でレンダリングが失敗した場合など
            return -1

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
                mylist_db.UpdateUsername(mylist_url, now_username)
                # 格納済の動画情報の投稿者名を更新する
                mylist_info_db.UpdateUsernameInMylist(mylist_url, now_username)

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
        mylist_info_db.UpsertFromList(records)

        # マイリストの更新確認日時更新
        # 新しい動画情報が追加されたかに関わらずchecked_atを更新する
        dst = GetNowDatetime()
        mylist_db.UpdateCheckdAt(mylist_url, dst)

        # マイリストの更新日時更新
        # 新しい動画情報が追加されたときにupdated_atを更新する
        if add_new_video_flag:
            dst = GetNowDatetime()
            mylist_db.UpdateUpdatedAt(mylist_url, dst)

        # プログレス表示
        all_index_num = len(now_video_lists)
        p_str = f"更新中({self.done_count}/{all_index_num})"
        self.window.write_event_value(self.E_PROGRESS, p_str)
        logger.info(mylist_url + f" : update done ... ({self.done_count}/{all_index_num}).")
        return 0

    def UpdateMylistInfoThread(self):
        # 全てのマイリストを更新する（マルチスレッド前提）

        # それぞれのマイリストごとに初回ロードか確認し、
        # 簡易版かレンダリングかどちらで更新するかを保持する
        m_list = self.GetTargetMylist()
        func_list = self.GetFunctionList(m_list)
        prev_video_lists = self.GetPrevVideoLists(m_list)

        # マルチスレッドですべてのマイリストの情報を取得する
        # now_video_listsにすべてのthreadの結果を格納して以降で利用する
        start = time.time()
        self.done_count = 0
        now_video_lists = self.GetMylistInfoExecute(func_list, m_list)
        elapsed_time = time.time() - start
        logger.info(f"{self.L_GETTING_ELAPSED_TIME} : {elapsed_time:.2f} [sec]")

        # マルチスレッドですべてのマイリストの情報を更新する
        start = time.time()
        self.done_count = 0
        result = self.UpdateMylistInfoExecute(m_list, prev_video_lists, now_video_lists)
        elapsed_time = time.time() - start
        logger.info(f"{self.L_UPDATE_ELAPSED_TIME} : {elapsed_time:.2f} [sec]")

        self.window.write_event_value(self.E_DONE, "")


class ProcessUpdateAllMylistInfoThreadProgress(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, False, "全マイリスト内容更新")

        # イベントキー
        self.E_PROGRESS = "-ALL_UPDATE_THREAD_PROGRESS-"

    def Run(self, mw):
        # -ALL_UPDATE_THREAD_PROGRESS-
        # -ALL_UPDATE-処理中のプログレス
        self.window = mw.window
        self.values = mw.values
        p_str = self.values[self.E_PROGRESS]
        self.window["-INPUT2-"].update(value=p_str)


class ProcessUpdateAllMylistInfoThreadDone(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, True, "全マイリスト内容更新")

        # ログメッセージ
        self.L_FINISH = "All mylist update finished."

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

        logger.info(self.L_FINISH)


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
