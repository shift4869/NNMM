"""FetchedPageVideoInfo のテスト

FetchedPageVideoInfo の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from nnmm.video_info_fetcher.value_objects.fetched_page_video_info import FetchedPageVideoInfo
from nnmm.video_info_fetcher.value_objects.mylistid import Mylistid
from nnmm.video_info_fetcher.value_objects.myshowname import Myshowname
from nnmm.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from nnmm.video_info_fetcher.value_objects.showname import Showname
from nnmm.video_info_fetcher.value_objects.title_list import TitleList
from nnmm.video_info_fetcher.value_objects.uploaded_at_list import UploadedAtList
from nnmm.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL
from nnmm.video_info_fetcher.value_objects.userid import Userid
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.username_list import UsernameList
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


class TestFetchedPageVideoInfo(unittest.TestCase):
    def test_FetchedPageVideoInfoInit(self):
        """FetchedPageVideoInfo の初期化後の状態をテストする"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        username = Username("shift4869")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = UserMylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:01:01"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:02"])
        username_list = UsernameList.create(["shift4869"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
        fvi_page = FetchedPageVideoInfo(
            no,
            userid,
            username,
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
        self.assertEqual(no, fvi_page.no)
        self.assertEqual(userid, fvi_page.userid)
        self.assertEqual(username, fvi_page.username)
        self.assertEqual(mylistid, fvi_page.mylistid)
        self.assertEqual(showname, fvi_page.showname)
        self.assertEqual(myshowname, fvi_page.myshowname)
        self.assertEqual(mylist_url, fvi_page.mylist_url)
        self.assertEqual(video_id_list, fvi_page.video_id_list)
        self.assertEqual(title_list, fvi_page.title_list)
        self.assertEqual(uploaded_at_list, fvi_page.uploaded_at_list)
        self.assertEqual(registered_at_list, fvi_page.registered_at_list)
        self.assertEqual(video_url_list, fvi_page.video_url_list)
        self.assertEqual(username_list, fvi_page.username_list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page.title_list = TitleList.create(["テスト動画2"])

    def test_is_valid(self):
        """_is_valid のテスト"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        username = Username("shift4869")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = UserMylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:01:01"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:02"])
        username_list = UsernameList.create(["shift4869"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
        fvi_page = FetchedPageVideoInfo(
            no,
            userid,
            username,
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
        self.assertEqual(True, fvi_page._is_valid())

        # 異常系
        # userid 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                None,
                username,
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
        # username 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                [],
                userid,
                username,
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
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                username,
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

    def test_to_dict(self):
        """to_dict のテスト"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        username = Username("shift4869")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = UserMylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:01:01"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:02"])
        username_list = UsernameList.create(["shift4869"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
        fvi_page = FetchedPageVideoInfo(
            no,
            userid,
            username,
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
            "username": username,
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
        }
        actual = fvi_page.to_dict()
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
