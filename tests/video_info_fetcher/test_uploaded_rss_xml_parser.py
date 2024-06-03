import sys
import unittest
from datetime import datetime

import xmltodict

from nnmm.util import MylistType, find_values
from nnmm.video_info_fetcher.uploaded_rss_xml_parser import UploadedRSSXmlParser
from nnmm.video_info_fetcher.value_objects.myshowname import Myshowname
from nnmm.video_info_fetcher.value_objects.registered_at import RegisteredAt
from nnmm.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from nnmm.video_info_fetcher.value_objects.showname import Showname
from nnmm.video_info_fetcher.value_objects.title import Title
from nnmm.video_info_fetcher.value_objects.title_list import TitleList
from nnmm.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


class TestUploadedRSSXmlParser(unittest.TestCase):
    def _get_url_set(self) -> list[str]:
        """urlセットを返す"""
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
            "https://www.nicovideo.jp/user/11111111/series/00000011",
        ]
        return url_info

    def _get_mylist_info(self, mylist_url: str) -> dict:
        urls = self._get_url_set()
        urls = [URL(url).non_query_url for url in urls]
        cols = ["mylist_url", "mylist_name", "username"]
        d = {
            urls[0]: [urls[0], "投稿者1さんの投稿動画‐ニコニコ動画", "投稿者1"],
            urls[1]: [urls[1], "投稿者2さんの投稿動画‐ニコニコ動画", "投稿者2"],
            urls[2]: [urls[2], "マイリスト テスト用マイリスト1‐ニコニコ動画", "投稿者1"],
            urls[3]: [urls[3], "マイリスト テスト用マイリスト2‐ニコニコ動画", "投稿者1"],
            urls[4]: [urls[4], "マイリスト テスト用マイリスト3‐ニコニコ動画", "投稿者3"],
            urls[5]: [urls[5], "シリーズ テスト用シリーズ1‐ニコニコ動画", "投稿者1"],
        }
        return dict(zip(cols, d[mylist_url]))

    def _get_iteminfo(self, n: int) -> dict:
        d = {
            "title": f"動画タイトル_{n}",
            "video_url": "https://www.nicovideo.jp/watch/" + f"sm1000000{n}",
            "registered_at": f"Mon, 09 May 2022 00:01:0{n} +0900",
            "video_id": f"sm1000000{n}",
        }
        return d

    def _make_xml(self, mylist_url) -> list[dict]:
        """xml を返す

        Notes:
           RSS取得でDLされる擬似的なxmlを返す
        """
        mylist_url = URL(mylist_url).non_query_url
        mylist_info = self._get_mylist_info(mylist_url)
        mylist_name = mylist_info["mylist_name"]
        username = mylist_info["username"]

        NUM = 5
        xml = '<?xml version="1.0" encoding="utf-8"?>'
        xml += """<rss version="2.0"
                       xmlns:dc="http://purl.org/dc/elements/1.1/"
                       xmlns:atom="http://www.w3.org/2005/Atom">
                  <channel>"""
        xml += f"<title>{mylist_name}</title>"
        xml += f"<link>{mylist_url}?ref=rss_mylist_rss2</link>"
        xml += f"<dc:creator>{username}</dc:creator>"

        for i in range(1, NUM + 1):
            d = self._get_iteminfo(i)

            title = d["title"]
            video_url = d["video_url"]
            registered_at = d["registered_at"]

            xml += "<item>"
            xml += f"<title>{title}</title>"
            xml += f"<link>{video_url}?ref=rss_mylist_rss2</link>"
            xml += f"<pubDate>{registered_at}</pubDate>"
            xml += "</item>"

        xml += "</channel></rss>"
        return xml

    def test_init(self):
        urls = self._get_url_set()
        for url in urls:
            xml = self._make_xml(url)
            xml_dict = xmltodict.parse(xml)
            if UploadedURL.is_valid_mylist_url(url):
                instance = UploadedRSSXmlParser(url, xml)
                self.assertEqual(xml_dict, instance.xml_dict)
            else:
                with self.assertRaises(ValueError):
                    instance = UploadedRSSXmlParser(url, xml)

    def test_get_username(self):
        urls = self._get_url_set()
        for url in urls:
            if not UploadedURL.is_valid_mylist_url(url):
                continue
            xml = self._make_xml(url)
            xml_dict = xmltodict.parse(xml)
            instance = UploadedRSSXmlParser(url, xml)

            actual = instance._get_username()
            expect = find_values(xml_dict, "dc:creator", True, [], [])
            self.assertEqual(Username(expect), actual)

    def test_get_showname_myshowname(self):
        urls = self._get_url_set()
        for url in urls:
            if not UploadedURL.is_valid_mylist_url(url):
                continue
            xml = self._make_xml(url)
            xml_dict = xmltodict.parse(xml)
            instance = UploadedRSSXmlParser(url, xml)

            actual = instance._get_showname_myshowname()

            username = instance._get_username()
            myshowname = Myshowname("投稿動画")
            showname = Showname.create(MylistType.uploaded, username, None)
            expect = (showname, myshowname)
            self.assertEqual(expect, actual)

    def test_get_entries(self):
        SOURCE_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
        DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        urls = self._get_url_set()
        for url in urls:
            if not UploadedURL.is_valid_mylist_url(url):
                continue
            xml = self._make_xml(url)
            xml_dict = xmltodict.parse(xml)
            instance = UploadedRSSXmlParser(url, xml)

            actual = instance._get_entries()

            items_dict = find_values(xml_dict, "item", True, [], [])
            video_url_list = [
                VideoURL.create(URL(video_url).non_query_url)
                for video_url in find_values(items_dict, "link", False, [], [])
            ]
            video_id_list = [video_url.video_id for video_url in video_url_list]
            title_list = [Title(title) for title in find_values(items_dict, "title", False, [], [])]
            registered_at_list = [
                RegisteredAt(datetime.strptime(pub_date, SOURCE_DATETIME_FORMAT).strftime(DESTINATION_DATETIME_FORMAT))
                for pub_date in find_values(items_dict, "pubDate", False, [], [])
            ]

            video_id_list = VideoidList.create(video_id_list)
            title_list = TitleList.create(title_list)
            registered_at_list = RegisteredAtList.create(registered_at_list)
            video_url_list = VideoURLList.create(video_url_list)
            expect = (video_id_list, title_list, registered_at_list, video_url_list)
            self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
