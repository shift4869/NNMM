# coding: utf-8
"""AsyncGetMyListInfoのテスト

AsyncGetMyListInfoの各種機能をテストする
"""

import asyncio
import shutil
import sys
import unittest
import urllib.parse
import warnings
from contextlib import ExitStack
from re import findall
from mock import MagicMock, patch, AsyncMock
from pathlib import Path

import pyppeteer
from requests_html import AsyncHTMLSession, HTMLResponse, HtmlElement

from NNMM.MylistDBController import *
from NNMM import AsyncGetMyListInfo

RSS_PATH = "./test/rss/"


class TestAsyncGetMyListInfo(unittest.TestCase):

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

    def __GetMylistInfoSet(self, mylist_url: str) -> tuple[str, str, str]:
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
        res = mylist_info.get(mylist_url, ("", "", ""))
        return res

    def __GetVideoInfoSet(self, mylist_url: str) -> list[tuple[str, str, str]]:
        """動画情報セットを返す
        """
        mylist_url_info = self.__GetMylistURLSet()
        title_t = "動画タイトル{}_{:02}"
        video_url_t = "https://www.nicovideo.jp/watch/sm{}00000{:02}"
        uploaded_t = "Wed, 19 Oct 2021 0{}:{:02}:00 +0900"
        video_info = {
            mylist_url_info[0]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(1, 10)],
            mylist_url_info[1]: [(title_t.format(2, i), video_url_t.format(2, i), uploaded_t.format(2, i)) for i in range(1, 10)],
            mylist_url_info[2]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(1, 5)],
            mylist_url_info[3]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(5, 10)],
            mylist_url_info[4]: [(title_t.format(3, i), video_url_t.format(3, i), uploaded_t.format(3, i)) for i in range(1, 10)],
        }
        res = video_info.get(mylist_url, [("", "", "")])
        return res

    def __MakeResponceMock(self, mylist_url, status_code):
        mock = MagicMock()

        def ReturnFind(val):
            r_find = MagicMock()
            r_attrib = MagicMock()
            r_attrib.attrib = {"href": val}
            r_find.find = lambda key: r_attrib if key == "a" else None
            return r_find

        def ReturnFindClass(name):
            result = []
            video_info_list = self.__GetVideoInfoSet(mylist_url)
            if name == "NC-MediaObject-main":
                result = [ReturnFind(video_info[1]) for video_info in video_info_list]
            return result

        mock.html.lxml.find_class = ReturnFindClass
        return mock

    def __MakeSessionResponceMock(self, mock, status_code) -> tuple[AsyncMock, MagicMock]:
        async def ReturnSessionResponce(request_url: str, do_rendering: bool, session: AsyncHTMLSession = None) -> tuple[AsyncMock, MagicMock]:
            ar_session = AsyncMock()
            r_responce = self.__MakeResponceMock(request_url, status_code)
            return (ar_session, r_responce)

        mock.side_effect = ReturnSessionResponce
        return mock

    def test_AsyncGetMyListInfo(self):
        """AsyncGetMyListInfoのテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.warning"))
            mockses = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.GetAsyncSessionResponce"))

            # 正常系
            mockses = self.__MakeSessionResponceMock(mockses, 200)
            urls = self.__GetURLSet()
            for url in urls:
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
                expect = self.__MakeExpectResult(url)
                self.assertEqual(expect, actual)
            return
            # 異常系
            # 入力URLが不正
            url = "https://不正なURL/user/11111111/video"
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)
 
            # session.getが常に失敗
            with patch("NNMM.AsyncGetMyListInfo.AsyncHTMLSession", lambda: self.__MakeSessionMock(503)):
                url = urls[0]
                actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
                self.assertEqual([], actual)

            # 動画リンクが1つもないマイリストを指定
            # 正確にはエラーではない(warning)が結果として空リストが返ってくる
            with patch("NNMM.GuiFunction.GetURLType", lambda x: "mylist"):
                url = "https://www.nicovideo.jp/user/99999999/mylist/99999999"
                actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
                self.assertEqual([], actual)

            # 動画名収集に失敗(AttributeError)
            url = urls[0]
            error_target = "NC-MediaObjectTitle"
            with patch("NNMM.AsyncGetMyListInfo.AsyncHTMLSession", lambda: self.__MakeSessionMock(200, error_target)):
                actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
                self.assertEqual([], actual)

            # 投稿日時収集に失敗(AttributeError)
            error_target = "NC-VideoRegisteredAtText-text"
            with patch("NNMM.AsyncGetMyListInfo.AsyncHTMLSession", lambda: self.__MakeSessionMock(200, error_target)):
                actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
                self.assertEqual([], actual)

            # 投稿日時収集に失敗(ValueError)
            error_target = "NC-VideoRegisteredAtText-text__ValueError"
            with patch("NNMM.AsyncGetMyListInfo.AsyncHTMLSession", lambda: self.__MakeSessionMock(200, error_target)):
                actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
                self.assertEqual([], actual)

            # 投稿者収集に失敗(AttributeError)
            error_target = "UserDetailsHeader-nickname"
            with patch("NNMM.AsyncGetMyListInfo.AsyncHTMLSession", lambda: self.__MakeSessionMock(200, error_target)):
                actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
                self.assertEqual([], actual)

            # マイリスト名収集に失敗(AttributeError)
            url = urls[2]
            error_target = "MylistHeader-name"
            with patch("NNMM.AsyncGetMyListInfo.AsyncHTMLSession", lambda: self.__MakeSessionMock(200, error_target)):
                actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
                self.assertEqual([], actual)
            pass

    def test_GetAsyncSessionResponce(self):
        """GetAsyncSessionResponceのテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.warning"))

            # 正常系
            # 異常系
            pass

    def test_AnalysisUploadedPage(self):
        """AnalysisUploadedPageのテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.warning"))

            # 正常系
            # 異常系
            pass

    def test_AnalysisMylistPage(self):
        """AnalysisMylistPageのテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.warning"))

            # 正常系
            # 異常系
            pass

    def test_GetUsernameFromApi(self):
        """GetUsernameFromApiのテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.warning"))

            # 正常系
            # 異常系
            pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
