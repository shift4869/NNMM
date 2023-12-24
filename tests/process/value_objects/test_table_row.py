import sys
import unittest
from collections import namedtuple
from copy import deepcopy
from dataclasses import FrozenInstanceError

from NNMM.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL
from NNMM.video_info_fetcher.value_objects.registered_at import RegisteredAt
from NNMM.process.value_objects.table_row import Status, TableRow, TableRowTuple
from NNMM.video_info_fetcher.value_objects.title import Title
from NNMM.video_info_fetcher.value_objects.uploaded_at import UploadedAt
from NNMM.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from NNMM.video_info_fetcher.value_objects.username import Username
from NNMM.video_info_fetcher.value_objects.video_url import VideoURL
from NNMM.video_info_fetcher.value_objects.videoid import Videoid


class TestTableRow(unittest.TestCase):
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
        }

    def _make_row(self, index: int = 1) -> list[str]:
        return list(self._make_video_dict(index).values())

    def _get_instance(self) -> TableRow:
        return TableRow.create(self._make_row())

    def test_init(self):
        row_index = 1
        video_id = Videoid("sm12345678")
        title = Title("title_1")
        username = Username("username_1")
        status = Status("未視聴")
        uploaded_at = UploadedAt("2023-12-22 12:34:56")
        registered_at = RegisteredAt("2023-12-22 12:34:56")
        video_url = VideoURL.create("https://www.nicovideo.jp/watch/sm12345678")
        mylist_url = UploadedURL.create("https://www.nicovideo.jp/user/10000001/video")
        COLS_NAME = [
            "No.",
            "動画ID",
            "動画名",
            "投稿者",
            "状況",
            "投稿日時",
            "登録日時",
            "動画URL",
            "所属マイリストURL",
        ]

        instance = TableRow(
            row_index, video_id, title, username, status, uploaded_at, registered_at, video_url, mylist_url
        )
        self.assertEqual(row_index, instance.row_number)
        self.assertEqual(video_id, instance.video_id)
        self.assertEqual(title, instance.title)
        self.assertEqual(username, instance.username)
        self.assertEqual(status, instance.status)
        self.assertEqual(uploaded_at, instance.uploaded_at)
        self.assertEqual(registered_at, instance.registered_at)
        self.assertEqual(video_url, instance.video_url)
        self.assertEqual(mylist_url, instance.mylist_url)
        self.assertEqual(COLS_NAME, TableRow.COLS_NAME)

        with self.assertRaises(ValueError):
            instance = TableRow(
                0, video_id, title, username, status, uploaded_at, registered_at, video_url, mylist_url
            )

        with self.assertRaises(FrozenInstanceError):
            instance.row_number = -1

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
            ]
            t[index] = "invalid"
            return Params._make(t)

        params_list = [make_params(i) for i in range(len(cols))]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = TableRow(*params)

    def test_fields(self):
        instance = self._get_instance()
        actual = instance.fields
        expect = TableRowTuple._fields
        self.assertEqual(expect, actual)

    def test_keys(self):
        instance = self._get_instance()
        actual = instance.keys()
        expect = TableRowTuple._fields
        self.assertEqual(expect, actual)

    def test_values(self):
        instance = self._get_instance()
        actual = instance.values()
        self.assertEqual(
            [
                instance.row_number,
                instance.video_id,
                instance.title,
                instance.username,
                instance.status,
                instance.uploaded_at,
                instance.registered_at,
                instance.video_url,
                instance.mylist_url,
            ],
            actual,
        )

    def test_clone(self):
        instance = self._get_instance()
        actual = instance.clone()
        self.assertEqual(instance, actual)

    def test_to_row(self):
        table_row = self._make_row()
        instance = self._get_instance()
        actual = instance.to_row()
        self.assertEqual(table_row, actual)

    def test_to_namedtuple(self):
        instance = self._get_instance()
        actual = instance.to_namedtuple()
        expect = TableRowTuple._make(instance.values())
        self.assertEqual(expect, actual)

    def test_to_typed_dict(self):
        instance = self._get_instance()
        actual = instance.to_typed_dict()
        expect = instance.to_namedtuple()._asdict()
        self.assertEqual(expect, actual)

    def test_to_dict(self):
        table_row = self._make_row()
        instance = self._get_instance()
        actual = instance.to_dict()
        expect = dict(zip(TableRowTuple._fields, table_row))
        self.assertEqual(expect, actual)

    def test_replace_from_typed_value(self):
        instance = self._get_instance()
        video_dict = self._make_row(1)
        after_table_row = TableRow.create(self._make_row(2))
        after_table_row_dict = {
            "row_index": after_table_row.row_number,
            "video_id": after_table_row.video_id,
            "title": after_table_row.title,
            "username": after_table_row.username,
            "status": after_table_row.status,
            "uploaded_at": after_table_row.uploaded_at,
            "registered_at": after_table_row.registered_at,
            "video_url": after_table_row.video_url,
            "mylist_url": after_table_row.mylist_url,
        }
        after_str_row_dict = {
            "row_index": after_table_row.row_number,
            "video_id": after_table_row.video_id.id,
            "title": after_table_row.title.name,
            "username": after_table_row.username.name,
            "status": after_table_row.status.value,
            "uploaded_at": after_table_row.uploaded_at.dt_str,
            "registered_at": after_table_row.registered_at.dt_str,
            "video_url": after_table_row.video_url.non_query_url,
            "mylist_url": after_table_row.mylist_url.non_query_url,
        }
        for key, value in after_table_row_dict.items():
            kargs = {key: value}
            actual = instance.replace_from_typed_value(**kargs)
            after_dict = dict(zip(after_str_row_dict.keys(), deepcopy(video_dict)))
            expect_row_dict = after_dict | {key: after_str_row_dict[key]}
            expect = TableRow.create(list(expect_row_dict.values()))
            self.assertEqual(expect, actual)

        with self.assertRaises(ValueError):
            actual = instance.replace_from_typed_value(invalid_key="invalid")

        with self.assertRaises(ValueError):
            actual = instance.replace_from_typed_value(row_index="invalid")

    def test_replace_from_str(self):
        instance = self._get_instance()
        video_dict = self._make_row(1)
        after_table_row = TableRow.create(self._make_row(2))
        after_str_row_dict = {
            "row_index": after_table_row.row_number,
            "video_id": after_table_row.video_id.id,
            "title": after_table_row.title.name,
            "username": after_table_row.username.name,
            "status": after_table_row.status.value,
            "uploaded_at": after_table_row.uploaded_at.dt_str,
            "registered_at": after_table_row.registered_at.dt_str,
            "video_url": after_table_row.video_url.non_query_url,
            "mylist_url": after_table_row.mylist_url.non_query_url,
        }
        for key, value in after_str_row_dict.items():
            kargs = {key: value}
            actual = instance.replace_from_str(**kargs)
            after_dict = dict(zip(after_str_row_dict.keys(), deepcopy(video_dict)))
            expect_row_dict = after_dict | kargs
            expect = TableRow.create(list(expect_row_dict.values()))
            self.assertEqual(expect, actual)

    def test_create(self):
        row_list = self._make_row(1)
        video_dict = self._make_video_dict(1)
        actual = TableRow.create(row_list)
        expect = TableRow(
            int(video_dict["id"]),
            Videoid(video_dict["video_id"]),
            Title(video_dict["title"]),
            Username(video_dict["username"]),
            Status(video_dict["status"]),
            UploadedAt(video_dict["uploaded_at"]),
            RegisteredAt(video_dict["registered_at"]),
            VideoURL.create(video_dict["video_url"]),
            UploadedURL.create(video_dict["mylist_url"]),
        )
        self.assertEqual(expect, actual)

        row_list = self._make_row(2)
        video_dict = self._make_video_dict(2)
        actual = TableRow.create(row_list)
        expect = TableRow(
            int(video_dict["id"]),
            Videoid(video_dict["video_id"]),
            Title(video_dict["title"]),
            Username(video_dict["username"]),
            Status(video_dict["status"]),
            UploadedAt(video_dict["uploaded_at"]),
            RegisteredAt(video_dict["registered_at"]),
            VideoURL.create(video_dict["video_url"]),
            UserMylistURL.create(video_dict["mylist_url"]),
        )
        self.assertEqual(expect, actual)

        # cls でインスタンス生成時にエラー
        with self.assertRaises(ValueError):
            row_list = self._make_row(1)
            row_list[8] = "invalid"
            actual = TableRow.create(row_list)

        # row の長さが異なる
        with self.assertRaises(ValueError):
            row_list = self._make_row(1)
            row_list.append("invalid")
            actual = TableRow.create(row_list)

        # 一部がstrでない
        with self.assertRaises(ValueError):
            row_list = self._make_row(1)
            row_list[8] = -1
            actual = TableRow.create(row_list)

        # row_number がintでもstrでない
        with self.assertRaises(ValueError):
            row_list = self._make_row(1)
            row_list[0] = []
            actual = TableRow.create(row_list)

        # row がlistでない
        with self.assertRaises(ValueError):
            actual = TableRow.create("invalid")


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
