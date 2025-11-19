import logging.config
import threading
import time
from abc import abstractmethod
from logging import INFO, getLogger

from PySide6.QtCore import QDateTime, QDir, QLibraryInfo, QSysInfo, Qt, QTimer, Slot, qVersion
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from nnmm.process.base import ProcessBase
from nnmm.process.update_mylist.database_updater import DatabaseUpdater
from nnmm.process.update_mylist.fetcher import Fetcher
from nnmm.process.update_mylist.value_objects.mylist_dict_list import MylistDictList
from nnmm.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from nnmm.process.update_mylist.value_objects.video_dict_list import VideoDictList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import CustomLogger, Result, is_mylist_include_new_video

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

        self.post_process = ThreadDoneBase
        self.L_KIND = "UpdateMylist Base"
        self.E_DONE = ""

    @abstractmethod
    def get_target_mylist(self) -> list[dict]:
        """更新対象のマイリストを返す

        Returns:
            list[dict]: 更新対象のマイリストを表す辞書リスト
        """
        raise NotImplementedError

    def create_component(self) -> QWidget:
        add_mylist_button = QPushButton(self.name)
        add_mylist_button.clicked.connect(lambda: self.callback())
        return add_mylist_button

    @Slot()
    def callback(self) -> Result:
        """マイリスト情報を更新する"""
        logger.info(f"{self.L_KIND} update start.")

        self.set_bottom_textbox("更新中", False)

        # 現在のマイリスト情報を取得する
        # 処理中もGUIイベントを処理するため別スレッドで起動
        threading.Thread(target=self.update_mylist_info_thread, daemon=True).start()

        logger.info(f"{self.L_KIND} update thread start success.")
        return Result.success

    def update_mylist_info_thread(self) -> Result:
        """マイリスト情報を更新する（マルチスレッド前提）"""
        logger.info(f"{self.L_KIND} update thread start.")

        # 更新対象取得
        m_list = self.get_target_mylist()
        if not m_list:
            logger.info("Target Mylist is nothing.")
            # self.window.write_event_value(self.E_DONE, "")
            return Result.failed

        now_mylist_with_video_list = MylistWithVideoList.create(m_list, self.mylist_info_db)

        # マルチスレッドで更新対象のマイリストの情報を取得する
        # fetched_video_listsにfetch結果を格納して以降で利用する
        start = time.time()
        fetched_video_lists = Fetcher(now_mylist_with_video_list, self.process_info).execute()
        elapsed_time = time.time() - start
        logger.info(f"{self.L_KIND} getting done elapsed time : {elapsed_time:.2f} [sec]")

        # マルチスレッドで更新対象のマイリストの情報についてDBを更新する
        start = time.time()
        result = DatabaseUpdater(fetched_video_lists, self.process_info).execute()
        elapsed_time = time.time() - start
        logger.info(f"{self.L_KIND} update done elapsed time : {elapsed_time:.2f} [sec]")

        logger.info(f"{self.L_KIND} update thread done.")

        # 後続処理へ
        threading.Thread(target=self.thread_done, daemon=False).start()
        return Result.success

    def thread_done(self) -> Result:
        """後続処理

        マイリスト更新処理が終わった後、派生先それぞれのTHREAD_DONEプロセスを呼び出す
        呼び出し先は self.post_process にて制御される
        """
        logger.info(f"{self.L_KIND} update post process start.")

        process_info = ProcessInfo.create("-UPDATE_THREAD_DONE-", self.window)
        pb = self.post_process(process_info)
        threading.Thread(target=pb.callback, daemon=False).start()

        logger.info(f"{self.L_KIND} update post process start success.")
        return Result.success


class ThreadDoneBase(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        """マイリストのマイリスト情報を更新するクラスのベース

        このクラスのインスタンスは直接作成・呼び出しは行わない
        必要ならrunをオーバーライドしてそれぞれの後処理を実装する
        """
        super().__init__(process_info)

        self.L_KIND = "UpdateMylist Base"

    def create_component(self) -> QWidget:
        "後続処理なのでコンポーネントは作成しない"
        return None

    @Slot()
    def callback(self) -> Result:
        """マイリスト情報を更新後の後処理"""
        # 左下の表示を更新する
        self.set_bottom_textbox("更新完了！", False)

        # テーブルの表示を更新する
        mylist_url = self.get_upper_textbox().to_str()
        if mylist_url != "":
            self.update_table_pane(mylist_url)

        # マイリストの新着表示を表示するかどうか判定する
        m_list = self.mylist_db.select()
        mylist_dict_list = MylistDictList.create(m_list)
        typed_mylist_list = mylist_dict_list.to_typed_mylist_list()
        for typed_mylist in typed_mylist_list:
            mylist_url = typed_mylist.url.non_query_url

            records = self.mylist_info_db.select_from_mylist_url(mylist_url)
            video_dict_list = VideoDictList.create(records)
            typed_video_list = video_dict_list.to_typed_video_list()
            def_data = []
            for typed_video in typed_video_list:
                def_data.append(list(typed_video.to_dict().values()))

            # 左のマイリストlistboxの表示を更新する
            # 一つでも未視聴の動画が含まれる場合はマイリストに進捗マークを追加する
            if is_mylist_include_new_video(def_data):
                # マイリストDB更新
                self.mylist_db.update_include_flag(mylist_url, True)

        # マイリスト画面表示更新
        self.update_mylist_pane()

        logger.info(f"{self.L_KIND} update post process done.")
        return Result.success


if __name__ == "__main__":
    import sys

    import qdarktheme
    from PySide6.QtWidgets import QApplication

    from nnmm.main_window import MainWindow

    app = QApplication()
    qdarktheme.setup_theme()
    window_main = MainWindow()
    window_main.show()
    sys.exit(app.exec())
