# coding: utf-8
"""FetchURL のテスト

FetchURL の各種機能をテストする
"""
import re
import sys
import unittest

from NNMM.VideoInfoFetcher.URL import URL, URLType
from NNMM.VideoInfoFetcher.FetchURL import FetchURL


class TestFetchURL(unittest.TestCase):
    def _get_url_set(self) -> list[str]:
        """urlセットを返す
        """
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def test_FetchURLInit(self):
        """FetchURL の初期化後の状態をテストする
        """
        urls = self._get_url_set()
        for original_url in urls:
            fetch_url = FetchURL(original_url)
            url = URL(original_url)

            if url.type == URLType.MYLIST:
                request_url = re.sub("/user/[0-9]+", "", str(original_url))
            else:
                request_url = original_url

            self.assertEqual(original_url, fetch_url.original_url)
            self.assertEqual(url, fetch_url.url)
            self.assertEqual(url.type, fetch_url.type)
            self.assertEqual(request_url, fetch_url.request_url)

    def test_get_request_url(self):
        """_get_request_url のテスト
        """
        urls = self._get_url_set()
        for original_url in urls:
            fetch_url = FetchURL(original_url)
            url = URL(original_url)

            if url.type == URLType.MYLIST:
                request_url = re.sub("/user/[0-9]+", "", str(original_url))
            else:
                request_url = original_url

            expect = request_url
            actual = fetch_url._get_request_url()
            self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
