# coding: utf-8
"""AsyncGetMyListInfoのテスト

AsyncGetMyListInfoの各種機能をテストする
"""

import asyncio
import re
import shutil
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime
from urllib.error import HTTPError
from mock import MagicMock, AsyncMock, patch, call
from pathlib import Path

import pyppeteer
from requests_html import AsyncHTMLSession, HTMLResponse, HtmlElement

from NNMM import GuiFunction
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
            # スクレイピングの場合はURLは開ければ良いため区別しない
            mylist_url_info = [
                "https://www.nicovideo.jp/user/11111111/video",
                "https://www.nicovideo.jp/user/22222222/video",
                "https://www.nicovideo.jp/mylist/00000011",
                "https://www.nicovideo.jp/mylist/00000012",
                "https://www.nicovideo.jp/mylist/00000031",
            ]
        """
        return self.__GetURLSet()

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
        uploaded_t = "2022/03/13 0{}:{:02}"
        video_info = {
            mylist_url_info[0]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(1, 10)],
            mylist_url_info[1]: [(title_t.format(2, i), video_url_t.format(2, i), uploaded_t.format(2, i)) for i in range(1, 10)],
            mylist_url_info[2]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(1, 5)],
            mylist_url_info[3]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(5, 10)],
            mylist_url_info[4]: [(title_t.format(3, i), video_url_t.format(3, i), uploaded_t.format(3, i)) for i in range(1, 10)],
        }
        res = video_info.get(mylist_url, [("", "", "")])
        return res

    def __MakeResponceMock(self, request_url, status_code: int = 200, error_target: str = ""):
        mock = MagicMock()

        def ReturnHref(val):
            r_href = MagicMock()
            r_attrib = MagicMock()
            r_attrib.attrib = {"href": val}
            r_href.find = lambda key: r_attrib if key == "a" else None
            return r_href

        def ReturnText(val):
            r_text = MagicMock()
            r_text.text = val
            return r_text

        def ReturnFindClass(name):
            result = []
            mylist_url = request_url
            mylist_info = self.__GetMylistInfoSet(mylist_url)
            video_info_list = self.__GetVideoInfoSet(mylist_url)
            if name == error_target:
                result = []
            elif name == "NC-MediaObject-main":
                result = [ReturnHref(video_info[1]) for video_info in video_info_list]
            elif name == "NC-MediaObjectTitle":
                result = [ReturnText(video_info[0]) for video_info in video_info_list]
            elif name == "NC-VideoRegisteredAtText-text":
                result = [ReturnText(video_info[2]) for video_info in video_info_list]
            elif name == "UserDetailsHeader-nickname":
                result = [ReturnText(mylist_info[2])]
            elif name == "MylistHeader-name":
                result = [ReturnText(mylist_info[0].replace("‐ニコニコ動画", ""))]
            return result

        def ReturnFindAll(name):
            if name == "thumb/user_nickname":
                # request_url = "https://ext.nicovideo.jp/api/getthumbinfo/sm10000001"
                pattern = "^https://ext.nicovideo.jp/api/getthumbinfo/(sm[0-9]+)$"
                video_id = re.findall(pattern, request_url)[0]

                urls = self.__GetURLSet()
                for mylist_url in urls:
                    mylist_info = self.__GetMylistInfoSet(mylist_url)
                    video_info_list = self.__GetVideoInfoSet(mylist_url)
                    for video_info in video_info_list:
                        if video_id in video_info[1]:
                            return [ReturnText(mylist_info[2])]
            return []

        mock.html.lxml.find_class = ReturnFindClass
        mock.html.lxml.findall = ReturnFindAll
        return mock

    def __MakeSessionResponceMock(self, mock, status_code: int = 200, error_target: str = "") -> tuple[AsyncMock, MagicMock]:
        async def ReturnSessionResponce(request_url: str, do_rendering: bool, session: AsyncHTMLSession = None) -> tuple[AsyncMock, MagicMock]:
            ar_session = AsyncMock()
            if error_target == "HTTPError":
                raise HTTPError
            if status_code == 503:
                return (ar_session, None)

            r_response = self.__MakeResponceMock(request_url, status_code, error_target)
            return (ar_session, r_response)

        mock.side_effect = ReturnSessionResponce
        return mock

    def __MakeAnalysisHtmlMock(self, mock, kind: str = ""):
        if kind == "HTTPError":
            async def ReturnAnalysisHtml(url_type: str, video_id_list: list[str], lxml: HtmlElement):
                raise HTTPError
            mock.side_effect = ReturnAnalysisHtml
        elif kind == "ReturnNone":
            async def ReturnAnalysisHtml(url_type: str, video_id_list: list[str], lxml: HtmlElement):
                return (None, None, None, "", "")
            mock.side_effect = ReturnAnalysisHtml
        elif kind == "ReturnDifferentLength":
            async def ReturnAnalysisHtml(url_type: str, video_id_list: list[str], lxml: HtmlElement):
                return (["title"], ["uploaded_at"], ["username"], "showname", "myshowname")
            mock.side_effect = ReturnAnalysisHtml
        elif kind == "ReturnTypeError":
            async def ReturnAnalysisHtml(url_type: str, video_id_list: list[str], lxml: HtmlElement):
                return (-1, -1, -1, "showname", "myshowname")
            mock.side_effect = ReturnAnalysisHtml
        else:
            mock.side_effect = AsyncMock
        return mock

    def __MakeExpectResult(self, mylist_url):
        res = []
        url_type = GuiFunction.GetURLType(mylist_url)
        mylist_info = self.__GetMylistInfoSet(mylist_url)
        video_info_list = self.__GetVideoInfoSet(mylist_url)

        pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
        video_list = [s[1] for s in video_info_list]
        video_id_list = [re.findall(pattern, s)[0] for s in video_list]

        td_format = "%Y/%m/%d %H:%M"
        dts_format = "%Y-%m-%d %H:%M:00"

        num = len(video_info_list)
        for i in range(num):
            video_info = video_info_list[i]
            video_id = video_id_list[i]

            dst = datetime.strptime(video_info[2], td_format)
            username = mylist_info[2]

            if url_type == "uploaded":
                myshowname = "投稿動画"
                showname = f"{username}さんの投稿動画"
            elif url_type == "mylist":
                myshowname = mylist_info[0].replace("‐ニコニコ動画", "")
                showname = f"「{myshowname}」-{username}さんのマイリスト"

            a = {
                "no": i + 1,
                "video_id": video_id,
                "title": video_info[0],
                "username": username,
                "status": "",
                "uploaded": dst.strftime(dts_format),
                "video_url": video_info[1],
                "mylist_url": mylist_url,
                "showname": showname,
                "mylistname": myshowname
            }
            res.append(a)
        return res

    def test_AsyncGetMyListInfo(self):
        """AsyncGetMyListInfo のテスト
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

            # 異常系
            # 入力URLが不正
            url = "https://不正なURL/user/11111111/video"
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)

            # session.getが常に失敗
            mockses = self.__MakeSessionResponceMock(mockses, 503)
            url = urls[0]
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)

            # session.getが例外送出
            mockses = self.__MakeSessionResponceMock(mockses, 503, "HTTPError")
            url = urls[0]
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)

            # 動画リンクが1つもないマイリストを指定
            # 正確にはエラーではない(warning)が結果として空リストが返ってくる
            mockses = self.__MakeSessionResponceMock(mockses, 200)
            url = "https://www.nicovideo.jp/user/99999999/mylist/99999999"
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)

            # 動画情報収集に失敗
            mockah = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.AnalysisHtml"))
            mockah = self.__MakeAnalysisHtmlMock(mockah, "HTTPError")
            mockses = self.__MakeSessionResponceMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)

            # 取得した動画情報がNone
            mockah = self.__MakeAnalysisHtmlMock(mockah, "ReturnNone")
            mockses = self.__MakeSessionResponceMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)

            # 取得した動画情報の長さが不正
            mockah = self.__MakeAnalysisHtmlMock(mockah, "ReturnDifferentLength")
            mockses = self.__MakeSessionResponceMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)

            # 取得した動画情報の内容が不正
            mockah = self.__MakeAnalysisHtmlMock(mockah, "ReturnTypeError")
            mockses = self.__MakeSessionResponceMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(AsyncGetMyListInfo.AsyncGetMyListInfo(url))
            self.assertEqual([], actual)

    def test_GetAsyncSessionResponce(self):
        """GetAsyncSessionResponce のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.warning"))
            mockas = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.AsyncHTMLSession"))
            mockpp = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.pyppeteer.launch"))
            mocksl = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.asyncio.sleep"))

            # 正常系
            session = AsyncMock()
            response = AsyncMock()

            async def ReturnGet(request_url):
                return response

            session.get.side_effect = ReturnGet
            mockas.side_effect = lambda: session

            url = self.__GetURLSet()[0]
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(AsyncGetMyListInfo.GetAsyncSessionResponce(url, True, None))
            expect = (session, response)
            self.assertEqual(expect, actual)

            # 呼び出し確認
            def assertMockCall(request_url, do_rendering):
                mc = session.mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual(call.get(request_url), mc[0])
                session.reset_mock()

                mc = response.mock_calls
                if do_rendering:
                    self.assertEqual(2, len(mc))
                    self.assertEqual(call.html.arender(sleep=2), mc[0])
                    self.assertEqual(call.raise_for_status(), mc[1])
                else:
                    self.assertEqual(1, len(mc))
                    self.assertEqual(call.raise_for_status(), mc[0])

                self.assertIsNotNone(response.html.lxml)
                response.reset_mock()

            assertMockCall(url, True)

            # 異常系
            pass

    def test_AnalysisUploadedPage(self):
        """AnalysisUploadedPage のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.warning"))

            # 正常系
            # 異常系
            pass

    def test_AnalysisMylistPage(self):
        """AnalysisMylistPage のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.AsyncGetMyListInfo.logger.warning"))

            # 正常系
            # 異常系
            pass

    def test_GetUsernameFromApi(self):
        """GetUsernameFromApi のテスト
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
