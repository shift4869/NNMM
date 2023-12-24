"""FetchedVideoInfo のテスト

FetchedVideoInfo の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo
from NNMM.video_info_fetcher.value_objects.mylist_url import MylistURL
from NNMM.video_info_fetcher.value_objects.mylistid import Mylistid
from NNMM.video_info_fetcher.value_objects.myshowname import Myshowname
from NNMM.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from NNMM.video_info_fetcher.value_objects.showname import Showname
from NNMM.video_info_fetcher.value_objects.title_list import TitleList
from NNMM.video_info_fetcher.value_objects.uploaded_at_list import UploadedAtList
from NNMM.video_info_fetcher.value_objects.userid import Userid
from NNMM.video_info_fetcher.value_objects.username_list import UsernameList
from NNMM.video_info_fetcher.value_objects.video_url_list import VideoURLList
from NNMM.video_info_fetcher.value_objects.videoid_list import VideoidList


class TestFetchedVideoInfo(unittest.TestCase):
    def test_FetchedVideoInfoInit(self):
        """FetchedVideoInfo の初期化後の状態をテストする"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = MylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
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
                mylist_url.mylist_url,
                showname.name,
                myshowname.name,
            ]
            expect_result_dict.append(dict(zip(EXPECT_RESULT_DICT_COLS, value_list)))
        self.assertEqual(expect_result_dict, fvi.result_dict)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
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
            fvi.title_list = TitleList.create(["テスト動画2"])

    def test_is_valid(self):
        """_is_valid のテスト"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = MylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
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
        self.assertEqual(True, fvi._is_valid())

        # 異常系
        # userid 指定が不正
        with self.assertRaises(TypeError):
            fvi = FetchedVideoInfo(
                no,
                None,
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
        # mylistid 指定が不正
        with self.assertRaises(TypeError):
            fvi = FetchedVideoInfo(
                no,
                userid,
                None,
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
        # showname 指定が不正
        with self.assertRaises(TypeError):
            fvi = FetchedVideoInfo(
                no,
                userid,
                mylistid,
                None,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                uploaded_at_list,
                registered_at_list,
                video_url_list,
                username_list,
            )
        # myshowname 指定が不正
        with self.assertRaises(TypeError):
            fvi = FetchedVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                None,
                mylist_url,
                video_id_list,
                title_list,
                uploaded_at_list,
                registered_at_list,
                video_url_list,
                username_list,
            )
        # mylist_url 指定が不正
        with self.assertRaises(TypeError):
            fvi = FetchedVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                None,
                video_id_list,
                title_list,
                uploaded_at_list,
                registered_at_list,
                video_url_list,
                username_list,
            )
        # video_id_list 指定が不正
        with self.assertRaises(TypeError):
            fvi = FetchedVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                None,
                title_list,
                uploaded_at_list,
                registered_at_list,
                video_url_list,
                username_list,
            )
        # title_list 指定が不正
        with self.assertRaises(TypeError):
            fvi = FetchedVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                None,
                uploaded_at_list,
                registered_at_list,
                video_url_list,
                username_list,
            )
        # uploaded_at_list 指定が不正
        with self.assertRaises(TypeError):
            fvi = FetchedVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                None,
                registered_at_list,
                video_url_list,
                username_list,
            )
        # registered_at_list 指定が不正
        with self.assertRaises(TypeError):
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
                None,
                video_url_list,
                username_list,
            )
        # video_url_list 指定が不正
        with self.assertRaises(TypeError):
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
                None,
                username_list,
            )
        # username_list 指定が不正
        with self.assertRaises(TypeError):
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
                None,
            )
        # no 指定が不正
        with self.assertRaises(ValueError):
            fvi = FetchedVideoInfo(
                [],
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
        # list の長さが同じでない
        title_list = TitleList.create(["テスト動画1", "テスト動画2"])
        with self.assertRaises(ValueError):
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

    def test_make_result_dict(self):
        """_make_result_dict のテスト"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = MylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1"])
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
                mylist_url.mylist_url,
                showname.name,
                myshowname.name,
            ]
            expect_result_dict.append(dict(zip(EXPECT_RESULT_DICT_COLS, value_list)))
        self.assertEqual(expect_result_dict, fvi._make_result_dict())

    def test_to_dict(self):
        """to_dict のテスト"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = MylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1"])
        no = list(range(1, len(video_id_list) + 1))

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
                mylist_url.mylist_url,
                showname.name,
                myshowname.name,
            ]
            expect_result_dict.append(dict(zip(FetchedVideoInfo.RESULT_DICT_COLS, value_list)))

        # 正常系
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
        expect = {
            "no": no,
            "userid": userid,
            "mylistid": mylistid,
            "showname": showname,
            "myshowname": myshowname,
            "mylist_url": mylist_url,
            "video_id_list": video_id_list,
            "title_list": title_list,
            "uploaded_at_list": uploaded_at_list,
            "registered_at_list": registered_at_list,
            "video_url_list": video_url_list,
            "username_list": username_list,
            "result_dict": expect_result_dict,
        }
        actual = fvi.to_dict()
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
