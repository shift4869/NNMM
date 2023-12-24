"""UserMylistURL のテスト

UserMylistURL の各種機能をテストする
"""

import re
import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.video_info_fetcher.value_objects.url import URL
from NNMM.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL


class TestUserMylistURL(unittest.TestCase):
    def test_MylistURLInit(self):
        """UserMylistURL の初期化後の状態をテストする"""
        # 正常系
        # 通常のマイリストページのURL（クエリ付き）
        EXPECT_RSS_URL_SUFFIX = "?rss=2.0"
        url = URL("https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo")
        mylist_url = UserMylistURL(url)
        self.assertEqual(url, mylist_url.url)
        self.assertEqual(url.non_query_url, mylist_url.non_query_url)
        self.assertEqual(url.original_url, mylist_url.original_url)

        non_user_url = re.sub("/user/[0-9]+", "", str(url.non_query_url))
        self.assertEqual(non_user_url + EXPECT_RSS_URL_SUFFIX, mylist_url.fetch_url)
        self.assertEqual(url.non_query_url, mylist_url.mylist_url)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        url = URL("https://www.nicovideo.jp/user/1234567/mylist/12345678")
        with self.assertRaises(FrozenInstanceError):
            mylist_url = UserMylistURL(url)
            mylist_url.url = URL("https://www.nicovideo.jp/user/1234567/mylist/23456789")

    def test_create(self):
        """create のテスト"""
        # 正常系
        # 文字列
        url = "https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo"
        mylist_url = UserMylistURL.create(url)
        self.assertEqual(url, mylist_url.original_url)

        # URL
        url = URL("https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo")
        mylist_url = UserMylistURL.create(url)
        self.assertEqual(url, mylist_url.url)

        # 異常系
        # URLを表す文字列でない（URLのエラー）
        url = "不正なURL"
        with self.assertRaises(ValueError):
            mylist_url = UserMylistURL.create(url)

    def test_is_valid(self):
        """is_valid のテスト"""
        # 正常系
        # 文字列
        url = "https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo"
        actual = UserMylistURL.is_valid(url)
        self.assertEqual(True, actual)

        # URL
        url = URL("https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo")
        actual = UserMylistURL.is_valid(url)
        self.assertEqual(True, actual)

        # 異常系
        # マイリストページのURLでない
        url = "https://不正なURLアドレス/user/1234567/mylist/12345678"
        with self.assertRaises(ValueError):
            actual = UserMylistURL.is_valid(url)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
