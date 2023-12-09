"""URL のテスト

URL の各種機能をテストする
"""
import sys
import unittest
import urllib.parse

from NNMM.VideoInfoFetcher.ValueObjects.url import URL


class TestURL(unittest.TestCase):
    def _get_url_set(self) -> list[str]:
        """urlセットを返す
        """
        urls = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return urls

    def test_URLInit(self):
        """URL の初期化後の状態をテストする
        """
        # 正常系
        urls = self._get_url_set()
        for original_url in urls:
            url = URL(original_url)  # 文字列からの生成チェック
            url_in_url = URL(url)  # URLからの生成チェック

            non_query_url = urllib.parse.urlunparse(
                urllib.parse.urlparse(original_url)._replace(query=None)
            )
            expect = non_query_url
            actual = url.non_query_url
            self.assertEqual(expect, actual)

            expect = original_url
            actual = url.original_url
            self.assertEqual(expect, actual)

        # 異常系
        # urlが不正
        with self.assertRaises(ValueError):
            original_url = "不正なURLアドレス"
            url = URL(original_url)

    def test_is_valid(self):
        """is_valid のテスト
        """
        original_url = self._get_url_set()[0]
        actual = URL.is_valid(original_url)
        self.assertEqual(True, actual)

        original_url = "不正なURLアドレス"
        actual = URL.is_valid(original_url)
        self.assertEqual(False, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
