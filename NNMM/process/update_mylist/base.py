import asyncio
import threading
import time
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from logging import INFO, getLogger

from NNMM.model import Mylist, MylistInfo
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.base import ProcessBase
from NNMM.process.update_mylist.database_updater import DatabaseUpdater
from NNMM.process.update_mylist.fetcher import Fetcher
from NNMM.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from NNMM.process.value_objects.mylist_row_list import MylistRowList
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, get_now_datetime, is_mylist_include_new_video
from NNMM.video_info_fetcher.video_info_rss_fetcher import VideoInfoRssFetcher

logger = getLogger(__name__)
logger.setLevel(INFO)


class Base(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        """マイリストのマイリスト情報を更新するクラスのベース

        Notes:
            このクラスのインスタンスは直接作成・呼び出しは行わない
            このクラスの派生クラスは get_target_mylist をオーバーライドする必要がある

        Attributes:
            lock (threading.Lock): マルチスレッドで使う排他ロック
            done_count (int): 処理対象について現在処理した数
            L_KIND (str): ログ出力用のメッセージベース
            E_DONE (str): 後続処理へのイベントキー
        """
        super().__init__(process_info)

        self.lock = threading.Lock()
        self.done_count = 0
        self.post_process = ThreadDoneBase
        self.L_KIND = "UpdateMylist Base"
        self.E_DONE = ""

    @abstractmethod
    def get_target_mylist(self) -> list[dict]:
        """更新対象のマイリストを返す

        Returns:
            list[dict]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        raise NotImplementedError

    def run(self) -> Result:
        """すべてのマイリストのマイリスト情報を更新する
        """
        logger.info(f"{self.L_KIND} update start.")

        self.window["-INPUT2-"].update(value="更新中")
        self.window.refresh()

        # 登録されたすべてのマイリストから現在のマイリスト情報を取得する
        # 処理中もGUIイベントを処理するため別スレッドで起動
        threading.Thread(target=self.update_mylist_info_thread,
                         daemon=True).start()

        logger.info(f"{self.L_KIND} update thread start success.")
        return Result.success

    def update_mylist_info_thread(self) -> None:
        """マイリスト情報を更新する（マルチスレッド前提）

        Returns: None
        """
        logger.info(f"{self.L_KIND} update thread start.")

        # 更新対象取得
        m_list = self.get_target_mylist()
        if not m_list:
            logger.info("Target Mylist is nothing.")
            self.window.write_event_value(self.E_DONE, "")
            return

        # now_video_lists = self.get_now_video_lists(m_list)
        now_mylist_with_video_list = MylistWithVideoList.create(m_list, self.mylist_info_db)

        # マルチスレッドですべてのマイリストの情報を取得する
        # fetched_video_listsにすべてのthreadの結果を格納して以降で利用する
        start = time.time()
        self.done_count = 0
        # fetched_video_lists = self.get_mylist_info_execute(m_list)
        fetched_video_lists = Fetcher(now_mylist_with_video_list, self.process_info).execute()
        elapsed_time = time.time() - start
        logger.info(f"{self.L_KIND} getting done elapsed time : {elapsed_time:.2f} [sec]")

        # マルチスレッドですべてのマイリストの情報を更新する
        start = time.time()
        self.done_count = 0
        # result = self.update_mylist_info_execute(m_list, now_mylist_with_video_list, fetched_video_lists)
        result = DatabaseUpdater(fetched_video_lists, self.process_info).execute()
        elapsed_time = time.time() - start
        logger.info(f"{self.L_KIND} update done elapsed time : {elapsed_time:.2f} [sec]")

        # 後続処理へ
        threading.Thread(target=self.thread_done,
                         daemon=False).start()

        logger.info(f"{self.L_KIND} update thread done.")
        return

    def thread_done(self) -> None:
        logger.info(f"{self.L_KIND} update post process start.")

        process_info = ProcessInfo.create("-UPDATE_THREAD_DONE-", self)
        pb = self.post_process(process_info)
        pb.run()

        logger.info(f"{self.L_KIND} update post process done.")


class ThreadDoneBase(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        """マイリストのマイリスト情報を更新するクラスのベース

        Notes:
            このクラスのインスタンスは直接作成・呼び出しは行わない
            必要ならrunをオーバーライドしてそれぞれの後処理を実装する
        """
        super().__init__(process_info)

        self.L_KIND = "UpdateMylist Base"

    def run(self) -> Result:
        """すべてのマイリストのマイリスト情報を更新後の後処理
        """
        # 左下の表示を更新する
        self.window["-INPUT2-"].update(value="更新完了！")

        # テーブルの表示を更新する
        mylist_url = self.get_upper_textbox().to_str()
        if mylist_url != "":
            self.update_table_pane(mylist_url)

        # マイリストの新着表示を表示するかどうか判定する
        m_list = self.mylist_db.select()
        mylist_row_list = MylistRowList.create()
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
        self.update_mylist_pane()

        logger.info(f"{self.L_KIND} update success.")
        return


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
