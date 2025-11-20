import sys
import unittest
from contextlib import ExitStack

import httpx
from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.fetcher import Fetcher
from nnmm.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from nnmm.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestFetcher(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        mylist_with_video_list = MagicMock(spec=MylistWithVideoList)
        instance = Fetcher(mylist_with_video_list, self.process_info)
        self.assertEqual(mylist_with_video_list, instance.mylist_with_video_list)

        with self.assertRaises(ValueError):
            instance = Fetcher("invalid", self.process_info)

    def test_execute(self):
        with ExitStack() as stack:
            mock_thread = stack.enter_context(patch("nnmm.process.update_mylist.fetcher.ThreadPoolExecutor"))
            mock_create = stack.enter_context(patch("nnmm.process.update_mylist.fetcher.PayloadList.create"))

            mock_thread.return_value.__enter__.return_value.submit.return_value.result.return_value = (
                "executor.submit().result()"
            )
            mock_create.side_effect = lambda p: "PayloadList.create()"
            mylist_with_video_list = MagicMock(spec=MylistWithVideoList)
            mylist_with_video = MagicMock(spec=MylistWithVideo)
            mylist_with_video.mylist.url.non_query_url = MagicMock()

            instance = Fetcher(mylist_with_video_list, self.process_info)
            instance.mylist_with_video_list = [mylist_with_video]
            actual = instance.execute()
            self.assertEqual("PayloadList.create()", actual)

            self.assertEqual(
                [
                    call(max_workers=8, thread_name_prefix="ap_thread"),
                    call().__enter__(),
                    call().__enter__().submit(instance.execute_worker, mylist_with_video.mylist.url.non_query_url, 1),
                    call().__enter__().submit().result(),
                    call().__exit__(None, None, None),
                ],
                mock_thread.mock_calls,
            )
            self.assertEqual([call([(mylist_with_video, "executor.submit().result()")])], mock_create.mock_calls)

    @unittest.skip("")
    def test_execute_worker(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch("nnmm.process.update_mylist.fetcher.logger.info"))
            mock_fetch_videoinfo = stack.enter_context(
                patch("nnmm.process.update_mylist.fetcher.VideoInfoFetcher.fetch_videoinfo")
            )
            mock_fetch_videoinfo.side_effect = lambda url: "VideoInfoFetcher.fetch_videoinfo()"
            mylist_with_video_list = MagicMock(spec=MylistWithVideoList)
            instance = Fetcher(mylist_with_video_list, self.process_info)

            mylist_url = "https://www.nicovideo.jp/user/1111111/mylist/10000001"
            all_index_num = 2
            actual = instance.execute_worker(mylist_url, all_index_num)
            expect = "VideoInfoFetcher.fetch_videoinfo()"
            self.assertEqual(expect, actual)

            self.assertEqual([call(mylist_url)], mock_fetch_videoinfo.mock_calls)
            self.assertEqual(
                [call.__getitem__("-INPUT2-"), call.__getitem__().update(value="取得中(1/2)")],
                instance.window.mock_calls,
            )
            mock_fetch_videoinfo.reset_mock()
            instance.window.reset_mock()

            mock_fetch_videoinfo.side_effect = httpx.HTTPStatusError
            actual = instance.execute_worker(mylist_url, all_index_num)
            self.assertEqual(Result.failed, actual)

            self.assertEqual([call(mylist_url)], mock_fetch_videoinfo.mock_calls)
            self.assertEqual(
                [call.__getitem__("-INPUT2-"), call.__getitem__().update(value="取得中(2/2)")],
                instance.window.mock_calls,
            )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
