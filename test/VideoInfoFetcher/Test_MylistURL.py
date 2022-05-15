# coding: utf-8
"""MylistURL のテスト

MylistURL の各種機能をテストする
"""
import re
import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.VideoInfoFetcher.URL import URL
from NNMM.VideoInfoFetcher.MylistURL import MylistURL


class TestMylistURL(unittest.TestCase):
    def test_MylistURLInit(self):
        """MylistURL の初期化後の状態をテストする
        """
        # 正常系
        # 通常のマイリストページのURL（クエリ付き）
        EXPECT_RSS_URL_SUFFIX = "?rss=2.0"
        url = URL("https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo")
        mylist_url = MylistURL(url)
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
            mylist_url = MylistURL(url)
            mylist_url.url = URL("https://www.nicovideo.jp/user/1234567/mylist/23456789")

        # マイリストページのURLでない
        url = URL("https://不正なURLアドレス/user/1234567/mylist/12345678")
        with self.assertRaises(ValueError):
            mylist_url = MylistURL(url)

    def test_create(self):
        """create のテスト
        """
        # 正常系
        # 文字列
        url = "https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo"
        mylist_url = MylistURL.create(url)
        self.assertEqual(url, mylist_url.original_url)

        # URL
        url = URL("https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo")
        mylist_url = MylistURL.create(url)
        self.assertEqual(url, mylist_url.url)

        # 異常系
        # URLを表す文字列でない（URLのエラー）
        url = "不正なURL"
        with self.assertRaises(ValueError):
            mylist_url = MylistURL.create(url)

    def test_is_valid(self):
        """is_valid のテスト
        """
        # 正常系
        # 文字列
        url = "https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo"
        actual = MylistURL.is_valid(url)
        self.assertEqual(True, actual)

        # URL
        url = URL("https://www.nicovideo.jp/user/1234567/mylist/12345678?ref=pc_mypage_nicorepo")
        actual = MylistURL.is_valid(url)
        self.assertEqual(True, actual)

        # 異常系
        # マイリストページのURLでない
        url = "https://不正なURLアドレス/user/1234567/mylist/12345678"
        actual = MylistURL.is_valid(url)
        self.assertEqual(False, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
