"""UploadedURL のテスト

UploadedURL の各種機能をテストする
"""

import re
import sys
import unittest
from dataclasses import FrozenInstanceError

from nnmm.video_info_fetcher.value_objects.mylistid import Mylistid
from nnmm.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.userid import Userid


class TestUploadedURL(unittest.TestCase):
    def test_UploadedURLInit(self):
        """UploadedURL の初期化後の状態をテストする"""
        # 正常系
        # 通常の投稿動画ページのURL（クエリ付き）
        EXPECT_RSS_URL_SUFFIX = "?rss=2.0"
        url = URL("https://www.nicovideo.jp/user/1234567/video?ref=pc_mypage_nicorepo")
        uploaded_url = UploadedURL(url)
        self.assertEqual(url.non_query_url, uploaded_url.non_query_url)
        self.assertEqual(url.original_url, uploaded_url.original_url)
        self.assertEqual(url.non_query_url + EXPECT_RSS_URL_SUFFIX, uploaded_url.fetch_url)

        non_query_url = uploaded_url.non_query_url
        userid = re.findall(UploadedURL.UPLOADED_URL_PATTERN, non_query_url)[0]
        self.assertEqual(Userid(userid), uploaded_url.userid)
        self.assertEqual(Mylistid(""), uploaded_url.mylistid)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        url = "https://www.nicovideo.jp/user/1234567/video"
        with self.assertRaises(FrozenInstanceError):
            uploaded_url = UploadedURL(url)
            uploaded_url.original_url = url + "FrozenError"

    def test_create(self):
        """create のテスト"""
        # 正常系
        # 文字列
        url = "https://www.nicovideo.jp/user/1234567/video?ref=pc_mypage_nicorepo"
        uploaded_url = UploadedURL.create(url)
        self.assertEqual(url, uploaded_url.original_url)

        # URL
        url = URL("https://www.nicovideo.jp/user/1234567/video?ref=pc_mypage_nicorepo")
        uploaded_url = UploadedURL.create(url)
        self.assertEqual(url.original_url, uploaded_url.original_url)
        self.assertEqual(url.non_query_url, uploaded_url.non_query_url)

        # 異常系
        # URLを表す文字列でない（URLのエラー）
        url = "不正なURL"
        with self.assertRaises(ValueError):
            uploaded_url = UploadedURL.create(url)

    def test_is_valid_mylist_url(self):
        """is_valid_mylist_url のテスト"""
        # 正常系
        # 文字列
        url = "https://www.nicovideo.jp/user/1234567/video?ref=pc_mypage_nicorepo"
        actual = UploadedURL.is_valid_mylist_url(url)
        self.assertEqual(True, actual)

        # URL
        url = URL("https://www.nicovideo.jp/user/1234567/video?ref=pc_mypage_nicorepo")
        actual = UploadedURL.is_valid_mylist_url(url)
        self.assertEqual(True, actual)

        # 異常系
        # 投稿動画ページのURLでない
        url = "https://不正なURLアドレス/user/1234567/video"
        actual = UploadedURL.is_valid_mylist_url(url)
        self.assertEqual(False, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
