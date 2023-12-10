import asyncio
import threading
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from logging import INFO, getLogger
from typing import Callable

from NNMM.gui_function import get_now_datetime, is_mylist_include_new_video, update_mylist_pane, update_table_pane
from NNMM.model import Mylist, MylistInfo
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_base import ProcessBase
from NNMM.video_info_fetcher.video_info_rss_fetcher import VideoInfoRssFetcher

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessUpdateMylistInfoBase(ProcessBase):
    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        """マイリストのマイリスト情報を更新するクラスのベース

        Notes:
            このクラスのインスタンスは直接作成・呼び出しは行わない
            このクラスの派生クラスはGetTargetMylist をオーバーライドする必要がある

        Attributes:
            lock (threading.Lock): マルチスレッドで使う排他ロック
            done_count (int): 処理対象について現在処理した数
            L_KIND (str): ログ出力用のメッセージベース
            E_DONE (str): 後続処理へのイベントキー
        """
        super().__init__(log_sflag, log_eflag, process_name)

        self.lock = threading.Lock()
        self.done_count = 0
        self.POST_PROCESS = ProcessUpdateMylistInfoThreadDoneBase
        self.L_KIND = "UpdateMylist Base"
        self.E_DONE = ""

    @abstractmethod
    def get_target_mylist(self) -> list[Mylist]:
        """更新対象のマイリストを返す

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        return []

    def get_prev_video_lists(self, m_list: list[Mylist]) -> list[list[MylistInfo]]:
        """それぞれのマイリストごとに既存のレコードを取得する

        Args:
            m_list (list[Mylist]): マイリストレコードオブジェクトのリスト
                                   mylist_db.select系の返り値

        Returns:
            list[list[MylistInfo]]: それぞれのマイリストに含まれる動画情報のリストのリスト
        """
        # 属性チェック
        if not hasattr(self, "mylist_info_db"):
            logger.error(f"{self.L_KIND} GetFunctionList failed, attribute error.")
            return []

        prev_video_lists = []
        for record in m_list:
            mylist_url = record.get("url")
            prev_video_list = self.mylist_info_db.select_from_mylist_url(mylist_url)
            prev_video_lists.append(prev_video_list)
        return prev_video_lists

    def run(self, mw):
        """すべてのマイリストのマイリスト情報を更新する

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, エラー時-1
        """
        logger.info(f"{self.L_KIND} update start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error(f"{self.L_KIND} update failed, argument error.")
            return -1

        self.window["-INPUT2-"].update(value="更新中")
        self.window.refresh()

        # 登録されたすべてのマイリストから現在のマイリスト情報を取得する
        # 処理中もGUIイベントを処理するため別スレッドで起動
        threading.Thread(target=self.update_mylist_info_thread,
                         args=(mw, ), daemon=True).start()

        logger.info(f"{self.L_KIND} update thread start success.")
        return 0

    def update_mylist_info_thread(self, mw):
        """マイリスト情報を更新する（マルチスレッド前提）

        Notes:
            それぞれのマイリストごとに初回ロードか確認し、
            簡易版かレンダリングかどちらで更新するかを保持する

        Returns:
            int: 成功時0, 更新対象無し1, エラー時-1
        """
        logger.info(f"{self.L_KIND} update thread start.")

        # 属性チェック
        if not hasattr(self, "window"):
            logger.error(f"{self.L_KIND} update thread failed, attribute error.")
            return -1

        # 更新対象取得
        m_list = self.get_target_mylist()
        if not m_list:
            logger.info("Target Mylist is nothing.")
            self.window.write_event_value(self.E_DONE, "")
            return 1

        prev_video_lists = self.get_prev_video_lists(m_list)

        # マルチスレッドですべてのマイリストの情報を取得する
        # now_video_listsにすべてのthreadの結果を格納して以降で利用する
        start = time.time()
        self.done_count = 0
        now_video_lists = self.get_mylist_info_execute(m_list)
        elapsed_time = time.time() - start
        logger.info(f"{self.L_KIND} getting done elapsed time : {elapsed_time:.2f} [sec]")

        # マルチスレッドですべてのマイリストの情報を更新する
        start = time.time()
        self.done_count = 0
        result = self.update_mylist_info_execute(m_list, prev_video_lists, now_video_lists)
        elapsed_time = time.time() - start
        logger.info(f"{self.L_KIND} update done elapsed time : {elapsed_time:.2f} [sec]")

        # 後続処理へ
        threading.Thread(target=self.thread_done,
                         args=(mw, ), daemon=False).start()

        logger.info(f"{self.L_KIND} update thread done.")
        return 0

    def get_mylist_info_worker(self, mylist_url: str, all_index_num: int) -> list[dict] | None:
        result = None
        try:
            result = asyncio.run(VideoInfoRssFetcher.fetch_videoinfo(mylist_url))
        except Exception as e:
            pass

        with self.lock:
            self.done_count = self.done_count + 1

        # 左下テキストボックスにプログレス表示
        p_str = f"取得中({self.done_count}/{all_index_num})"
        self.window["-INPUT2-"].update(value=p_str)
        logger.info(mylist_url + f" : getting done ... ({self.done_count}/{all_index_num}).")
        return result

    def get_mylist_info_execute(self, m_list: list[Mylist]) -> list[list[MylistInfo]]:
        result_buf = []
        all_index_num = len(m_list)
        with ThreadPoolExecutor(max_workers=8, thread_name_prefix="ap_thread") as executor:
            futures = []
            for record in m_list:
                mylist_url = record.get("url", "")
                future = executor.submit(
                    self.get_mylist_info_worker, mylist_url, all_index_num
                )
                futures.append((mylist_url, future))
            result_buf = [(f[0], f[1].result()) for f in futures]
        return result_buf

    def update_mylist_info_execute(self, m_list: list[Mylist], prev_video_lists: list[list[MylistInfo]], now_video_lists: list[list[MylistInfo]]) -> list[int]:
        """それぞれのマイリスト情報を更新する

        Args:
            m_list (list[Mylist]): マイリストレコードオブジェクトのリスト
                                   mylist_db.select系の返り値
            prev_video_lists (list[list[MylistInfo]]): それぞれのマイリストに含まれる動画情報のリストのリスト
            now_video_lists (list[list[MylistInfo]]): それぞれのマイリストについて取得した動画情報のリストのリスト

        Returns:
            list[int]: それぞれのマイリストについて動画情報を更新した際の結果のリスト
                       成功で0, 失敗で-1が格納される
                       エラー時空リスト
        """
        result_buf = []

        # リストの大きさが一致しない場合はエラー
        if len(m_list) != len(prev_video_lists):
            return []

        # ワーカースレッドを作成
        with ThreadPoolExecutor(max_workers=8, thread_name_prefix="np_thread") as executor:
            futures = []

            # 引数のマイリストレコードとprev_video_listをワーカーに渡す
            for m, prev_video_list in zip(m_list, prev_video_lists):
                # ワーカー起動
                future = executor.submit(self.update_mylist_info_worker, m, prev_video_list, now_video_lists)
                futures.append((m.get("url"), future))

            # 結果を取得する（futureパターン）
            result_buf = [(f[0], f[1].result()) for f in futures]
        # 結果を返す
        return result_buf

    def update_mylist_info_worker(self, m_record: Mylist, prev_video_list: list[MylistInfo], now_video_lists: list[list[MylistInfo]]) -> int:
        """動画情報を更新するワーカー

        Note:
            更新結果は mylist_db, mylist_info_db のDBに保存される
            画面表示の更新は行わない

        Args:
            m_record (Mylist): マイリストレコードオブジェクト
            prev_video_list (list[MylistInfo]): マイリストに含まれる動画情報のリスト
            now_video_lists (list[list[MylistInfo]]): それぞれのマイリストについて取得した動画情報のリストのリスト

        Returns:
            int: 更新成功時0, 取得レコード0件なら1, エラー時-1
        """
        # 属性チェック
        k = ["lock", "done_count", "window", "mylist_db", "mylist_info_db"]
        if not (set(k) <= set(dir(self))):
            logger.error(f"{self.L_KIND} UpdateMylistInfoWorker failed, attribute error")
            return -1

        # 引数チェック
        mylist_info_cols = MylistInfo.__table__.c.keys()
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
        try:
            if not (hasattr(m_record, "get") and m_record.get("url")):
                raise ValueError
            if not (isinstance(prev_video_list, list)):
                raise ValueError
            for m in prev_video_list:
                if not (set(m.keys()) <= set(mylist_info_cols)):
                    raise ValueError
            if not (isinstance(now_video_lists, list) and now_video_lists):
                raise ValueError
            for mylist_url, now_video_list in now_video_lists:
                if not (isinstance(mylist_url, str) and mylist_url):
                    raise ValueError
                if not (isinstance(now_video_list, list)):
                    raise ValueError
                for m in now_video_list:
                    if not (set(m.keys()) <= set(table_cols)):
                        raise ValueError
        except ValueError:
            logger.error(f"{self.L_KIND} UpdateMylistInfoWorker failed, argument error")
            return -1

        # マルチスレッド内では各々のスレッドごとに新しくDBセッションを張る
        mylist_db = MylistDBController(self.mylist_db.dbname)
        mylist_info_db = MylistInfoDBController(self.mylist_info_db.dbname)
        with self.lock:
            self.done_count = self.done_count + 1

        # 取得した動画情報について、マイリストに対応したものを取り出す
        mylist_url = m_record.get("url")
        records = [r[1] for r in now_video_lists if r[0] == mylist_url]
        if len(records) == 1:
            records = records[0]
        else:
            logger.error(f"{self.L_KIND} UpdateMylistInfoWorker failed, now_video_lists is invalid")
            return -1

        if len(records) == 0:
            # 新規マイリスト取得でレンダリングが失敗した場合など
            all_index_num = len(now_video_lists)
            logger.info(mylist_url + f" : no records ... ({self.done_count}/{all_index_num}).")
            return 1

        # 更新前の動画idリストの設定
        prev_videoid_list = [m["video_id"] for m in prev_video_list]

        # 更新後の動画idリストの設定
        now_video_list = records
        now_videoid_list = [m["video_id"] for m in now_video_list]

        # 状況ステータスを調べる
        status_check_list = []
        add_new_video_flag = False
        for n in now_videoid_list:
            if n in prev_videoid_list:
                # 以前から保持していた動画が取得された場合->ステータスも保持する
                s = [p["status"] for p in prev_video_list if p["video_id"] == n]
                status_check_list.append(s[0])
            else:
                # 新規に動画が追加された場合->"未視聴"に設定
                status_check_list.append("未視聴")
                add_new_video_flag = True

        # 状況ステータス設定
        for m, s in zip(now_video_list, status_check_list):
            m["status"] = s

        # THINK::マイリスト作成者名が変わっていた場合に更新する方法
        # usernameが変更されていた場合
        # 作成したばかり等で登録件数0のマイリストの場合は除く
        # if now_video_list:
        #     # usernameが変更されていた場合
        #     now_username = now_video_list[0].get("username")
        #     if prev_username != now_username:
        #         # マイリストの名前を更新する
        #         mylist_db.update_username(mylist_url, now_username)
        #         # 格納済の動画情報の投稿者名を更新する
        #         mylist_info_db.update_username_in_mylist(mylist_url, now_username)
        #         logger.info(f"Mylist username changed , {prev_username} -> {now_username}")

        # DBに格納
        records = []
        try:
            for m in now_video_list:
                dst = get_now_datetime()
                r = {
                    "video_id": m["video_id"],
                    "title": m["title"],
                    "username": m["username"],
                    "status": m["status"],
                    "uploaded_at": m["uploaded_at"],
                    "registered_at": m["registered_at"],
                    "video_url": m["video_url"],
                    "mylist_url": m["mylist_url"],
                    "created_at": dst
                }
                if not (set(r.keys()) <= set(MylistInfo.__table__.c.keys())):
                    raise KeyError
                records.append(r)
        except KeyError:
            logger.error(f"{self.L_KIND} UpdateMylistInfoWorker failed, key error")
            return -1
        mylist_info_db.upsert_from_list(records)

        # マイリストの更新確認日時更新
        # 新しい動画情報が追加されたかに関わらずchecked_atを更新する
        dst = get_now_datetime()
        mylist_db.update_checked_at(mylist_url, dst)

        # マイリストの更新日時更新
        # 新しい動画情報が追加されたときにupdated_atを更新する
        if add_new_video_flag:
            dst = get_now_datetime()
            mylist_db.update_updated_at(mylist_url, dst)

        # プログレス表示
        all_index_num = len(now_video_lists)
        p_str = f"更新中({self.done_count}/{all_index_num})"
        self.window["-INPUT2-"].update(value=p_str)
        logger.info(mylist_url + f" : update done ... ({self.done_count}/{all_index_num}).")
        return 0

    def thread_done(self, mw):
        logger.info(f"{self.L_KIND} update post process start.")

        pb = self.POST_PROCESS()
        pb.run(mw)

        logger.info(f"{self.L_KIND} update post process done.")


class ProcessUpdateMylistInfoThreadDoneBase(ProcessBase):
    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        """マイリストのマイリスト情報を更新するクラスのベース

        Notes:
            このクラスのインスタンスは直接作成・呼び出しは行わない
            必要ならrunをオーバーライドしてそれぞれの後処理を実装する

        Attributes:
            L_KIND (str): ログ出力用のメッセージベース
        """
        super().__init__(log_sflag, log_eflag, process_name)

        self.L_KIND = "UpdateMylist Base"

    def run(self, mw) -> int:
        """すべてのマイリストのマイリスト情報を更新後の後処理

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, エラー時-1
        """
        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error(f"{self.L_KIND} update failed, argument error.")
            return -1

        # 左下の表示を更新する
        self.window["-INPUT2-"].update(value="更新完了！")

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        if mylist_url != "":
            update_table_pane(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        # マイリストの新着表示を表示するかどうか判定する
        m_list = self.mylist_db.select()
        for m in m_list:
            mylist_url = m.get("url")
            video_list = self.mylist_info_db.select_from_mylist_url(mylist_url)
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
            def_data = []
            for i, t in enumerate(video_list):
                a = [i + 1, t["video_id"], t["title"], t["username"], t["status"], t["uploaded_at"], t["registered_at"], t["video_url"], t["mylist_url"]]
                def_data.append(a)

            # 左のマイリストlistboxの表示を更新する
            # 一つでも未視聴の動画が含まれる場合はマイリストに進捗マークを追加する
            if is_mylist_include_new_video(def_data):
                # マイリストDB更新
                self.mylist_db.update_include_flag(mylist_url, True)

        # マイリスト画面表示更新
        update_mylist_pane(self.window, self.mylist_db)

        logger.info(f"{self.L_KIND} update success.")
        return 0


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()