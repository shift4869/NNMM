import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from logging import INFO, getLogger

from NNMM.process.update_mylist.executor_base import ExecutorBase
from NNMM.process.update_mylist.value_objects.payload import Payload
from NNMM.process.update_mylist.value_objects.payload_list import PayloadList
from NNMM.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from NNMM.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from NNMM.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from NNMM.process.update_mylist.value_objects.video_dict_list import VideoDictList
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result
from NNMM.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo
from NNMM.video_info_fetcher.video_info_rss_fetcher import VideoInfoRssFetcher

logger = getLogger(__name__)
logger.setLevel(INFO)


class Fetcher(ExecutorBase):
    mylist_with_video_list: MylistWithVideoList
    process_info: ProcessInfo

    def __init__(self, mylist_with_video_list: MylistWithVideoList, process_info: ProcessInfo) -> None:
        self.mylist_with_video_list = mylist_with_video_list
        self.process_info = process_info

        self.window = process_info.window
        self.lock = threading.Lock()
        self.done_count = 0

    def execute(self) -> PayloadList:
        result_buf = []
        all_index_num = len(self.mylist_with_video_list)
        with ThreadPoolExecutor(max_workers=8, thread_name_prefix="ap_thread") as executor:
            futures = []
            for mylist_with_video in self.mylist_with_video_list:
                mylist = mylist_with_video.mylist
                video_list = mylist_with_video.video_list
                mylist_url = mylist.url.non_query_url
                future = executor.submit(
                    self.execute_worker, mylist_url, all_index_num
                )
                futures.append((mylist_with_video, future))
            result_buf = [(f[0], f[1].result()) for f in futures]
        return PayloadList.create(result_buf)

    def execute_worker(self, *argv) -> FetchedVideoInfo | Result:
        mylist_url, all_index_num = argv
        result = Result.failed
        try:
            result = asyncio.run(VideoInfoRssFetcher.fetch_videoinfo(mylist_url))
        except Exception as e:
            pass

        with self.lock:
            self.done_count = self.done_count + 1
            p_str = f"取得中({self.done_count}/{all_index_num})"
            self.window["-INPUT2-"].update(value=p_str)
            logger.info(mylist_url + f" : getting done ... ({self.done_count}/{all_index_num}).")
        return result


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
