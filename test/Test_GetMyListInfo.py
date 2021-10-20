# coding: utf-8
"""GetMyListInfoのテスト

GetMyListInfoの各種機能をテストする
"""

import asyncio
import copy
import re
import shutil
import sys
import unittest
import urllib.parse
from contextlib import ExitStack
from mock import MagicMock, PropertyMock, patch, mock_open, AsyncMock
from pathlib import Path

import pyppeteer
import requests
from bs4 import BeautifulSoup
from requests_html import AsyncHTMLSession
from sqlalchemy.sql import visitors

from NNMM.MylistDBController import *
from NNMM import GetMyListInfo, GuiFunction

RSS_PATH = "./test/rss/"


class TestGetMyListInfo(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if Path(RSS_PATH).exists():
            shutil.rmtree(RSS_PATH)
        pass

    def __GetURLSet(self) -> list[str]:
        """urlセットを返す
        """
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def __GetMylistURLSet(self) -> list[str]:
        """mylist_urlセットを返す
        """
        mylist_url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/mylist/00000011",
            "https://www.nicovideo.jp/mylist/00000012",
            "https://www.nicovideo.jp/mylist/00000031",
        ]
        return mylist_url_info

    def __GetMylistInfoSet(self, mylist_url: str):
        """マイリスト情報セットを返す
        """
        mylist_url_info = self.__GetMylistURLSet()
        mylist_info = {
            mylist_url_info[0]: ("投稿者1さんの投稿動画‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:00 +0900", "投稿者1"),
            mylist_url_info[1]: ("投稿者2さんの投稿動画‐ニコニコ動画", "Wed, 19 Oct 2021 02:00:00 +0900", "投稿者2"),
            mylist_url_info[2]: ("マイリスト 投稿者1のマイリスト1‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:01 +0900", "投稿者1"),
            mylist_url_info[3]: ("マイリスト 投稿者1のマイリスト2‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:02 +0900", "投稿者1"),
            mylist_url_info[4]: ("マイリスト 投稿者3のマイリスト1‐ニコニコ動画", "Wed, 19 Oct 2021 03:00:01 +0900", "投稿者3"),
        }
        res = mylist_info.get(mylist_url)
        return res

    def __GetVideoInfoSet(self, mylist_url: str):
        """動画情報セットを返す
        """
        mylist_url_info = self.__GetMylistURLSet()
        title_t = "動画タイトル{}_{:02}"
        video_url_t = "https://www.nicovideo.jp/watch/sm{}00000{:02}"
        uploaded_t = "Wed, 19 Oct 2021 0{}:00:{:02} +0900"
        video_info = {
            mylist_url_info[0]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(1, 10)],
            mylist_url_info[1]: [(title_t.format(2, i), video_url_t.format(2, i), uploaded_t.format(2, i)) for i in range(1, 10)],
            mylist_url_info[2]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(1, 5)],
            mylist_url_info[3]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(5, 10)],
            mylist_url_info[4]: [(title_t.format(3, i), video_url_t.format(3, i), uploaded_t.format(3, i)) for i in range(1, 10)],
        }
        res = video_info.get(mylist_url)
        return res

    def __GetURLType(self, url: str) -> str:
        # 投稿動画
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
        if re.search(pattern, url):
            return "uploaded"

        # マイリスト
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, url):
            return "mylist"

        return ""

    def __MakeXML(self, mylist_url: str) -> str:
        xml = ""

        # クエリ除去
        mylist_url = urllib.parse.urlunparse(
            urllib.parse.urlparse(mylist_url)._replace(query=None)
        )

        # マイリストのURLならRSSが取得できるURLに加工
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        # マイリスト情報加工
        title, uploaded, username = self.__GetMylistInfoSet(mylist_url)
        xml = f"""
            <?xml version="1.0" encoding="utf-8"?>
            <rss version="2.0"
                    xmlns:dc="http://purl.org/dc/elements/1.1/"
                    xmlns:atom="http://www.w3.org/2005/Atom">
            <channel>
                <title>{title}</title>
                <link>{mylist_url}?ref=rss_mylist_rss2</link>
                <description></description>
                <pubDate>{uploaded}</pubDate>
                <dc:creator>{username}</dc:creator>
        """

        # 動画情報加工
        video_info = self.__GetVideoInfoSet(mylist_url)
        for item in reversed(video_info):
            title, video_url, uploaded = item
            xml = xml + f"""
                <item>
                    <title>{title}</title>
                    <link>{video_url}?ref=rss_mylist_rss2</link>
                    <pubDate>{uploaded}</pubDate>
                    <description><![CDATA[]]></description>
                </item>
            """

        xml = xml + "</channel></rss>"
        return xml

    def __MakeEventLoopMock(self):
        r_response = AsyncMock()

        async def ReturnRunInExecutor(s, executor, func, args):
            r = MagicMock()
            url = args
            type(r).raise_for_status = lambda s: 0
            type(r).text = self.__MakeXML(url)
            return r
        type(r_response).run_in_executor = ReturnRunInExecutor
        return r_response

    def __MakeConfigMock(self):
        return {"general": {"rss_save_path": RSS_PATH}}

    def __MakeLinks(self, url):
        video_urls = []

        # クエリ除去
        url = urllib.parse.urlunparse(
            urllib.parse.urlparse(url)._replace(query=None)
        )

        # マイリストのURLならRSSが取得できるURLに加工
        mylist_url = url
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        # 動画情報加工
        video_info = self.__GetVideoInfoSet(mylist_url)

        # 本来はsetで返すべきだがキャストするのでそのままlistで返す
        video_urls = [v[1] for v in video_info]
        return video_urls.reverse()

    def __MakeTitles(self, url):
        titles = []

        # クエリ除去
        url = urllib.parse.urlunparse(
            urllib.parse.urlparse(url)._replace(query=None)
        )

        # マイリストのURLならRSSが取得できるURLに加工
        mylist_url = url
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        # 動画情報加工
        video_info = self.__GetVideoInfoSet(mylist_url)

        titles = [v[0] for v in video_info]
        return titles.reverse()

    def __MakeUploads(self, url):
        res = []

        # クエリ除去
        url = urllib.parse.urlunparse(
            urllib.parse.urlparse(url)._replace(query=None)
        )

        # マイリストのURLならRSSが取得できるURLに加工
        mylist_url = url
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        # 動画情報加工
        video_info = self.__GetVideoInfoSet(mylist_url)

        res = [v[2] for v in video_info]
        return res.reverse()

    def __MakeSessionMock(self):
        r_response = AsyncMock()

        async def ReturnGet(s, url):
            r_get = MagicMock()

            def ReturnHtml():
                r_html = AsyncMock()

                async def ReturnARender(s):
                    return None
                type(r_html).arender = ReturnARender

                type(r_html).links = self.__MakeLinks(url)

                def ReturnLxml():
                    r_lxml = MagicMock()

                    def ReturnFindClass(s, id):
                        r_finds = []
                        value_list = []

                        if id == "NC-MediaObjectTitle":
                            value_list = self.__MakeTitles(url)
                        elif id == "NC-VideoRegisteredAtText-text":
                            value_list = self.__MakeUploads(url)

                        for v in value_list:
                            r_p = MagicMock()
                            type(r_p).text = v
                            r_finds.append(r_p)
                        return r_finds

                    type(r_lxml).find_class = ReturnFindClass
                    return r_lxml
                type(r_html).lxml = ReturnLxml()

                return r_html

            type(r_get).html = ReturnHtml()
            return r_get

        type(r_response).get = ReturnGet
        return r_response

    async def __MakePyppeteerMock(self, argv):
        return None

    def __MakeExpectResult(self, url):
        expect = []
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]

        # クエリ除去
        url = urllib.parse.urlunparse(
            urllib.parse.urlparse(url)._replace(query=None)
        )

        # url_type判定
        type = self.__GetURLType(url)

        mylist_url = url
        # マイリストのURLならRSSが取得できるURLに加工
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        # マイリスト情報と動画情報を取得
        mylist_info = self.__GetMylistInfoSet(mylist_url)
        video_info = self.__GetVideoInfoSet(mylist_url)

        username = mylist_info[2]

        for i, item in enumerate(reversed(video_info)):
            # マイリスト名収集
            showname = ""
            myshowname = ""
            if type == "uploaded":
                # 投稿動画の場合はマイリスト名がないのでユーザー名と合わせて便宜上の名前に設定
                myshowname = "投稿動画"
                showname = f"{username}さんの投稿動画"
            elif type == "mylist":
                # マイリストの場合はタイトルから取得
                pattern = "^マイリスト (.*)‐ニコニコ動画$"
                myshowname = re.findall(pattern, mylist_info[0])[0]
                showname = f"「{myshowname}」-{username}さんのマイリスト"

            title = item[0]

            video_url = item[1]
            pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+"
            if re.findall(pattern, video_url):
                # クエリ除去してURL部分のみ保持
                video_url = urllib.parse.urlunparse(
                    urllib.parse.urlparse(video_url)._replace(query=None)
                )

            pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
            video_id = re.findall(pattern, item[1])[0]

            td_format = "%a, %d %b %Y %H:%M:%S %z"
            dts_format = "%Y-%m-%d %H:%M:%S"
            uploaded = datetime.strptime(item[2], td_format).strftime(dts_format)

            value_list = [i + 1, video_id, title, username, "",
                          uploaded, video_url, url, showname, myshowname]
            expect.append(dict(zip(table_cols, value_list)))
        return expect

    def test_AsyncGetMyListInfoLightWeight(self):
        """AsyncGetMyListInfoLightWeightのテスト
        """
        with ExitStack() as stack:
            # mockio = stack.enter_context(patch("pathlib.Path.open", mock_open()))
            mockelm = stack.enter_context(patch("asyncio.get_event_loop", self.__MakeEventLoopMock))
            mockcpb = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig", self.__MakeConfigMock))

            urls = self.__GetURLSet()
            for url in urls:
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfo.AsyncGetMyListInfoLightWeight(url))
                expect = self.__MakeExpectResult(url)
                self.assertEqual(expect, actual)
            pass

    def test_AsyncGetMyListInfo(self):
        """AsyncGetMyListInfoのテスト
        """
        with ExitStack() as stack:
            # mockio = stack.enter_context(patch("pathlib.Path.open", mock_open()))
            mockses = stack.enter_context(patch("NNMM.GetMyListInfo.AsyncHTMLSession", self.__MakeSessionMock))
            mockpyp = stack.enter_context(patch("pyppeteer.launch", self.__MakePyppeteerMock))

            urls = self.__GetURLSet()
            for url in urls:
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfo.AsyncGetMyListInfo(url))
                expect = self.__MakeExpectResult(url)
                self.assertEqual(expect, actual)
            pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
