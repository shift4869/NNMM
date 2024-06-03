import sys
import unittest
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, patch

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.single import Single, SingleThreadDone
from nnmm.process.value_objects.process_info import ProcessInfo


class TestSingle(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_mylist_dict(self, index: int = 1) -> dict:
        mylist_dict = {
            "id": str(index),
            "username": f"username_{index}",
            "mylistname": "投稿動画",
            "type": "uploaded",
            "showname": f"投稿者{index}さんの投稿動画",
            "url": f"https://www.nicovideo.jp/user/1000000{index}/video",
            "created_at": "2023-12-22 12:34:56",
            "updated_at": "2023-12-22 12:34:56",
            "checked_at": "2023-12-22 12:34:56",
            "check_interval": "15分",
            "is_include_new": True,
        }
        return mylist_dict

    def test_init(self):
        instance = Single(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(SingleThreadDone, instance.post_process)
        self.assertEqual("Single mylist", instance.L_KIND)
        self.assertEqual("-UPDATE_THREAD_DONE-", instance.E_DONE)

    def test_get_target_mylist(self):
        with ExitStack() as stack:
            mock_get_upper_textbox = stack.enter_context(
                patch("nnmm.process.update_mylist.single.Base.get_upper_textbox")
            )

            mylist_dict_list = [self._get_mylist_dict()]
            mylist_url = mylist_dict_list[0]["url"]
            instance = Single(self.process_info)

            mock_get_upper_textbox.return_value.to_str.side_effect = lambda: mylist_url
            instance.mylist_db.select_from_url = lambda url: mylist_dict_list
            actual = instance.get_target_mylist()
            expect = mylist_dict_list
            self.assertEqual(expect, actual)

            instance.mylist_db.reset_mock()
            mock_get_upper_textbox.return_value.to_str.side_effect = lambda: ""
            actual = instance.get_target_mylist()
            self.assertEqual([], actual)
            instance.mylist_db.assert_not_called()

    def test_thread_done_init(self):
        instance = SingleThreadDone(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual("Single mylist", instance.L_KIND)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
