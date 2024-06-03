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
from nnmm.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL
from nnmm.video_info_fetcher.value_objects.userid import Userid
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


class TestFetchedPageVideoInfo(unittest.TestCase):
    def test_FetchedPageVideoInfoInit(self):
        """FetchedPageVideoInfo の初期化後の状態をテストする"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = UserMylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        title_list = TitleList.create(["テスト動画"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
        fvi_page = FetchedPageVideoInfo(
            no,
            userid,
            mylistid,
            showname,
            myshowname,
            mylist_url,
            video_id_list,
            title_list,
            registered_at_list,
            video_url_list,
        )
        self.assertEqual(no, fvi_page.no)
        self.assertEqual(userid, fvi_page.userid)
        self.assertEqual(mylistid, fvi_page.mylistid)
        self.assertEqual(showname, fvi_page.showname)
        self.assertEqual(myshowname, fvi_page.myshowname)
        self.assertEqual(mylist_url, fvi_page.mylist_url)
        self.assertEqual(video_id_list, fvi_page.video_id_list)
        self.assertEqual(title_list, fvi_page.title_list)
        self.assertEqual(registered_at_list, fvi_page.registered_at_list)
        self.assertEqual(video_url_list, fvi_page.video_url_list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                registered_at_list,
                video_url_list,
            )
            fvi_page.title_list = TitleList.create(["テスト動画2"])

    def test_is_valid(self):
        """_is_valid のテスト"""
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = UserMylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        title_list = TitleList.create(["テスト動画"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
        fvi_page = FetchedPageVideoInfo(
            no,
            userid,
            mylistid,
            showname,
            myshowname,
            mylist_url,
            video_id_list,
            title_list,
            registered_at_list,
            video_url_list,
        )
        self.assertEqual(True, fvi_page._is_valid())

        # 異常系
        # userid 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                None,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                registered_at_list,
                video_url_list,
            )
        # mylistid 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                None,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                registered_at_list,
                video_url_list,
            )
        # showname 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                mylistid,
                None,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                registered_at_list,
                video_url_list,
            )
        # myshowname 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                None,
                mylist_url,
                video_id_list,
                title_list,
                registered_at_list,
                video_url_list,
            )
        # mylist_url 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                None,
                video_id_list,
                title_list,
                registered_at_list,
                video_url_list,
            )
        # video_id_list 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                None,
                title_list,
                registered_at_list,
                video_url_list,
            )
        # title_list 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                None,
                registered_at_list,
                video_url_list,
            )
        # registered_at_list 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no, userid, mylistid, showname, myshowname, mylist_url, video_id_list, title_list, None, video_url_list
            )
        # video_url_list 指定が不正
        with self.assertRaises(TypeError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                registered_at_list,
                None,
            )
        # no 指定が不正
        with self.assertRaises(ValueError):
            fvi_page = FetchedPageVideoInfo(
                [],
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                registered_at_list,
                video_url_list,
            )
        # list の長さが同じでない
        title_list = TitleList.create(["テスト動画1", "テスト動画2"])
        with self.assertRaises(ValueError):
            fvi_page = FetchedPageVideoInfo(
                no,
                userid,
                mylistid,
                showname,
                myshowname,
                mylist_url,
                video_id_list,
                title_list,
                registered_at_list,
                video_url_list,
            )

    def test_to_dict(self):
        """to_dict のテスト"""
        title_list = TitleList.create(["テスト動画"])
        userid = Userid("1234567")
        mylistid = Mylistid("12345678")
        showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
        myshowname = Myshowname("「まとめマイリスト」")
        mylist_url = UserMylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        title_list = TitleList.create(["テスト動画"])
        registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
        fvi_page = FetchedPageVideoInfo(
            no,
            userid,
            mylistid,
            showname,
            myshowname,
            mylist_url,
            video_id_list,
            title_list,
            registered_at_list,
            video_url_list,
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
            "registered_at_list": registered_at_list,
            "video_url_list": video_url_list,
        }
        actual = fvi_page.to_dict()
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
