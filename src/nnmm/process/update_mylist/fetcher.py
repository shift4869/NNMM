import asyncio
from concurrent.futures import ThreadPoolExecutor
from logging import INFO, getLogger

from PySide6.QtWidgets import QLineEdit

from nnmm.process.update_mylist.executor_base import ExecutorBase
from nnmm.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from nnmm.process.update_mylist.value_objects.payload_list import PayloadList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result
from nnmm.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo
from nnmm.video_info_fetcher.video_info_fetcher import VideoInfoFetcher

logger = getLogger(__name__)
logger.setLevel(INFO)


class Fetcher(ExecutorBase):
    """マイリスト更新時に video_info を fetch してくる fetcher をマルチスレッドで起動する

    Attribute:
        mylist_with_video_list (MylistWithVideoList): fetch すべきマイリスト情報と現在の動画情報

    Returns:
        PayloadList: PayloadList.create() で返される fetch 後の動画情報
    """

    mylist_with_video_list: MylistWithVideoList

    def __init__(self, mylist_with_video_list: MylistWithVideoList, process_info: ProcessInfo) -> None:
        """初期設定

        Args:
            mylist_with_video_list (MylistWithVideoList): fetch すべきマイリスト情報と現在の動画情報
            process_info (ProcessInfo): 画面更新用 process_info
        """
        super().__init__(process_info)
        if not isinstance(mylist_with_video_list, MylistWithVideoList):
            raise ValueError("mylist_with_video_list must be MylistWithVideoList.")
        self.mylist_with_video_list = mylist_with_video_list

    def execute(self) -> PayloadList:
        """fetch する thread を起動する

        Returns:
            PayloadList: fetch すべきマイリスト情報と現在の動画情報と、fetch 後の動画情報をまとめたペイロード
        """
        result_buf = []
        all_index_num = len(self.mylist_with_video_list)
        with ThreadPoolExecutor(max_workers=8, thread_name_prefix="ap_thread") as executor:
            futures = []
            for mylist_with_video in self.mylist_with_video_list:
                mylist = mylist_with_video.mylist
                video_list = mylist_with_video.video_list
                mylist_url = mylist.url.non_query_url
                future = executor.submit(self.execute_worker, mylist_url, all_index_num)
                futures.append((mylist_with_video, future))
            result_buf = [(f[0], f[1].result()) for f in futures]
        return PayloadList.create(result_buf)

    def execute_worker(self, *argv) -> FetchedVideoInfo | Result:
        """具体的な fetch を担当するワーカー

        Returns:
            FetchedVideoInfo | Result: fetch 後の動画情報, fetch 失敗時は Result.failed
        """
        mylist_url, all_index_num = argv
        result = Result.failed
        try:
            result = asyncio.run(VideoInfoFetcher.fetch_videoinfo(mylist_url))
        except Exception as e:
            pass

        with self.lock:
            self.done_count = self.done_count + 1
            if isinstance(result, FetchedVideoInfo):
                p_str = f"取得中({self.done_count}/{all_index_num})"
                oneline_log: QLineEdit = self.window.oneline_log
                oneline_log.setText(p_str)
                oneline_log.update()
                logger.info(mylist_url + f" : getting done ... ({self.done_count}/{all_index_num}).")
            else:
                logger.info(mylist_url + f" : fetching failed. ({self.done_count}/{all_index_num}).")
        return result


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
