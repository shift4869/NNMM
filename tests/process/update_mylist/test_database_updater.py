import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.database_updater import DatabaseUpdater
from nnmm.process.update_mylist.value_objects.payload import Payload
from nnmm.process.update_mylist.value_objects.payload_list import PayloadList
from nnmm.process.update_mylist.value_objects.typed_mylist import TypedMylist
from nnmm.process.update_mylist.value_objects.typed_video import TypedVideo
from nnmm.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result
from nnmm.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo
from nnmm.video_info_fetcher.value_objects.mylistid import Mylistid
from nnmm.video_info_fetcher.value_objects.myshowname import Myshowname
from nnmm.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from nnmm.video_info_fetcher.value_objects.showname import Showname
from nnmm.video_info_fetcher.value_objects.title_list import TitleList
from nnmm.video_info_fetcher.value_objects.uploaded_at_list import UploadedAtList
from nnmm.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL
from nnmm.video_info_fetcher.value_objects.userid import Userid
from nnmm.video_info_fetcher.value_objects.username_list import UsernameList
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


class TestDatabaseUpdater(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_typed_mylist(self) -> TypedMylist:
        mylist_dict = {
            "id": 1,
            "username": "username_1",
            "mylistname": "投稿動画",
            "type": "uploaded",
            "showname": "投稿者1さんの投稿動画",
            "url": "https://www.nicovideo.jp/user/10000001/video",
            "created_at": "2023-12-22 12:34:56",
            "updated_at": "2023-12-22 12:34:56",
            "checked_at": "2023-12-22 12:34:56",
            "check_interval": "15分",
            "check_failed_count": 0,
            "is_include_new": True,
        }
        return TypedMylist.create(mylist_dict)

    def _get_typed_video_list(self) -> TypedVideoList:
        typed_video = TypedVideo.create({
            "id": 1,
            "video_id": "sm12345671",
            "title": "title_1",
            "username": "username_1",
            "status": "未視聴",
            "uploaded_at": "2023-12-22 12:34:51",
            "registered_at": "2023-12-22 12:34:51",
            "video_url": "https://www.nicovideo.jp/watch/sm12345671",
            "mylist_url": "https://www.nicovideo.jp/user/10000001/video",
            "created_at": "2023-12-22 12:34:51",
        })
        return TypedVideoList.create([typed_video])

    def _get_fetched_video_info(self) -> FetchedVideoInfo:
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = UserMylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1"])
        no = list(range(1, len(video_id_list) + 1))

        fetched_video_info = FetchedVideoInfo(
            no,
            userid,
            mylistid,
            showname,
            myshowname,
            mylist_url,
            video_id_list,
            title_list,
            uploaded_at_list,
            registered_at_list,
            video_url_list,
            username_list,
        )
        return fetched_video_info

    def test_init(self):
        payload_list = MagicMock(spec=PayloadList)
        instance = DatabaseUpdater(payload_list, self.process_info)
        self.assertEqual(payload_list, instance.payload_list)

        with self.assertRaises(ValueError):
            instance = DatabaseUpdater("invalid", self.process_info)

    def test_execute(self):
        with ExitStack() as stack:
            mock_thread = stack.enter_context(patch("nnmm.process.update_mylist.database_updater.ThreadPoolExecutor"))

            mock_thread.return_value.__enter__.return_value.submit.return_value.result.return_value = (
                "executor.submit().result()"
            )
            payload_list = MagicMock(spec=PayloadList)
            payload = MagicMock(spec=Payload)

            instance = DatabaseUpdater(payload_list, self.process_info)
            instance.payload_list = [payload]
            actual = instance.execute()
            self.assertEqual([(payload, "executor.submit().result()")], actual)

            self.assertEqual(
                [
                    call(max_workers=8, thread_name_prefix="np_thread"),
                    call().__enter__(),
                    call()
                    .__enter__()
                    .submit(instance.execute_worker, payload.mylist, payload.video_list, payload.fetched_info, 1),
                    call().__enter__().submit().result(),
                    call().__exit__(None, None, None),
                ],
                mock_thread.mock_calls,
            )

    @unittest.skip("")
    def test_execute_worker(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch("nnmm.process.update_mylist.database_updater.logger.info"))
            mock_mylist_db = stack.enter_context(
                patch("nnmm.process.update_mylist.database_updater.MylistDBController")
            )
            mock_mylist_info_db = stack.enter_context(
                patch("nnmm.process.update_mylist.database_updater.MylistInfoDBController")
            )
            mock_get_now_datetime = stack.enter_context(
                patch("nnmm.process.update_mylist.database_updater.get_now_datetime")
            )
            dst = "2023-12-23 15:49:43"
            mock_get_now_datetime.return_value = dst
            payload_list = MagicMock(spec=PayloadList)
            payload = MagicMock(spec=PayloadList)

            instance = DatabaseUpdater(payload_list, self.process_info)
            instance.mylist_db.dbname = "mylist_db.dbname"
            instance.mylist_info_db.dbname = "mylist_info_db.dbname"

            def get_payload(is_valid_fetched_info, add_new_video_flag):
                mylist = self._get_typed_mylist()
                video_list = self._get_typed_video_list()
                fetched_info = self._get_fetched_video_info()

                if not is_valid_fetched_info:
                    fetched_info = Result.failed

                if not add_new_video_flag:
                    video_list = [v.replace_from_str(status="") for v in video_list]
                    video_list = [v.replace_from_str(video_id="sm12345678") for v in video_list]

                all_index_num = 1
                payload = (mylist, video_list, fetched_info, all_index_num)
                return payload

            def pre_run(payload, is_valid_fetched_info, add_new_video_flag):
                mock_mylist_db.reset_mock()
                mock_mylist_info_db.reset_mock()
                instance.window.reset_mock()
                instance.done_count = 0

            def post_run(payload, is_valid_fetched_info, add_new_video_flag):
                mylist_url = payload[0].url.non_query_url
                if not is_valid_fetched_info:
                    self.assertEqual(
                        [call("mylist_db.dbname"), call().update_check_failed_count(mylist_url)],
                        mock_mylist_db.mock_calls,
                    )
                    self.assertEqual([call("mylist_info_db.dbname")], mock_mylist_info_db.mock_calls)
                    instance.window.assert_not_called()
                    return

                expect_mylist_db_calls = [
                    call("mylist_db.dbname"),
                    call().reset_check_failed_count(mylist_url),
                    call().update_checked_at(mylist_url, dst),
                ]
                if add_new_video_flag:
                    expect_mylist_db_calls.append(call().update_updated_at(mylist_url, dst))
                self.assertEqual(expect_mylist_db_calls, mock_mylist_db.mock_calls)

                if not add_new_video_flag:
                    status = ""
                else:
                    status = "未視聴"

                self.assertEqual(
                    [
                        call("mylist_info_db.dbname"),
                        call().upsert_from_list([
                            {
                                "id": "1",
                                "video_id": "sm12345678",
                                "title": "テスト動画",
                                "username": "投稿者1",
                                "status": status,
                                "uploaded_at": "2022-05-06 00:00:01",
                                "registered_at": "2022-05-06 00:01:01",
                                "video_url": "https://www.nicovideo.jp/watch/sm12345678",
                                "mylist_url": "https://www.nicovideo.jp/user/1234567/mylist/12345678",
                                "created_at": "2023-12-23 15:49:43",
                            }
                        ]),
                    ],
                    mock_mylist_info_db.mock_calls,
                )

                self.assertEqual(
                    [call.__getitem__("-INPUT2-"), call.__getitem__().update(value="更新中(1/1)")],
                    instance.window.mock_calls,
                )

            Params = namedtuple("Params", ["is_valid_fetched_info", "add_new_video_flag", "result"])
            params_list = [
                Params(True, True, Result.success),
                Params(True, False, Result.success),
                Params(False, True, Result.failed),
            ]
            for params in params_list:
                payload = get_payload(*params[:-1])
                pre_run(payload, *params[:-1])
                actual = instance.execute_worker(*payload)
                expect = params.result
                self.assertEqual(expect, actual)
                post_run(payload, *params[:-1])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
