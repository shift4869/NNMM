"""VideoURL のテスト

VideoURL の各種機能をテストする
"""

import re
import sys
import unittest
from dataclasses import FrozenInstanceError

from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.videoid import Videoid


class TestVideoURL(unittest.TestCase):
    def test_VideoURLInit(self):
        """VideoURL の初期化後の状態をテストする"""
        # 正常系
        # 通常の動画URL（クエリ付き）
        url = URL("https://www.nicovideo.jp/watch/sm12345678?ref=pc_mypage_nicorepo")
        video_url = VideoURL(url)
        self.assertEqual(url, video_url.url)
        self.assertEqual(url.non_query_url, video_url.non_query_url)
        self.assertEqual(url.original_url, video_url.original_url)
        self.assertEqual(url.non_query_url, video_url.fetch_url)
        self.assertEqual(url.non_query_url, video_url.video_url)

        video_id = re.findall(VideoURL.VIDEO_URL_PATTERN, url.non_query_url)[0]
        self.assertEqual(Videoid(video_id), video_url.video_id)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        url = URL("https://www.nicovideo.jp/watch/sm12345678")
        with self.assertRaises(FrozenInstanceError):
            video_url = VideoURL(url)
            video_url.url = URL("https://www.nicovideo.jp/watch/sm23456789")

    def test_create(self):
        """create のテスト"""
        # 正常系
        # 文字列
        url = "https://www.nicovideo.jp/watch/sm12345678?ref=pc_mypage_nicorepo"
        video_url = VideoURL.create(url)
        self.assertEqual(url, video_url.original_url)

        # URL
        url = URL("https://www.nicovideo.jp/watch/sm12345678?ref=pc_mypage_nicorepo")
        video_url = VideoURL.create(url)
        self.assertEqual(url, video_url.url)

        # 異常系
        # URLを表す文字列でない（URLのエラー）
        url = "不正なURL"
        with self.assertRaises(ValueError):
            video_url = VideoURL.create(url)

    def test_is_valid(self):
        """is_valid のテスト"""
        # 正常系
        # 文字列
        url = "https://www.nicovideo.jp/watch/sm12345678?ref=pc_mypage_nicorepo"
        actual = VideoURL.is_valid(url)
        self.assertEqual(True, actual)

        # URL
        url = URL("https://www.nicovideo.jp/watch/sm12345678?ref=pc_mypage_nicorepo")
        actual = VideoURL.is_valid(url)
        self.assertEqual(True, actual)

        # 異常系
        # 末尾に動画IDがない
        url = "https://www.nicovideo.jp/watch/"
        actual = VideoURL.is_valid(url)
        self.assertEqual(False, actual)

        # 動画URLでない
        url = "https://不正なURLアドレス/watch/sm12345678"
        with self.assertRaises(ValueError):
            actual = VideoURL.is_valid(url)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
