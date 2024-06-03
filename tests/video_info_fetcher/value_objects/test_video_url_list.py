"""VideoURLList のテスト

VideoURLList の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList


class TestVideoURLList(unittest.TestCase):
    def _get_urls(self):
        NUM = 5
        base_url = "https://www.nicovideo.jp/watch/sm1000000{}"
        return [base_url.format(i) for i in range(1, NUM + 1)]

    def _get_video_urls(self):
        video_url_strs = self._get_urls()
        return [VideoURL.create(r) for r in video_url_strs]

    def test_VideoURLListInit(self):
        """VideoURLList の初期化後の状態をテストする"""
        base_url = "https://www.nicovideo.jp/watch/sm1000000{}"
        video_url_strs = self._get_urls()
        video_urls = self._get_video_urls()

        # 正常系
        # VideoURL のリスト
        video_url_list = VideoURLList(video_urls)
        self.assertEqual(video_urls, video_url_list._list)

        # 空リスト
        video_url_list = VideoURLList([])
        self.assertEqual([], video_url_list._list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            video_url_list = VideoURLList(video_urls)
            video_url_list._list = [VideoURL.create(base_url.format(1))]

        # 引数がlistでない
        with self.assertRaises(TypeError):
            video_url_list = VideoURLList(base_url.format(1))

        # 引数がlist[VideoURL]でない
        with self.assertRaises(ValueError):
            video_url_list = VideoURLList(video_url_strs)

        # 引数のlistの要素のうち、一部がVideoURLでない
        num = len(video_urls)
        video_urls[num // 2] = base_url.format(num // 2)
        with self.assertRaises(ValueError):
            video_url_list = VideoURLList(video_urls)

    def test_iter_len(self):
        """iter と len のテスト"""
        video_urls = self._get_video_urls()
        video_url_list = VideoURLList(video_urls)
        self.assertEqual(len(video_urls), len(video_url_list))
        for expect, actual in zip(video_urls, video_url_list):
            self.assertEqual(expect, actual)

    def test_create(self):
        """create のテスト"""
        base_url = "https://www.nicovideo.jp/watch/sm1000000{}"
        video_url_strs = self._get_urls()
        video_urls = self._get_video_urls()

        # 正常系
        # 空リスト
        video_url_list = VideoURLList.create([])
        self.assertEqual([], video_url_list._list)

        # 動画URLのリスト
        video_url_list = VideoURLList.create(video_urls)
        self.assertEqual(video_urls, video_url_list._list)

        # 動画URLを表す文字列のリスト
        video_url_list = VideoURLList.create(video_url_strs)
        self.assertEqual(video_urls, video_url_list._list)

        # 異常系
        # リストでない（str）
        with self.assertRaises(TypeError):
            video_url_list = VideoURLList.create(base_url.format(1))

        # リストでない（int）
        with self.assertRaises(TypeError):
            video_url_list = VideoURLList.create(-1)

        # リストだが要素が動画URLでも文字列でもない
        with self.assertRaises(ValueError):
            video_url_list = VideoURLList.create([-1])

        # 文字列のリストだが動画URLを表していない
        # VideoURL のエラーが送出される
        with self.assertRaises(ValueError):
            video_url_list = VideoURLList.create(["不正な文字列"])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
