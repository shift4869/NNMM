import sys
import unittest
from contextlib import ExitStack
from dataclasses import FrozenInstanceError
from typing import Iterator

from mock import MagicMock, patch

from NNMM.model import Mylist
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from NNMM.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList


class TestMylistWithVideoList(unittest.TestCase):
    def _get_mylist_dict(self, index: int = 1) -> dict:
        return {
            "id": index,
            "username": f"username_{index}",
            "mylistname": f"mylistname_{index}",
            "type": f"uploaded",
            "showname": f"投稿者{index}さんの投稿動画",
            "url": f"https://www.nicovideo.jp/user/{index:08}/video",
            "created_at": "2023-12-21 12:34:56",
            "updated_at": "2023-12-21 12:34:56",
            "checked_at": "2023-12-21 12:34:56",
            "check_interval": "15分",
            "check_failed_count": 0,
            "is_include_new": False,
        }

    def _get_mylist(self, index: int = 1) -> Mylist:
        mylist = self._get_mylist_dict(index)
        return Mylist(
            mylist["id"],
            mylist["username"],
            mylist["mylistname"],
            mylist["type"],
            mylist["showname"],
            mylist["url"],
            mylist["created_at"],
            mylist["updated_at"],
            mylist["checked_at"],
            mylist["check_interval"],
            mylist["check_failed_count"],
            mylist["is_include_new"],
        )

    def test_init(self):
        mylist_with_video = MagicMock(spec=MylistWithVideo)
        instance = MylistWithVideoList([mylist_with_video])
        self.assertEqual([mylist_with_video], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = MylistWithVideoList(params)

        with self.assertRaises(FrozenInstanceError):
            instance = MylistWithVideoList([mylist_with_video])
            instance._list = []

    def test_magic_method(self):
        mylist_with_video = MagicMock(spec=MylistWithVideo)
        instance = MylistWithVideoList([mylist_with_video])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], mylist_with_video)

    def test_create(self):
        with ExitStack() as stack:
            mock_create = stack.enter_context(
                patch("NNMM.process.update_mylist.value_objects.mylist_with_video_list.MylistWithVideo.create")
            )
            mock_mylist_with_video = MagicMock(spec=MylistWithVideo)
            mock_create.side_effect = lambda m, db: mock_mylist_with_video
            mylist_mylist_info_db = MagicMock(spec=MylistInfoDBController)

            mylist_list = [self._get_mylist_dict()]
            expect = MylistWithVideoList([mock_mylist_with_video])
            actual = MylistWithVideoList.create(mylist_list, mylist_mylist_info_db)
            self.assertEqual(expect, actual)

            mylist_list = [self._get_mylist()]
            expect = MylistWithVideoList([mock_mylist_with_video])
            actual = MylistWithVideoList.create(mylist_list, mylist_mylist_info_db)
            self.assertEqual(expect, actual)

            mylist_list = [self._get_mylist(), self._get_mylist_dict()]
            with self.assertRaises(ValueError):
                actual = MylistWithVideoList.create(mylist_list, mylist_mylist_info_db)

            with self.assertRaises(ValueError):
                actual = MylistWithVideoList.create("invalid_arg", mylist_mylist_info_db)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
