# coding: utf-8
"""GetMyListInfoFromHtml のテスト

GetMyListInfoFromHtml の各種機能をテストする
"""

import asyncio
import re
import shutil
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from urllib.error import HTTPError
from mock import MagicMock, AsyncMock, patch, call
from pathlib import Path

from requests_html import AsyncHTMLSession, HTML

from NNMM import GuiFunction
from NNMM import GetMyListInfoFromHtml

RSS_PATH = "./test/rss/"


class TestGetMyListInfoFromHtml(unittest.TestCase):

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

        Notes:
            スクレイピングの場合はURLは開ければ良いため区別しない
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
        m_range = {
            mylist_url_info[0]: range(1, 10),
            mylist_url_info[1]: range(1, 10),
            mylist_url_info[2]: range(1, 5),
            mylist_url_info[3]: range(5, 10),
            mylist_url_info[4]: range(1, 10),
        }.get(mylist_url, range(1, 10))

        pattern = r"https://www.nicovideo.jp/user/([0-9]{8})/.*"
        userid = re.findall(pattern, mylist_url)[0]
        n = userid[0]

        res = []
        src_df = "%Y-%m-%dT%H:%M:%S%z"
        dst_df = "%Y-%m-%d %H:%M:%S"
        for i in m_range:
            video_id = f"sm{n}00000{i:02}"
            video_info = self.__GetVideoInfo(video_id)
            uploaded_at = datetime.strptime(video_info["uploaded_at"], src_df).strftime(dst_df)

            rd = datetime.strptime(video_info["uploaded_at"], src_df)
            rd += timedelta(minutes=1)
            registered_at = rd.strftime(dst_df)

            video_info["uploaded_at"] = uploaded_at
            video_info["registered_at"] = registered_at
            res.append(video_info)

        return res

    def __GetVideoInfo(self, video_id: str) -> list[tuple[str, str, str]]:
        """動画情報を返す
        """
        # video_idのパターンはsm{投稿者id}00000{動画識別2桁}
        pattern = r"sm([0-9]{1})00000([0-9]{2})"
        n, m = re.findall(pattern, video_id)[0]
        title = f"動画タイトル{n}_{m}"
        uploaded_at = f"2022-04-29T0{n}:{m}:00+09:00"
        video_url = "https://www.nicovideo.jp/watch/" + video_id
        user_id = n * 8
        username = f"動画投稿者{n}"

        res = {
            "video_id": video_id,         # 動画ID [sm12345678]
            "title": title,               # 動画タイトル [テスト動画]
            "uploaded_at": uploaded_at,   # 投稿日時 [%Y-%m-%d %H:%M:%S]
            "video_url": video_url,       # 動画URL [https://www.nicovideo.jp/watch/sm12345678]
            "user_id": user_id,           # 投稿者id [投稿者1]
            "username": username,         # 投稿者 [投稿者1]
        }
        return res

    def __GetXMLFromAPI(self, video_id: str) -> str:
        """APIから返ってくる動画情報セットxmlを返す
        """
        video_info = self.__GetVideoInfo(video_id)
        title = video_info.get("title")
        first_retrieve = video_info.get("uploaded_at")
        watch_url = video_info.get("video_url")
        user_id = video_info.get("user_id")
        user_nickname = video_info.get("username")

        xml = """<?xml version="1.0" encoding="utf-8"?>
                    <nicovideo_thumb_response status="ok">
                        <thumb>"""
        xml += f"""<video_id>{video_id}</video_id>
                <title>{title}</title>
                <first_retrieve>{first_retrieve}</first_retrieve>
                <watch_url>{watch_url}</watch_url>
                <user_id>{user_id}</user_id>
                <user_nickname>{user_nickname}</user_nickname>"""
        xml += """</thumb>
                    </nicovideo_thumb_response>"""

        return xml

    def __MakeResponseMock(self, request_url, status_code: int = 200, error_target: str = ""):
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

            src_df = "%Y-%m-%d %H:%M:%S"
            dst_df = "%Y/%m/%d %H:%M"
            if name == error_target:
                result = []
            elif name == "NC-MediaObject-main":
                result = [ReturnHref(video_info["video_url"]) for video_info in video_info_list]
            elif name == "NC-MediaObjectTitle":
                result = [ReturnText(video_info["title"]) for video_info in video_info_list]
            elif name == "NC-VideoRegisteredAtText-text":
                result = [ReturnText(datetime.strptime(video_info["uploaded_at"], src_df).strftime(dst_df)) for video_info in video_info_list]
            elif name == "MylistItemAddition-addedAt":
                result = [ReturnText(datetime.strptime(video_info["registered_at"], src_df).strftime(dst_df)) for video_info in video_info_list]
            elif name == "UserDetailsHeader-nickname":
                result = [ReturnText(mylist_info[2])]
            elif name == "MylistHeader-name":
                result = [ReturnText(mylist_info[0].replace("‐ニコニコ動画", ""))]
            return result

        mock.html.lxml.find_class = ReturnFindClass
        return mock

    def __MakeAPIResponseMock(self, request_url, status_code: int = 200, error_target: str = ""):
        mock = MagicMock()

        pattern = "^https://ext.nicovideo.jp/api/getthumbinfo/(sm[0-9]+)$"
        video_id = re.findall(pattern, request_url)[0]
        xml = self.__GetXMLFromAPI(video_id)
        html = HTML(html=xml)

        mock.html = html
        return mock

    def __MakeSessionResponseMock(self, mock, status_code: int = 200, error_target: str = "") -> tuple[AsyncMock, MagicMock]:
        async def ReturnSessionResponse(request_url: str, do_rendering: bool, session: AsyncHTMLSession = None) -> tuple[AsyncMock, MagicMock]:
            ar_session = AsyncMock()
            if error_target == "HTTPError":
                raise HTTPError
            if status_code == 503:
                return (ar_session, None)

            r_response = self.__MakeResponseMock(request_url, status_code, error_target)
            return (ar_session, r_response)

        mock.side_effect = ReturnSessionResponse
        return mock

    def __MakeAPISessionResponseMock(self, mock, status_code: int = 200, error_target: str = "") -> tuple[AsyncMock, MagicMock]:
        async def ReturnSessionResponse(request_url: str, do_rendering: bool, session: AsyncHTMLSession = None) -> tuple[AsyncMock, MagicMock]:
            ar_session = AsyncMock()
            if error_target == "HTTPError":
                raise HTTPError
            if status_code == 503:
                return (ar_session, None)

            r_response = self.__MakeAPIResponseMock(request_url, status_code, error_target)
            return (ar_session, r_response)

        mock.side_effect = ReturnSessionResponse
        return mock

    def __MakeAnalysisHtmlMock(self, mock, url: str = "", kind: str = ""):
        url_type = GuiFunction.GetURLType(url)
        mylist_url = url

        mylist_info = self.__GetMylistInfoSet(mylist_url)
        video_info_list = self.__GetVideoInfoSet(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        registered_at_list = [video_info["registered_at"] for video_info in video_info_list]

        if url_type == "uploaded":
            username = mylist_info[2]
            showname = f"{username}さんの投稿動画"
            myshowname = "投稿動画"
        elif url_type == "mylist":
            username = mylist_info[2]
            myshowname = mylist_info[0].replace("‐ニコニコ動画", "")
            showname = f"「{myshowname}」-{username}さんのマイリスト"

        html_result = {
            "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
            "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        }

        def ReturnHtml(u, lxml):
            if kind == "AttributeError":
                raise AttributeError
            return html_result

        mock.side_effect = ReturnHtml
        return mock

    def __MakeGetUsernameFromApiMock(self, mock, url: str = "", kind: str = ""):
        mylist_url = url

        video_info_list = self.__GetVideoInfoSet(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        video_id_list = [video_info["video_id"] for video_info in video_info_list]
        video_url_list = [video_info["video_url"] for video_info in video_info_list]
        username_list = [video_info["username"] for video_info in video_info_list]

        api_result = {
            "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
            "title_list": title_list,               # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
            "username_list": username_list,         # 投稿者リスト [投稿者1]
        }

        if kind == "TitleError":
            api_result["title_list"] = [t + "_不正なタイトル名" for t in title_list]
        if kind == "VideoUrlError":
            api_result["video_url_list"] = [v + "_不正なタイトル名" for v in video_url_list]
        if kind == "UsernameError":
            api_result["username_list"] = []

        def ReturnApi(v):
            if kind == "HTTPError":
                raise HTTPError
            return api_result

        mock.side_effect = ReturnApi
        return mock

    def __MakeExpectResult(self, url):
        url_type = GuiFunction.GetURLType(url)
        mylist_url = url

        mylist_info = self.__GetMylistInfoSet(mylist_url)
        video_info_list = self.__GetVideoInfoSet(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        registered_at_list = [video_info["registered_at"] for video_info in video_info_list]
        video_id_list = [video_info["video_id"] for video_info in video_info_list]
        video_url_list = [video_info["video_url"] for video_info in video_info_list]
        username_list = [video_info["username"] for video_info in video_info_list]

        if url_type == "uploaded":
            username = mylist_info[2]
            showname = f"{username}さんの投稿動画"
            myshowname = "投稿動画"
        elif url_type == "mylist":
            username = mylist_info[2]
            myshowname = mylist_info[0].replace("‐ニコニコ動画", "")
            showname = f"「{myshowname}」-{username}さんのマイリスト"

        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
        res = []
        for video_id, title, uploaded_at, registered_at, username, video_url in zip(video_id_list, title_list, uploaded_at_list, registered_at_list, username_list, video_url_list):
            # 出力インターフェイスチェック
            value_list = [-1, video_id, title, username, "", uploaded_at, registered_at, video_url, mylist_url, showname, myshowname]
            if len(table_cols) != len(value_list):
                continue

            # 登録
            res.append(dict(zip(table_cols, value_list)))

        # No.を付記する
        for i, _ in enumerate(res):
            res[i]["no"] = i + 1

        return res

    def test_GetMyListInfoFromHtml(self):
        """GetMyListInfoFromHtml のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.warning"))
            mockses = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.GetAsyncSessionResponse"))
            mockhtml = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.AnalysisHtml"))
            mockhapi = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.GetUsernameFromApi"))

            # 正常系
            mockses = self.__MakeSessionResponseMock(mockses, 200)
            urls = self.__GetURLSet()
            for url in urls:
                mockhtml = self.__MakeAnalysisHtmlMock(mockhtml, url)
                mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url)

                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
                expect = self.__MakeExpectResult(url)
                self.assertEqual(expect, actual)

            # 異常系
            # 入力URLが不正
            url = "https://不正なURL/user/11111111/video"
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # session.getが常に失敗
            mockses = self.__MakeSessionResponseMock(mockses, 503)
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # session.getが例外送出
            mockses = self.__MakeSessionResponseMock(mockses, 503, "HTTPError")
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # 動画リンクが1つもないマイリストを指定
            # 正確にはエラーではない(warning)が結果として空リストが返ってくる
            mockses = self.__MakeSessionResponseMock(mockses, 200)
            url = "https://www.nicovideo.jp/user/99999999/mylist/99999999"
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # htmlからの動画情報収集に失敗
            mockhtml = self.__MakeAnalysisHtmlMock(mockhtml, url, "AttributeError")
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url)
            mockses = self.__MakeSessionResponseMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # apiからの動画情報収集に失敗
            mockhtml = self.__MakeAnalysisHtmlMock(mockhtml, url)
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url, "HTTPError")
            mockses = self.__MakeSessionResponseMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # 取得したtitleの情報がhtmlとapiで異なる
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url, "TitleError")
            mockses = self.__MakeSessionResponseMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # 取得したvideo_urlの情報がhtmlとapiで異なる
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url, "VideoUrlError")
            mockses = self.__MakeSessionResponseMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # username_listの大きさが不正
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url, "UsernameError")
            mockses = self.__MakeSessionResponseMock(mockses, 200)
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(url))
            self.assertEqual([], actual)

            # TODO::結合時のエラーを模倣する

    def test_GetAsyncSessionResponse(self):
        """GetAsyncSessionResponse のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.warning"))
            mockas = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.AsyncHTMLSession"))
            mockpp = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.pyppeteer.launch"))
            mocksl = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.asyncio.sleep"))

            # 正常系
            MAX_RETRY_NUM = 5
            session = AsyncMock()
            response = AsyncMock()

            def MakeReturnGet(retry_count=0, html_error=False):
                global count
                count = retry_count

                async def ReturnGet(request_url):
                    global count
                    if count <= 0:
                        if html_error:
                            del response.html.lxml
                        response.raise_for_status = AsyncMock
                        return response
                    else:
                        count = count - 1
                        response.raise_for_status = HTTPError
                        return response

                return ReturnGet

            session.get.side_effect = MakeReturnGet()
            mockas.side_effect = lambda: session

            # do_renderingがTrue, sessionがNone
            url = self.__GetURLSet()[0]
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetAsyncSessionResponse(url, True, None))
            expect = (session, response)
            self.assertEqual(expect, actual)

            # 呼び出し確認
            def assertMockCall(request_url, do_rendering, use_session):
                if use_session is None:
                    mockas.assert_called_once()
                    mockas.reset_mock()

                    mc = session.mock_calls
                    self.assertEqual(1, len(mc))
                    self.assertEqual(call.get(request_url), mc[0])
                    session.reset_mock()
                else:
                    mockas.assert_not_called()
                    mockas.reset_mock()

                    mc = session.mock_calls
                    self.assertEqual(2, len(mc))
                    self.assertEqual(call.__bool__(), mc[0])
                    self.assertEqual(call.get(request_url), mc[1])
                    session.reset_mock()

                mc = response.mock_calls
                if do_rendering:
                    self.assertEqual(1, len(mc))
                    self.assertEqual(call.html.arender(sleep=2), mc[0])
                else:
                    self.assertEqual(0, len(mc))

                self.assertIsNotNone(response.html.lxml)
                response.reset_mock()

            assertMockCall(url, True, None)

            # do_renderingがFalse, sessionがNone
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetAsyncSessionResponse(url, False, None))
            expect = (session, response)
            self.assertEqual(expect, actual)
            assertMockCall(url, False, None)

            # do_renderingがTrue, sessionがNoneでない
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetAsyncSessionResponse(url, True, session))
            expect = (session, response)
            self.assertEqual(expect, actual)
            assertMockCall(url, True, session)

            # do_renderingがFalse, sessionがNoneでない
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetAsyncSessionResponse(url, False, session))
            expect = (session, response)
            self.assertEqual(expect, actual)
            assertMockCall(url, False, session)

            # リトライして成功するパターン
            session.get.side_effect = MakeReturnGet(MAX_RETRY_NUM - 1, False)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetAsyncSessionResponse(url, True, None))
            expect = (session, response)
            self.assertEqual(expect, actual)

            # 異常系
            # MAX_RETRY_NUM回リトライしたが失敗したパターン
            session.get.side_effect = MakeReturnGet(MAX_RETRY_NUM, False)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetAsyncSessionResponse(url, True, None))
            expect = (session, None)
            self.assertEqual(expect, actual)

            # responseの取得に成功したがresponse.html.lxmlが存在しないパターン
            session.get.side_effect = MakeReturnGet(0, True)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetAsyncSessionResponse(url, True, None))
            expect = (session, None)
            self.assertEqual(expect, actual)

    def test_AnalysisHtml(self):
        """AnalysisHtml のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.warning"))
            mockaup = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.AnalysisUploadedPage"))
            mockamp = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.AnalysisMylistPage"))

            mockaup.return_value = "AnalysisUploadedPage result"
            mockamp.return_value = "AnalysisMylistPage result"

            # 正常系
            # 投稿動画ページ
            url_type = "uploaded"
            video_id_list = []
            lxml = None
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisHtml(url_type, lxml))
            expect = "AnalysisUploadedPage result"
            self.assertEqual(expect, actual)
            mockaup.assert_called_once_with(lxml)
            mockaup.reset_mock()
            mockamp.assert_not_called()
            mockamp.reset_mock()

            # マイリストページ
            url_type = "mylist"
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisHtml(url_type, lxml))
            expect = "AnalysisMylistPage result"
            self.assertEqual(expect, actual)
            mockaup.assert_not_called()
            mockaup.reset_mock()
            mockamp.assert_called_once_with(lxml)
            mockamp.reset_mock()

            # 異常系
            # 不正なurlタイプ
            with self.assertRaises(ValueError):
                url_type = "invalid url type"
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisHtml(url_type, lxml))

    def test_AnalysisUploadedPage(self):
        """AnalysisUploadedPage のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.warning"))

            # 探索対象のクラスタグ定数
            TCT_TITLE = "NC-MediaObjectTitle"
            TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
            TCT_USERNAME = "UserDetailsHeader-nickname"

            # 正常系
            expect = {}
            mylist_url = self.__GetURLSet()[0]
            mylist_info = self.__GetMylistInfoSet(mylist_url)
            video_info_list = self.__GetVideoInfoSet(mylist_url)
            title_list = [video_info["title"] for video_info in video_info_list]
            uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
            registered_at_list = uploaded_at_list

            username = mylist_info[2]
            showname = f"{username}さんの投稿動画"
            myshowname = "投稿動画"

            expect = {
                "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
                "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
                "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
            }

            response = self.__MakeResponseMock(mylist_url)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisUploadedPage(response.html.lxml))
            self.assertEqual(expect, actual)

            # 異常系
            # 動画名収集失敗
            with self.assertRaises(AttributeError):
                response = self.__MakeResponseMock(mylist_url, 200, TCT_TITLE)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisUploadedPage(response.html.lxml))

            # 投稿日時収集失敗
            with self.assertRaises(AttributeError):
                response = self.__MakeResponseMock(mylist_url, 200, TCT_UPLOADED)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisUploadedPage(response.html.lxml))

            # TODO::投稿日時収集は成功するが解釈に失敗

            # 投稿者収集失敗
            with self.assertRaises(AttributeError):
                response = self.__MakeResponseMock(mylist_url, 200, TCT_USERNAME)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisUploadedPage(response.html.lxml))

    def test_AnalysisMylistPage(self):
        """AnalysisMylistPage のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.warning"))

            # 探索対象のクラスタグ定数
            TCT_TITLE = "NC-MediaObjectTitle"
            TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
            TCT_REGISTERED = "MylistItemAddition-addedAt"
            TCT_USERNAME = "UserDetailsHeader-nickname"
            TCT_MYSHOWNAME = "MylistHeader-name"

            # 正常系
            expect = {}
            mylist_url = self.__GetURLSet()[0]
            mylist_info = self.__GetMylistInfoSet(mylist_url)
            video_info_list = self.__GetVideoInfoSet(mylist_url)
            title_list = [video_info["title"] for video_info in video_info_list]
            uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
            registered_at_list = [video_info["registered_at"] for video_info in video_info_list]

            username = mylist_info[2]
            myshowname = mylist_info[0].replace("‐ニコニコ動画", "")
            showname = f"「{myshowname}」-{username}さんのマイリスト"

            expect = {
                "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
                "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
                "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
            }

            response = self.__MakeResponseMock(mylist_url)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisMylistPage(response.html.lxml))
            self.assertEqual(expect, actual)

            # 異常系
            # 動画名収集失敗
            with self.assertRaises(AttributeError):
                response = self.__MakeResponseMock(mylist_url, 200, TCT_TITLE)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisMylistPage(response.html.lxml))

            # 投稿日時収集失敗
            with self.assertRaises(AttributeError):
                response = self.__MakeResponseMock(mylist_url, 200, TCT_UPLOADED)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisMylistPage(response.html.lxml))

            # TODO::投稿日時収集は成功するが解釈に失敗

            # 登録日時収集失敗
            with self.assertRaises(AttributeError):
                response = self.__MakeResponseMock(mylist_url, 200, TCT_REGISTERED)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisMylistPage(response.html.lxml))

            # TODO::登録日時収集は成功するが解釈に失敗

            # 投稿者収集失敗
            with self.assertRaises(AttributeError):
                response = self.__MakeResponseMock(mylist_url, 200, TCT_USERNAME)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisMylistPage(response.html.lxml))

            # マイリスト名収集失敗
            with self.assertRaises(AttributeError):
                response = self.__MakeResponseMock(mylist_url, 200, TCT_MYSHOWNAME)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromHtml.AnalysisMylistPage(response.html.lxml))

    def test_GetUsernameFromApi(self):
        """GetUsernameFromApi のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.logger.warning"))
            mockapises = stack.enter_context(patch("NNMM.GetMyListInfoFromHtml.GetAsyncSessionResponse"))

            # 正常系
            mockapises = self.__MakeAPISessionResponseMock(mockapises, 200)

            expect = {}
            mylist_url = self.__GetURLSet()[0]
            video_info_list = self.__GetVideoInfoSet(mylist_url)
            video_id_list = [video_info["video_id"] for video_info in video_info_list]
            title_list = [video_info["title"] for video_info in video_info_list]
            uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
            video_url_list = [video_info["video_url"] for video_info in video_info_list]
            username_list = [video_info["username"] for video_info in video_info_list]

            expect = {
                "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
                "title_list": title_list,               # 動画タイトルリスト [テスト動画]
                "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                "username_list": username_list,         # 投稿者リスト [投稿者1]
            }

            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromHtml.GetUsernameFromApi(video_id_list))
            self.assertEqual(expect, actual)

            # 異常系
            # GetAsyncSessionResponse に失敗
            mockapises = self.__MakeAPISessionResponseMock(mockapises, 503)

            loop = asyncio.new_event_loop()
            with self.assertRaises(ValueError):
                actual = loop.run_until_complete(GetMyListInfoFromHtml.GetUsernameFromApi(video_id_list))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
