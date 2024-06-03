import sys
import unittest

from mock import call, patch

from nnmm.video_info_fetcher.value_objects.mylist_url import MylistURL
from nnmm.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory
from nnmm.video_info_fetcher.value_objects.series_url import SeriesURL
from nnmm.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL


class TestMylistURLFactory(unittest.TestCase):
    def test_init(self):
        class_list = MylistURLFactory._class_list
        self.assertEqual([UploadedURL, UserMylistURL, SeriesURL], class_list)

        with self.assertRaises(ValueError):
            instance = MylistURLFactory()

    def test_create(self):
        urls = [
            "https://www.nicovideo.jp/user/37896001/video",
            "https://www.nicovideo.jp/user/6063658/mylist/72036443",
            "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/12899156/series/442402",
        ]

        def expect_mylist_url(url):
            class_list: list[MylistURL] = [UploadedURL, UserMylistURL, SeriesURL]
            for c in class_list:
                if c.is_valid_mylist_url(url):
                    return c.create(url)
            return None

        for url in urls:
            actual = MylistURLFactory.create(url)
            expect = expect_mylist_url(url)
            self.assertEqual(expect, actual)

        for url in urls:
            actual = MylistURLFactory.create(URL(url))
            expect = expect_mylist_url(url)
            self.assertEqual(expect, actual)

        url = "https://不正なURLアドレス/user/6063658/mylist/72036443"
        with self.assertRaises(ValueError):
            expect = expect_mylist_url(url)
            actual = MylistURLFactory.create(url)

        class DummyClass:
            pass

        MylistURLFactory._class_list.insert(0, DummyClass)
        for url in urls:
            actual = MylistURLFactory.create(url)
            expect = expect_mylist_url(url)
            self.assertEqual(expect, actual)
        MylistURLFactory._class_list.remove(DummyClass)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
