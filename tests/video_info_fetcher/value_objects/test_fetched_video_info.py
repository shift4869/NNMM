import sys
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime

import freezegun

from nnmm.video_info_fetcher.value_objects.fetched_api_video_info import FetchedAPIVideoInfo
from nnmm.video_info_fetcher.value_objects.fetched_page_video_info import FetchedPageVideoInfo
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


class TestFetchedVideoInfo(unittest.TestCase):
    def make_instance(self, max_index_num: int = 5) -> FetchedVideoInfo:
        n = max_index_num
        userid = Userid(str(n) * 7)
        mylistid = Mylistid(str(n) * 8)
        showname = Showname("「testマイリスト」-test_userさんのマイリスト")
        myshowname = Myshowname("「testマイリスト」")
        mylist_url = UserMylistURL.create(f"https://www.nicovideo.jp/user/{userid.id}/mylist/{mylistid.id}")
        title_list = TitleList.create([f"テスト動画_{i}" for i in range(n)])
        uploaded_at_list = UploadedAtList.create([f"2023-03-28 00:00:{i % 10:02}" for i in range(n)])
        registered_at_list = RegisteredAtList.create([f"2023-03-28 00:01:{i % 10:02}" for i in range(n)])
        video_url_list = VideoURLList.create([f"https://www.nicovideo.jp/watch/sm{i + 10000000}" for i in range(n)])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1" for i in range(n)])
        no = list(range(1, len(video_id_list) + 1))

        fvi = FetchedVideoInfo(
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
        return fvi

    def test_init(self):
        n = 5
        userid = Userid(str(n) * 7)
        mylistid = Mylistid(str(n) * 8)
        showname = Showname("「testマイリスト」-test_userさんのマイリスト")
        myshowname = Myshowname("「testマイリスト」")
        mylist_url = UserMylistURL.create(f"https://www.nicovideo.jp/user/{userid.id}/mylist/{mylistid.id}")
        title_list = TitleList.create([f"テスト動画_{i}" for i in range(n)])
        uploaded_at_list = UploadedAtList.create([f"2023-03-28 00:00:{i % 10:02}" for i in range(n)])
        registered_at_list = RegisteredAtList.create([f"2023-03-28 00:01:{i % 10:02}" for i in range(n)])
        video_url_list = VideoURLList.create([f"https://www.nicovideo.jp/watch/sm{i + 10000000}" for i in range(n)])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1" for i in range(n)])
        no = list(range(1, len(video_id_list) + 1))

        fvi = self.make_instance()
        self.assertEqual(no, fvi.no)
        self.assertEqual(userid, fvi.userid)
        self.assertEqual(mylistid, fvi.mylistid)
        self.assertEqual(showname, fvi.showname)
        self.assertEqual(myshowname, fvi.myshowname)
        self.assertEqual(mylist_url, fvi.mylist_url)
        self.assertEqual(video_id_list, fvi.video_id_list)
        self.assertEqual(title_list, fvi.title_list)
        self.assertEqual(uploaded_at_list, fvi.uploaded_at_list)
        self.assertEqual(registered_at_list, fvi.registered_at_list)
        self.assertEqual(video_url_list, fvi.video_url_list)
        self.assertEqual(username_list, fvi.username_list)

        EXPECT_RESULT_DICT_COLS = (
            "no",
            "video_id",
            "title",
            "username",
            "status",
            "uploaded_at",
            "registered_at",
            "video_url",
            "mylist_url",
            "showname",
            "mylistname",
        )
        self.assertEqual(EXPECT_RESULT_DICT_COLS, FetchedVideoInfo.RESULT_DICT_COLS)

        expect_result_dict = []
        zipped_list = zip(
            no, video_id_list, title_list, uploaded_at_list, registered_at_list, username_list, video_url_list
        )
        for n, video_id, title, uploaded_at, registered_at, username, video_url in zipped_list:
            value_list = [
                n,
                video_id.id,
                title.name,
                username.name,
                "",
                uploaded_at.dt_str,
                registered_at.dt_str,
                video_url.video_url,
                mylist_url.non_query_url,
                showname.name,
                myshowname.name,
            ]
            expect_result_dict.append(dict(zip(EXPECT_RESULT_DICT_COLS, value_list)))
        self.assertEqual(expect_result_dict, fvi.result_dict)
        self.assertEqual(len(no), len(fvi))

        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            fvi = self.make_instance()
            fvi.title_list = TitleList.create(["テスト動画2"])

    def test_is_valid(self):
        instance = self.make_instance(5)
        another_title_list = TitleList.create(["テスト動画1", "テスト動画2"])

        p = (
            instance.no,
            instance.userid,
            instance.mylistid,
            instance.showname,
            instance.myshowname,
            instance.mylist_url,
            instance.video_id_list,
            instance.title_list,
            instance.uploaded_at_list,
            instance.registered_at_list,
            instance.video_url_list,
            instance.username_list,
        )
        params_list = [
            (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11]),
            (None, p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11]),
            (p[0], None, p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11]),
            (p[0], p[1], None, p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11]),
            (p[0], p[1], p[2], None, p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11]),
            (p[0], p[1], p[2], p[3], None, p[5], p[6], p[7], p[8], p[9], p[10], p[11]),
            (p[0], p[1], p[2], p[3], p[4], None, p[6], p[7], p[8], p[9], p[10], p[11]),
            (p[0], p[1], p[2], p[3], p[4], p[5], None, p[7], p[8], p[9], p[10], p[11]),
            (p[0], p[1], p[2], p[3], p[4], p[5], p[6], None, p[8], p[9], p[10], p[11]),
            (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], None, p[9], p[10], p[11]),
            (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], None, p[10], p[11]),
            (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], None, p[11]),
            (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], None),
            (p[0], p[1], p[2], p[3], p[4], p[5], p[6], another_title_list, p[8], p[9], p[10], p[11]),
        ]

        for i, params in enumerate(params_list):
            if i == 0:
                fvi = FetchedVideoInfo(
                    params[0],
                    params[1],
                    params[2],
                    params[3],
                    params[4],
                    params[5],
                    params[6],
                    params[7],
                    params[8],
                    params[9],
                    params[10],
                    params[11],
                )
                self.assertEqual(True, fvi._is_valid())
            else:
                with self.assertRaises((TypeError, ValueError)):
                    fvi = FetchedVideoInfo(
                        params[0],
                        params[1],
                        params[2],
                        params[3],
                        params[4],
                        params[5],
                        params[6],
                        params[7],
                        params[8],
                        params[9],
                        params[10],
                        params[11],
                    )

    def test_make_result_dict(self):
        self.enterContext(freezegun.freeze_time("2023-04-01 00:01:00"))
        instance = self.make_instance(5)
        EXPECT_RESULT_DICT_COLS = (
            "no",
            "video_id",
            "title",
            "username",
            "status",
            "uploaded_at",
            "registered_at",
            "video_url",
            "mylist_url",
            "showname",
            "mylistname",
        )
        for is_future_time in [False, True]:
            if is_future_time:
                self.enterContext(freezegun.freeze_time("2023-03-28 00:01:00"))
            expect_result_dict = []
            now_date = datetime.now()
            zipped_list = zip(
                instance.no,
                instance.video_id_list,
                instance.title_list,
                instance.uploaded_at_list,
                instance.registered_at_list,
                instance.username_list,
                instance.video_url_list,
            )
            for n, video_id, title, uploaded_at, registered_at, username, video_url in zipped_list:
                if now_date < datetime.strptime(registered_at.dt_str, RegisteredAtList.DESTINATION_DATETIME_FORMAT):
                    continue
                value_list = [
                    n,
                    video_id.id,
                    title.name,
                    username.name,
                    "",
                    uploaded_at.dt_str,
                    registered_at.dt_str,
                    video_url.video_url,
                    instance.mylist_url.non_query_url,
                    instance.showname.name,
                    instance.myshowname.name,
                ]
                expect_result_dict.append(dict(zip(EXPECT_RESULT_DICT_COLS, value_list)))
            self.assertEqual(expect_result_dict, instance._make_result_dict())

        self.enterContext(freezegun.freeze_time("2023-04-01 00:01:00"))
        instance = self.make_instance(5)
        actual_result_dict = instance._make_result_dict()
        self.assertEqual(instance.result_dict, actual_result_dict)
        self.assertEqual(instance.result, actual_result_dict)

    def test_to_dict(self):
        instance = self.make_instance(5)

        expect_result_dict = []
        zipped_list = zip(
            instance.no,
            instance.video_id_list,
            instance.title_list,
            instance.uploaded_at_list,
            instance.registered_at_list,
            instance.username_list,
            instance.video_url_list,
        )
        for n, video_id, title, uploaded_at, registered_at, username, video_url in zipped_list:
            value_list = [
                n,
                video_id.id,
                title.name,
                username.name,
                "",
                uploaded_at.dt_str,
                registered_at.dt_str,
                video_url.video_url,
                instance.mylist_url.non_query_url,
                instance.showname.name,
                instance.myshowname.name,
            ]
            expect_result_dict.append(dict(zip(FetchedVideoInfo.RESULT_DICT_COLS, value_list)))

        expect = {
            "no": instance.no,
            "userid": instance.userid,
            "mylistid": instance.mylistid,
            "showname": instance.showname,
            "myshowname": instance.myshowname,
            "mylist_url": instance.mylist_url,
            "video_id_list": instance.video_id_list,
            "title_list": instance.title_list,
            "uploaded_at_list": instance.uploaded_at_list,
            "registered_at_list": instance.registered_at_list,
            "video_url_list": instance.video_url_list,
            "username_list": instance.username_list,
            "result_dict": expect_result_dict,
        }
        actual = instance.to_dict()
        self.assertEqual(expect, actual)

    def test_merge(self):
        instance = self.make_instance(5)
        fvi_page = FetchedPageVideoInfo(
            instance.no,
            instance.userid,
            instance.mylistid,
            instance.showname,
            instance.myshowname,
            instance.mylist_url,
            instance.video_id_list,
            instance.title_list,
            instance.registered_at_list,
            instance.video_url_list,
        )
        fvi_api = FetchedAPIVideoInfo(
            instance.no,
            instance.video_id_list,
            instance.title_list,
            instance.uploaded_at_list,
            instance.video_url_list,
            instance.username_list,
        )
        fvi_d = FetchedVideoInfo.merge(fvi_page, fvi_api)
        self.assertEqual(instance, fvi_d)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
