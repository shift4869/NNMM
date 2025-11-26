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
from nnmm.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


class TestFetcher(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.update_mylist.fetcher.logger.info"))
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
        mock_thread = self.enterContext(patch("nnmm.process.update_mylist.fetcher.ThreadPoolExecutor"))
        mock_create = self.enterContext(patch("nnmm.process.update_mylist.fetcher.PayloadList.create"))

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

    def test_execute_worker(self):
        mock_fetch_videoinfo = self.enterContext(
            patch("nnmm.process.update_mylist.fetcher.VideoInfoFetcher.fetch_videoinfo")
        )
        mylist_with_video_list = MagicMock(spec=MylistWithVideoList)
        instance = Fetcher(mylist_with_video_list, self.process_info)
        instance.window.oneline_log = MagicMock()

        mylist_url = "https://www.nicovideo.jp/user/1111111/mylist/10000001"
        all_index_num = 2

        # 正常系
        fetched_video_info = MagicMock(spec=FetchedVideoInfo)
        mock_fetch_videoinfo.return_value = fetched_video_info

        actual = instance.execute_worker(mylist_url, all_index_num)
        expect = fetched_video_info
        self.assertEqual(expect, actual)
        self.assertEqual([call(mylist_url), call().__eq__(fetched_video_info)], mock_fetch_videoinfo.mock_calls)
        self.assertEqual(
            [call.setText("取得中(1/2)"), call.update()],
            instance.window.oneline_log.mock_calls,
        )

        mock_fetch_videoinfo.reset_mock()
        instance.window.oneline_log.reset_mock()

        # 異常系: fetch 時に例外が発生しても処理は続行される
        mock_fetch_videoinfo.side_effect = httpx.HTTPStatusError

        actual = instance.execute_worker(mylist_url, all_index_num)
        self.assertEqual(Result.failed, actual)
        self.assertEqual([call(mylist_url)], mock_fetch_videoinfo.mock_calls)
        instance.window.oneline_log.assert_not_called()

        mock_fetch_videoinfo.reset_mock()
        instance.window.oneline_log.reset_mock()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
