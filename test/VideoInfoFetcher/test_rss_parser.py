import asyncio
import re
import sys
import unittest
from datetime import datetime

import xmltodict

from NNMM.VideoInfoFetcher.rss_parser import RSSParser
from NNMM.VideoInfoFetcher.ValueObjects.fetched_page_video_info import FetchedPageVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.item_info import ItemInfo
from NNMM.VideoInfoFetcher.ValueObjects.mylist_url import MylistURL
from NNMM.VideoInfoFetcher.ValueObjects.myshowname import Myshowname
from NNMM.VideoInfoFetcher.ValueObjects.registered_at import RegisteredAt
from NNMM.VideoInfoFetcher.ValueObjects.registered_at_list import RegisteredAtList
from NNMM.VideoInfoFetcher.ValueObjects.showname import Showname
from NNMM.VideoInfoFetcher.ValueObjects.title import Title
from NNMM.VideoInfoFetcher.ValueObjects.title_list import TitleList
from NNMM.VideoInfoFetcher.ValueObjects.uploaded_url import UploadedURL
from NNMM.VideoInfoFetcher.ValueObjects.url import URL
from NNMM.VideoInfoFetcher.ValueObjects.username import Username
from NNMM.VideoInfoFetcher.ValueObjects.video_url import VideoURL
from NNMM.VideoInfoFetcher.ValueObjects.video_url_list import VideoURLList
from NNMM.VideoInfoFetcher.ValueObjects.videoid_list import VideoidList


class TestRSSParser(unittest.TestCase):
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

    def _make_xml(self, mylist_url, error_target="", error_value="", error_del=False) -> list[dict]:
        """xml を返す

        Notes:
           RSS取得でDLされる擬似的なxmlを返す
        """
        # 日付フォーマット
        SOURCE_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
        DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        mylist_url = URL(mylist_url).non_query_url
        mylist_info = self._get_mylist_info(mylist_url)
        mylist_name = mylist_info["mylist_name"]
        username = mylist_info["username"]

        NUM = 5
        xml = '<?xml version="1.0" encoding="utf-8"?>'
        xml += '''<rss version="2.0"
                       xmlns:dc="http://purl.org/dc/elements/1.1/"
                       xmlns:atom="http://www.w3.org/2005/Atom">
                  <channel>'''
        xml += f"<title>{mylist_name}</title>"
        xml += f"<link>{mylist_url}?ref=rss_mylist_rss2</link>"
        xml += f"<dc:creator>{username}</dc:creator>"

        for i in range(1, NUM + 1):
            d = self._get_iteminfo(i)

            if error_target != "":
                d[error_target] = error_value

            title = d["title"]
            video_url = d["video_url"]
            registered_at = d["registered_at"]

            xml += "<item>"
            if not error_del and error_target != "title":
                xml += f"<title>{title}</title>"
            if not error_del and error_target != "video_url":
                xml += f"<link>{video_url}?ref=rss_mylist_rss2</link>"
            if not error_del and error_target != "registered_at":
                xml += f"<pubDate>{registered_at}</pubDate>"
            xml += "</item>"

        xml += "</channel></rss>"
        return xml

    def iteminfo(self, item_lx) -> ItemInfo:
        RP = RSSParser

        title = Title(item_lx["title"])

        link_lx = item_lx["link"]
        video_url = VideoURL.create(link_lx)

        pubDate_lx = item_lx["pubDate"]
        dst = datetime.strptime(pubDate_lx, RP.SOURCE_DATETIME_FORMAT)
        registered_at = RegisteredAt(dst.strftime(RP.DESTINATION_DATETIME_FORMAT))
        return ItemInfo(title, registered_at, video_url)

    def test_RSSParserInit(self):
        """RSSParser の初期化後の状態をテストする
        """
        urls = self._get_url_set()
        for url in urls:
            xml = self._make_xml(url)
            xml_dict = xmltodict.parse(xml)
            rp = RSSParser(url, xml)

            if UploadedURL.is_valid(url):
                mylist_url = UploadedURL.create(url)
            elif MylistURL.is_valid(url):
                mylist_url = MylistURL.create(url)

            self.assertEqual(mylist_url, rp.mylist_url)
            self.assertEqual(xml_dict, rp.xml_dict)

            # TODO::入力値チェックを入れる

    def test_get_mylist_url(self):
        """_get_mylist_url のテスト
        """
        url = self._get_url_set()[0]
        xml = self._make_xml(url)
        rp = RSSParser(url, xml)
        self.assertEqual(UploadedURL.create(url), rp._get_mylist_url())

        url = self._get_url_set()[2]
        xml = self._make_xml(url)
        rp = RSSParser(url, xml)
        self.assertEqual(MylistURL.create(url), rp._get_mylist_url())

    def test_get_userid_mylistid(self):
        """_get_userid_mylistid のテスト
        """
        urls = self._get_url_set()
        for url in urls:
            if UploadedURL.is_valid(url):
                mylist_url = UploadedURL.create(url)
            elif MylistURL.is_valid(url):
                mylist_url = MylistURL.create(url)
            xml = self._make_xml(url)

            rp = RSSParser(URL(url).non_query_url, xml)

            expect = (mylist_url.userid, mylist_url.mylistid)
            actual = rp._get_userid_mylistid()
            self.assertEqual(expect, actual)

    def test_get_username(self):
        """_get_username のテスト
        """
        # 投稿動画
        url = self._get_url_set()[0]
        xml = self._make_xml(url)
        xml_dict = xmltodict.parse(xml)

        mylist_url = URL(url).non_query_url
        rp = RSSParser(mylist_url, xml)

        title_lx = xml_dict["rss"]["channel"]["title"]
        pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
        expect = Username(re.findall(pattern, title_lx)[0])
        actual = rp._get_username()
        self.assertEqual(expect, actual)

        # マイリスト
        url = self._get_url_set()[2]
        xml = self._make_xml(url)
        xml_dict = xmltodict.parse(xml)

        mylist_url = URL(url).non_query_url
        rp = RSSParser(mylist_url, xml)

        creator_lx = xml_dict["rss"]["channel"]["dc:creator"]
        expect = Username(creator_lx)
        actual = rp._get_username()
        self.assertEqual(expect, actual)

    def test_get_showname_myshowname(self):
        """_get_showname_myshowname のテスト
        """
        # 投稿動画
        url = self._get_url_set()[0]
        xml = self._make_xml(url)
        xml_dict = xmltodict.parse(xml)

        mylist_url = URL(url).non_query_url
        rp = RSSParser(mylist_url, xml)

        username = rp._get_username()
        myshowname = Myshowname("投稿動画")
        showname = Showname.create(username, None)
        expect = (showname, myshowname)
        actual = rp._get_showname_myshowname()
        self.assertEqual(expect, actual)

        # マイリスト
        url = self._get_url_set()[2]
        xml = self._make_xml(url)
        xml_dict = xmltodict.parse(xml)

        mylist_url = URL(url).non_query_url
        rp = RSSParser(mylist_url, xml)

        username = rp._get_username()
        title_lx = xml_dict["rss"]["channel"]["title"]
        pattern = "^マイリスト (.*)‐ニコニコ動画$"
        
        myshowname = Myshowname("投稿動画")

        myshowname = Myshowname(re.findall(pattern, title_lx)[0])
        showname = Showname.create(username, myshowname)
        expect = (showname, myshowname)
        actual = rp._get_showname_myshowname()
        self.assertEqual(expect, actual)

    def test_parse(self):
        """parse のテスト
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        urls = self._get_url_set()
        for url in urls:
            xml = self._make_xml(url)
            xml_dict = xmltodict.parse(xml)

            rp = RSSParser(URL(url).non_query_url, xml)

            if UploadedURL.is_valid(url):
                mylist_url = UploadedURL.create(url)
                userid = mylist_url.userid
                mylistid = mylist_url.mylistid  # 投稿動画の場合、マイリストIDは空文字列

                title_lx = xml_dict["rss"]["channel"]["title"]
                pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
                username = Username(re.findall(pattern, title_lx)[0])

                myshowname = Myshowname("投稿動画")
                showname = Showname.create(username, None)
            elif MylistURL.is_valid(url):
                mylist_url = MylistURL.create(url)
                userid = mylist_url.userid
                mylistid = mylist_url.mylistid

                creator_lx = xml_dict["rss"]["channel"]["dc:creator"]
                username = Username(creator_lx)

                title_lx = xml_dict["rss"]["channel"]["title"]
                pattern = "^マイリスト (.*)‐ニコニコ動画$"
                myshowname = Myshowname(re.findall(pattern, title_lx)[0])
                showname = Showname.create(username, myshowname)

            video_id_list = []
            title_list = []
            registered_at_list = []
            video_url_list = []
            items_lx = xml_dict["rss"]["channel"]["item"]
            for item in items_lx:
                iteminfo = self.iteminfo(item)
                video_id_list.append(iteminfo.video_id)
                title_list.append(iteminfo.title)
                registered_at_list.append(iteminfo.registered_at)
                video_url_list.append(iteminfo.video_url)

            video_id_list = VideoidList.create(video_id_list)
            title_list = TitleList.create(title_list)
            registered_at_list = RegisteredAtList.create(registered_at_list)
            video_url_list = VideoURLList.create(video_url_list)

            num = len(title_list)
            res = {
                "no": list(range(1, num + 1)),               # No. [1, ..., len()-1]
                "userid": userid,                            # ユーザーID 1234567
                "mylistid": mylistid,                        # マイリストID 12345678
                "showname": showname,                        # マイリスト表示名 「投稿者1さんの投稿動画」
                "myshowname": myshowname,                    # マイリスト名 「投稿動画」
                "mylist_url": mylist_url,                    # マイリストURL https://www.nicovideo.jp/user/11111111/video
                "video_id_list": video_id_list,              # 動画IDリスト [sm12345678]
                "title_list": title_list,                    # 動画タイトルリスト [テスト動画]
                "registered_at_list": registered_at_list,    # 登録日時リスト [%Y-%m-%d %H:%M:%S]
                "video_url_list": video_url_list,            # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
            }
            expect = FetchedPageVideoInfo(**res)

            actual = loop.run_until_complete(rp.parse())
            self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
