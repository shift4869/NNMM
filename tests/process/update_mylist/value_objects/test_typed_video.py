import sys
import unittest
from collections import namedtuple
from copy import deepcopy
from dataclasses import FrozenInstanceError

from NNMM.process.update_mylist.value_objects.created_at import CreatedAt
from NNMM.process.update_mylist.value_objects.typed_video import TypedVideo
from NNMM.process.update_mylist.value_objects.video_row_index import VideoRowIndex
from NNMM.process.value_objects.table_row import Status
from NNMM.video_info_fetcher.value_objects.registered_at import RegisteredAt
from NNMM.video_info_fetcher.value_objects.title import Title
from NNMM.video_info_fetcher.value_objects.uploaded_at import UploadedAt
from NNMM.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from NNMM.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL
from NNMM.video_info_fetcher.value_objects.username import Username
from NNMM.video_info_fetcher.value_objects.video_url import VideoURL
from NNMM.video_info_fetcher.value_objects.videoid import Videoid


class TestTypedVideo(unittest.TestCase):
    def _make_video_dict(self, index: int = 1) -> dict[str, str]:
        uploaded_url = f"https://www.nicovideo.jp/user/1000000{index}/video"
        mylist_url = f"https://www.nicovideo.jp/user/1000000{index}/mylist/{index:08}"
        return {
            "id": str(index),
            "video_id": f"sm1234567{index}",
            "title": f"title_{index}",
            "username": f"username_{index}",
            "status": f"未視聴" if index == 1 else "",
            "uploaded_at": f"2023-12-22 12:34:5{index}",
            "registered_at": f"2023-12-22 12:34:5{index}",
            "video_url": f"https://www.nicovideo.jp/watch/sm1234567{index}",
            "mylist_url": uploaded_url if index == 1 else mylist_url,
            "created_at": f"2023-12-22 12:34:5{index}",
        }

    def _get_instance(self) -> TypedVideo:
        return TypedVideo.create(self._make_video_dict())

    def test_init(self):
        row_index = VideoRowIndex(1)
        video_id = Videoid("sm12345678")
        title = Title("title_1")
        username = Username("username_1")
        status = Status("未視聴")
        uploaded_at = UploadedAt("2023-12-22 12:34:56")
        registered_at = RegisteredAt("2023-12-22 12:34:56")
        video_url = VideoURL.create("https://www.nicovideo.jp/watch/sm12345678")
        mylist_url = UploadedURL.create("https://www.nicovideo.jp/user/10000001/video")
        created_at = CreatedAt("2023-12-22 12:34:56")

        instance = TypedVideo(
            row_index, video_id, title, username, status, uploaded_at, registered_at, video_url, mylist_url, created_at
        )
        self.assertEqual(row_index, instance.id)
        self.assertEqual(video_id, instance.video_id)
        self.assertEqual(title, instance.title)
        self.assertEqual(username, instance.username)
        self.assertEqual(status, instance.status)
        self.assertEqual(uploaded_at, instance.uploaded_at)
        self.assertEqual(registered_at, instance.registered_at)
        self.assertEqual(video_url, instance.video_url)
        self.assertEqual(mylist_url, instance.mylist_url)
        self.assertEqual(created_at, instance.created_at)

        with self.assertRaises(FrozenInstanceError):
            instance.id = -1

        cols = [
            "row_index",
            "video_id",
            "title",
            "username",
            "status",
            "uploaded_at",
            "registered_at",
            "video_url",
            "mylist_url",
            "created_at",
        ]
        Params = namedtuple("Params", cols)

        def make_params(index: int) -> Params:
            t = [
                row_index,
                video_id,
                title,
                username,
                status,
                uploaded_at,
                registered_at,
                video_url,
                mylist_url,
                created_at,
            ]
            t[index] = "invalid"
            return Params._make(t)

        params_list = [make_params(i) for i in range(len(cols))]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = TypedVideo(*params)

    def test_replace_from_typed_value(self):
        instance = self._get_instance()
        video_dict = self._make_video_dict(1)
        after_typed_video = TypedVideo.create(self._make_video_dict(2))
        after_typed_video_dict = {
            "id": after_typed_video.id,
            "video_id": after_typed_video.video_id,
            "title": after_typed_video.title,
            "username": after_typed_video.username,
            "status": after_typed_video.status,
            "uploaded_at": after_typed_video.uploaded_at,
            "registered_at": after_typed_video.registered_at,
            "video_url": after_typed_video.video_url,
            "mylist_url": after_typed_video.mylist_url,
            "created_at": after_typed_video.created_at,
        }
        after_str_video_dict = {
            "id": str(after_typed_video.id.index),
            "video_id": after_typed_video.video_id.id,
            "title": after_typed_video.title.name,
            "username": after_typed_video.username.name,
            "status": after_typed_video.status.value,
            "uploaded_at": after_typed_video.uploaded_at.dt_str,
            "registered_at": after_typed_video.registered_at.dt_str,
            "video_url": after_typed_video.video_url.non_query_url,
            "mylist_url": after_typed_video.mylist_url.non_query_url,
            "created_at": after_typed_video.created_at.dt_str,
        }
        for key, value in after_typed_video_dict.items():
            kargs = {key: value}
            actual = instance.replace_from_typed_value(**kargs)
            expect_video_dict = deepcopy(video_dict) | {key: after_str_video_dict[key]}
            expect = TypedVideo.create(expect_video_dict)
            self.assertEqual(expect, actual)

        with self.assertRaises(ValueError):
            actual = instance.replace_from_typed_value(invalid_key="invalid")

        with self.assertRaises(ValueError):
            actual = instance.replace_from_typed_value(id="invalid")

    def test_replace_from_str(self):
        instance = self._get_instance()
        video_dict = self._make_video_dict(1)
        after_typed_video = TypedVideo.create(self._make_video_dict(2))
        after_str_video_dict = {
            "id": str(after_typed_video.id.index),
            "video_id": after_typed_video.video_id.id,
            "title": after_typed_video.title.name,
            "username": after_typed_video.username.name,
            "status": after_typed_video.status.value,
            "uploaded_at": after_typed_video.uploaded_at.dt_str,
            "registered_at": after_typed_video.registered_at.dt_str,
            "video_url": after_typed_video.video_url.non_query_url,
            "mylist_url": after_typed_video.mylist_url.non_query_url,
            "created_at": after_typed_video.created_at.dt_str,
        }
        for key, value in after_str_video_dict.items():
            kargs = {key: value}
            actual = instance.replace_from_str(**kargs)
            expect_video_dict = deepcopy(video_dict) | kargs
            expect = TypedVideo.create(expect_video_dict)
            self.assertEqual(expect, actual)

    def test_to_dict(self):
        instance = self._get_instance()
        video_dict = self._make_video_dict(1)
        actual = instance.to_dict()
        self.assertEqual(video_dict, actual)

    def test_create(self):
        video_dict = self._make_video_dict(1)
        actual = TypedVideo.create(video_dict)
        expect = TypedVideo(
            VideoRowIndex(int(video_dict["id"])),
            Videoid(video_dict["video_id"]),
            Title(video_dict["title"]),
            Username(video_dict["username"]),
            Status(video_dict["status"]),
            UploadedAt(video_dict["uploaded_at"]),
            RegisteredAt(video_dict["registered_at"]),
            VideoURL.create(video_dict["video_url"]),
            UploadedURL.create(video_dict["mylist_url"]),
            CreatedAt(video_dict["created_at"]),
        )
        self.assertEqual(expect, actual)

        video_dict = self._make_video_dict(2)
        actual = TypedVideo.create(video_dict)
        expect = TypedVideo(
            VideoRowIndex(int(video_dict["id"])),
            Videoid(video_dict["video_id"]),
            Title(video_dict["title"]),
            Username(video_dict["username"]),
            Status(video_dict["status"]),
            UploadedAt(video_dict["uploaded_at"]),
            RegisteredAt(video_dict["registered_at"]),
            VideoURL.create(video_dict["video_url"]),
            UserMylistURL.create(video_dict["mylist_url"]),
            CreatedAt(video_dict["created_at"]),
        )
        self.assertEqual(expect, actual)

        with self.assertRaises(ValueError):
            video_dict = self._make_video_dict(1)
            video_dict["mylist_url"] = "invalid"
            actual = TypedVideo.create(video_dict)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
