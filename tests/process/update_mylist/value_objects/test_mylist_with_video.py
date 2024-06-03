import sys
import unittest

from mock import MagicMock

from nnmm.model import Mylist
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from nnmm.process.update_mylist.value_objects.typed_mylist import TypedMylist
from nnmm.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from nnmm.process.update_mylist.value_objects.video_dict_list import VideoDictList


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
            "updated_at": "2023-12-21 12:34:57",
            "checked_at": "2023-12-21 12:34:58",
            "check_interval": "15分",
            "check_failed_count": 0,
            "is_include_new": False,
        }

    def _get_video_dict(self, mylist_url: str, index: int = 1) -> dict:
        return {
            "id": index,
            "video_id": f"sm{index:08}",
            "title": f"title{index}",
            "username": f"username_{index}",
            "status": "未視聴",
            "uploaded_at": "2023-12-21 12:34:56",
            "registered_at": "2023-12-21 12:34:57",
            "video_url": f"https://www.nicovideo.jp/watch/sm{index:08}",
            "mylist_url": mylist_url,
            "created_at": "2023-12-21 12:34:58",
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
            mylist["is_include_new"],
        )

    def test_init(self):
        typed_mylist = MagicMock(spec=TypedMylist)
        typed_video_list = MagicMock(spec=TypedVideoList)
        instance = MylistWithVideo(typed_mylist, typed_video_list)
        self.assertEqual(typed_mylist, instance._typed_mylist)
        self.assertEqual(typed_video_list, instance._video_list)
        self.assertEqual(typed_mylist, instance.mylist)
        self.assertEqual(typed_video_list, instance.video_list)

        with self.assertRaises(ValueError):
            instance = MylistWithVideo("invalid", typed_video_list)
        with self.assertRaises(ValueError):
            instance = MylistWithVideo(typed_mylist, "invalid")

    def test_create(self):
        mock_mylist_info_db = MagicMock(spec=MylistInfoDBController)

        def f(mylist_url):
            return [self._get_video_dict(mylist_url)]

        mock_mylist_info_db.select_from_mylist_url.side_effect = f

        typed_mylist = TypedMylist.create(self._get_mylist_dict())
        mylist_url = typed_mylist.url.non_query_url
        video_dict_list = VideoDictList.create([self._get_video_dict(mylist_url)])
        typed_video_list = video_dict_list.to_typed_video_list()
        expect = MylistWithVideo(typed_mylist, typed_video_list)
        actual = MylistWithVideo.create(typed_mylist, mock_mylist_info_db)
        self.assertEqual(expect, actual)

        with self.assertRaises(ValueError):
            instance = MylistWithVideo.create("invalid", mock_mylist_info_db)
        with self.assertRaises(ValueError):
            instance = MylistWithVideo.create(typed_mylist, "invalid")


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
