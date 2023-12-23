import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.base import ThreadDoneBase
from NNMM.process.update_mylist.value_objects.video_dict_list import VideoDictList
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestBase(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_mylist_dict(self) -> dict:
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
            "is_include_new": True,
        }
        return mylist_dict

    def _get_video_dict_list(self, mylist_url) -> list[dict]:
        typed_video = {
            "id": 1,
            "video_id": "sm12345671",
            "title": "title_1",
            "username": "username_1",
            "status": "未視聴",
            "uploaded_at": "2023-12-22 12:34:51",
            "registered_at": "2023-12-22 12:34:51",
            "video_url": "https://www.nicovideo.jp/watch/sm12345671",
            "mylist_url": mylist_url,
            "created_at": "2023-12-22 12:34:51",
        }
        return [typed_video]

    def test_init(self):
        instance = ThreadDoneBase(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual("UpdateMylist Base", instance.L_KIND)

    def test_run(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch("NNMM.process.update_mylist.base.logger.info"))
            mock_get_upper_textbox = stack.enter_context(
                patch("NNMM.process.update_mylist.base.ProcessBase.get_upper_textbox")
            )
            mock_update_table_pane = stack.enter_context(
                patch("NNMM.process.update_mylist.base.ProcessBase.update_table_pane")
            )
            mock_is_mylist_include_new_video = stack.enter_context(
                patch("NNMM.process.update_mylist.base.is_mylist_include_new_video")
            )
            mock_update_mylist_pane = stack.enter_context(
                patch("NNMM.process.update_mylist.base.ProcessBase.update_mylist_pane")
            )

            instance = ThreadDoneBase(self.process_info)

            def pre_run(is_valid_mylist_url, is_mylist_include_new_video):
                mylist_dict = self._get_mylist_dict()
                mylist_url = mylist_dict["url"]

                mock_get_upper_textbox.reset_mock()
                if is_valid_mylist_url:
                    mock_get_upper_textbox.return_value.to_str.side_effect = lambda: mylist_url
                else:
                    mock_get_upper_textbox.return_value.to_str.side_effect = lambda: ""

                mock_update_table_pane.reset_mock()
                instance.mylist_db.reset_mock()
                instance.mylist_db.select.side_effect = lambda: [mylist_dict]

                video_dict_list = self._get_video_dict_list(mylist_url)
                instance.mylist_info_db.reset_mock()
                instance.mylist_info_db.select_from_mylist_url.side_effect = lambda url: video_dict_list

                mock_is_mylist_include_new_video.reset_mock()

                def f(def_data):
                    return is_mylist_include_new_video

                mock_is_mylist_include_new_video.side_effect = f

                mock_update_mylist_pane.reset_mock()

            def post_run(is_valid_maylist_url, is_mylist_include_new_video):
                mylist_dict = self._get_mylist_dict()
                mylist_url = mylist_dict["url"]
                self.assertEqual([call(), call().to_str()], mock_get_upper_textbox.mock_calls)

                if is_valid_maylist_url:
                    self.assertEqual([call(mylist_url)], mock_update_table_pane.mock_calls)

                expect_mylist_db_calls = [call.select()]
                if is_mylist_include_new_video:
                    expect_mylist_db_calls.append(call.update_include_flag(mylist_url, True))
                self.assertEqual(expect_mylist_db_calls, instance.mylist_db.mock_calls)

                self.assertEqual([call.select_from_mylist_url(mylist_url)], instance.mylist_info_db.mock_calls)

                video_dict_list = self._get_video_dict_list(mylist_url)
                video_dict_list = VideoDictList.create(video_dict_list)
                typed_video_list = video_dict_list.to_typed_video_list()
                def_data = []
                for typed_video in typed_video_list:
                    def_data.append(list(typed_video.to_dict().values()))
                self.assertEqual([call(def_data)], mock_is_mylist_include_new_video.mock_calls)

                self.assertEqual([call()], mock_update_mylist_pane.mock_calls)

            Params = namedtuple("Params", ["is_valid_maylist_url", "is_mylist_include_new_video", "result"])
            params_list = [
                Params(True, True, Result.success),
                Params(True, False, Result.success),
                Params(False, True, Result.success),
                Params(False, False, Result.success),
            ]
            for params in params_list:
                pre_run(*params[:-1])
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(*params[:-1])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
