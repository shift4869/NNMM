import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.base import ThreadDoneBase
from nnmm.process.update_mylist.value_objects.mylist_dict_list import MylistDictList
from nnmm.process.update_mylist.value_objects.video_dict_list import VideoDictList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestBase(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.update_mylist.base.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
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
            "created_at": "2025-11-25 12:34:56",
            "updated_at": "2025-11-25 12:34:56",
            "checked_at": "2025-11-25 12:34:56",
            "check_interval": "15分",
            "check_failed_count": 0,
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
            "uploaded_at": "2025-11-25 12:34:51",
            "registered_at": "2025-11-25 12:34:51",
            "video_url": "https://www.nicovideo.jp/watch/sm12345671",
            "mylist_url": mylist_url,
            "created_at": "2025-11-25 12:34:51",
        }
        return [typed_video]

    def test_init(self):
        instance = ThreadDoneBase(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual("UpdateMylist Base", instance.L_KIND)

    def test_create_component(self):
        instance = ThreadDoneBase(self.process_info)
        self.assertIsNone(instance.create_component())

    def test_callback(self):
        mock_show_mylist_info_all = self.enterContext(patch("nnmm.process.update_mylist.base.show_mylist_info_all"))
        mock_is_mylist_include_new_video = self.enterContext(
            patch("nnmm.process.update_mylist.base.is_mylist_include_new_video")
        )

        Params = namedtuple(
            "Params",
            [
                "is_valid_mylist_url",
                "is_valid_typed_mylist_list",
                "is_valid_typed_video_list",
                "is_mylist_include_new_video",
                "result",
            ],
        )

        def pre_run(params: Params) -> ThreadDoneBase:
            instance = ThreadDoneBase(self.process_info)
            instance.window.mylist_db = instance.mylist_db
            instance.window.mylist_info_db = instance.mylist_info_db
            instance.set_bottom_textbox = MagicMock()

            mylist_dict = self._get_mylist_dict()
            valid_mylist_url = mylist_dict["url"]
            records = self._get_video_dict_list(valid_mylist_url)

            mock_show_mylist_info_all.reset_mock()
            instance.get_upper_textbox = MagicMock()
            if params.is_valid_mylist_url:
                instance.get_upper_textbox.return_value.to_str.return_value = valid_mylist_url
            else:
                instance.get_upper_textbox.return_value.to_str.return_value = ""

            instance.update_table_pane = MagicMock()

            instance.mylist_db.reset_mock()
            if params.is_valid_typed_mylist_list:
                instance.mylist_db.select.return_value = [mylist_dict]
            else:
                instance.mylist_db.select.return_value = []

            instance.mylist_info_db.reset_mock()
            if params.is_valid_typed_video_list:
                instance.mylist_info_db.select_from_mylist_url.return_value = records
            else:
                instance.mylist_info_db.select_from_mylist_url.return_value = []

            mock_is_mylist_include_new_video.reset_mock()
            if params.is_mylist_include_new_video:
                mock_is_mylist_include_new_video.side_effect = lambda def_data: True
            else:
                mock_is_mylist_include_new_video.side_effect = lambda def_data: False

            instance.update_mylist_pane = MagicMock()
            return instance

        def post_run(actual: Result, instance: ThreadDoneBase, params: Params) -> None:
            self.assertEqual(params.result, actual)

            instance.set_bottom_textbox.assert_called_once_with("更新完了！", False)

            mylist_url = ""
            mylist_dict = self._get_mylist_dict()
            valid_mylist_url = mylist_dict["url"]
            records = self._get_video_dict_list(valid_mylist_url)

            if params.is_valid_mylist_url:
                mylist_url = valid_mylist_url
                mock_show_mylist_info_all.assert_not_called()
            else:
                self.assertEqual(
                    [
                        call.ShowMylistInfoAll(ProcessInfo.create("全動画表示", instance.window)),
                        call.ShowMylistInfoAll().callback(),
                    ],
                    mock_show_mylist_info_all.mock_calls,
                )

            instance.update_table_pane.assert_called_once_with(mylist_url)
            instance.mylist_db.select.assert_called_once_with()

            if params.is_valid_typed_mylist_list:
                mylist_dict_list = MylistDictList.create([mylist_dict])
                typed_mylist = mylist_dict_list.to_typed_mylist_list()[0]
                mylist_url = typed_mylist.url.non_query_url
                instance.mylist_info_db.select_from_mylist_url.assert_called_once_with(mylist_url)

                video_dict_list = VideoDictList.create(records)
                typed_video = video_dict_list.to_typed_video_list()[0]
                def_data = []
                if params.is_valid_typed_video_list:
                    def_data.append(list(typed_video.to_dict().values()))

                mock_is_mylist_include_new_video.assert_called_once_with(def_data)

                if params.is_mylist_include_new_video:
                    instance.mylist_db.update_include_flag.assert_called_once_with(mylist_url, True)
                else:
                    instance.mylist_db.update_include_flag.assert_not_called()
            else:
                instance.mylist_info_db.select_from_mylist_url.assert_not_called()
                mock_is_mylist_include_new_video.assert_not_called()
                instance.mylist_db.update_include_flag.assert_not_called()

        params_list = [
            Params(True, True, True, True, Result.success),
            Params(True, True, True, False, Result.success),
            Params(True, True, False, False, Result.success),
            Params(True, False, False, False, Result.success),
            Params(False, False, False, False, Result.success),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
