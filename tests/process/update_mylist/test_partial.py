import sys
import unittest
from contextlib import ExitStack

import freezegun
import PySimpleGUI as sg
from mock import MagicMock, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.partial import Partial, PartialThreadDone
from NNMM.process.value_objects.process_info import ProcessInfo


class TestPartial(unittest.TestCase):
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
        instance = Partial(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(PartialThreadDone, instance.post_process)
        self.assertEqual("Partial mylist", instance.L_KIND)
        self.assertEqual("-PARTIAL_UPDATE_THREAD_DONE-", instance.E_DONE)

    def test_get_target_mylist(self):
        with ExitStack() as stack:
            f_now = "2023-12-23 12:34:56"
            freeze_gun = stack.enter_context(freezegun.freeze_time(f_now))
            mock_logger = stack.enter_context(patch("NNMM.process.update_mylist.partial.logger.error"))

            mylist_dict_list = [self._get_mylist_dict(i) for i in range(3)]
            # 更新対象となるmylist_dict
            mylist_dict_list[0]["checked_at"] = "2023-12-20 12:34:56"
            # 更新対象とならないmylist_dict
            mylist_dict_list[1]["checked_at"] = "2023-12-23 12:34:56"
            # インターバル文字列解釈エラーとなるmylist_dict
            mylist_dict_list[2]["check_interval"] = "invalid"

            instance = Partial(self.process_info)
            instance.mylist_db.select = lambda: mylist_dict_list
            actual = instance.get_target_mylist()
            expect = [mylist_dict_list[0]]
            self.assertEqual(expect, actual)

            # キーエラーとなるmylist_dict
            mylist_dict_list = [self._get_mylist_dict()]
            del mylist_dict_list[0]["check_interval"]
            actual = instance.get_target_mylist()
            self.assertEqual([], actual)

    def test_thread_done_init(self):
        instance = PartialThreadDone(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual("Partial mylist", instance.L_KIND)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
