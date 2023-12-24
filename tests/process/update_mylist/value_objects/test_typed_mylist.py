import sys
import unittest
from collections import namedtuple
from dataclasses import FrozenInstanceError

from NNMM.process.update_mylist.value_objects.check_interval import CheckInterval
from NNMM.process.update_mylist.value_objects.checked_at import CheckedAt
from NNMM.process.update_mylist.value_objects.created_at import CreatedAt
from NNMM.process.update_mylist.value_objects.mylist_row_index import MylistRowIndex
from NNMM.process.update_mylist.value_objects.typed_mylist import TypedMylist
from NNMM.process.update_mylist.value_objects.updated_at import UpdatedAt
from NNMM.util import IncludeNewStatus, MylistType
from NNMM.video_info_fetcher.value_objects.myshowname import Myshowname
from NNMM.video_info_fetcher.value_objects.showname import Showname
from NNMM.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from NNMM.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL
from NNMM.video_info_fetcher.value_objects.username import Username


class TestTypedMylist(unittest.TestCase):
    def test_init(self):
        row_index = MylistRowIndex(1)
        username = Username("username_1")
        mylistname = Myshowname("投稿動画")
        type = MylistType(MylistType.uploaded)
        showname = Showname("投稿者1さんの投稿動画")
        url = UploadedURL.create("https://www.nicovideo.jp/user/10000001/video")
        created_at = CreatedAt("2023-12-22 12:34:56")
        updated_at = UpdatedAt("2023-12-22 12:34:56")
        checked_at = CheckedAt("2023-12-22 12:34:56")
        check_interval = CheckInterval.create("15分")
        is_include_new = IncludeNewStatus(IncludeNewStatus.yes)

        instance = TypedMylist(
            row_index,
            username,
            mylistname,
            type,
            showname,
            url,
            created_at,
            updated_at,
            checked_at,
            check_interval,
            is_include_new,
        )
        self.assertEqual(row_index, instance.id)
        self.assertEqual(username, instance.username)
        self.assertEqual(mylistname, instance.mylistname)
        self.assertEqual(type, instance.type)
        self.assertEqual(showname, instance.showname)
        self.assertEqual(url, instance.url)
        self.assertEqual(created_at, instance.created_at)
        self.assertEqual(updated_at, instance.updated_at)
        self.assertEqual(checked_at, instance.checked_at)
        self.assertEqual(check_interval, instance.check_interval)
        self.assertEqual(is_include_new, instance.is_include_new)

        with self.assertRaises(FrozenInstanceError):
            instance.id = -1

        cols = [
            "row_index",
            "username",
            "mylistname",
            "type",
            "showname",
            "url",
            "created_at",
            "updated_at",
            "checked_at",
            "check_interval",
            "is_include_new",
        ]
        Params = namedtuple("Params", cols)

        def make_params(index: int) -> Params:
            t = [
                row_index,
                username,
                mylistname,
                type,
                showname,
                url,
                created_at,
                updated_at,
                checked_at,
                check_interval,
                is_include_new,
            ]
            t[index] = "invalid"
            return Params._make(t)

        params_list = [make_params(i) for i in range(len(cols))]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = TypedMylist(*params)

    def test_create(self):
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
        actual = TypedMylist.create(mylist_dict)
        expect = TypedMylist(
            MylistRowIndex(1),
            Username("username_1"),
            Myshowname("投稿動画"),
            MylistType(MylistType.uploaded),
            Showname("投稿者1さんの投稿動画"),
            UploadedURL.create("https://www.nicovideo.jp/user/10000001/video"),
            CreatedAt("2023-12-22 12:34:56"),
            UpdatedAt("2023-12-22 12:34:56"),
            CheckedAt("2023-12-22 12:34:56"),
            CheckInterval.create("15分"),
            IncludeNewStatus(True),
        )
        self.assertEqual(expect, actual)

        mylist_dict = {
            "id": 2,
            "username": "username_1",
            "mylistname": "マイリスト1",
            "type": "mylist",
            "showname": "「マイリスト1」-投稿者1さんの投稿動画",
            "url": "https://www.nicovideo.jp/user/1111111/mylist/10000001",
            "created_at": "2023-12-22 12:34:56",
            "updated_at": "2023-12-22 12:34:56",
            "checked_at": "2023-12-22 12:34:56",
            "check_interval": "15分",
            "is_include_new": False,
        }
        actual = TypedMylist.create(mylist_dict)
        expect = TypedMylist(
            MylistRowIndex(2),
            Username("username_1"),
            Myshowname("マイリスト1"),
            MylistType(MylistType.mylist),
            Showname("「マイリスト1」-投稿者1さんの投稿動画"),
            UserMylistURL.create("https://www.nicovideo.jp/user/1111111/mylist/10000001"),
            CreatedAt("2023-12-22 12:34:56"),
            UpdatedAt("2023-12-22 12:34:56"),
            CheckedAt("2023-12-22 12:34:56"),
            CheckInterval.create("15分"),
            IncludeNewStatus(False),
        )
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
