# coding: utf-8
"""URL のテスト

URL の各種機能をテストする
"""
import re
import sys
import unittest
import urllib.parse

from NNMM.VideoInfoFetcher.URL import URL, URLType


class TestURL(unittest.TestCase):
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

    def test_URLInit(self):
        """URL の初期化後の状態をテストする
        """
        # 正常系
        def get_type(url) -> URLType:
            if re.search(URL.UPLOADED_URL_PATTERN, url):
                return URLType.UPLOADED
            if re.search(URL.MYLIST_URL_PATTERN, url):
                return URLType.MYLIST
            return ""

        urls = self._get_url_set()
        for original_url in urls:
            url = URL(original_url)

            exclude_query_url = urllib.parse.urlunparse(
                urllib.parse.urlparse(original_url)._replace(query=None)
            )
            expect = exclude_query_url
            actual = url.url
            self.assertEqual(expect, actual)

            expect = get_type(exclude_query_url)
            actual = url.type
            self.assertEqual(expect, actual)

        # 異常系
        # urlが不正
        with self.assertRaises(ValueError):
            original_url = "https://不正なURLアドレス/user/11111111/video"
            url = URL(original_url)

    def test_is_valid(self):
        """_is_valid のテスト
        """
        urls = self._get_url_set()
        original_url = urls[0]
        url = URL(original_url)
        actual = url._is_valid()
        self.assertEqual(True, actual)

        original_url = urls[2]
        url = URL(original_url)
        actual = url._is_valid()
        self.assertEqual(True, actual)

        original_url = "https://不正なURLアドレス/user/11111111/video"
        url.url = original_url  # 不正な代入
        actual = url._is_valid()
        self.assertEqual(False, actual)

    def test_get_type(self):
        """_get_type のテスト
        """
        urls = self._get_url_set()
        original_url = urls[0]
        url = URL(original_url)
        expect = URLType.UPLOADED
        actual = url._get_type()
        self.assertEqual(expect, actual)

        original_url = urls[2]
        url = URL(original_url)
        expect = URLType.MYLIST
        actual = url._get_type()
        self.assertEqual(expect, actual)

        with self.assertRaises(ValueError):
            original_url = "https://不正なURLアドレス/user/11111111/video"
            url.url = original_url  # 不正な代入
            actual = url._get_type()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
