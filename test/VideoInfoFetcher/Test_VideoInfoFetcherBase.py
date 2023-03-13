# coding: utf-8
"""VideoInfoFetcherBase のテスト

VideoInfoFetcherBase の各種機能をテストする
"""

import asyncio
import re
import shutil
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError

from mock import AsyncMock, MagicMock, call, patch
from requests_html import HTML, AsyncHTMLSession

from NNMM.VideoInfoFetcher.ValueObjects.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.ValueObjects.RegisteredAt import RegisteredAt
from NNMM.VideoInfoFetcher.ValueObjects.Title import Title
from NNMM.VideoInfoFetcher.ValueObjects.TitleList import TitleList
from NNMM.VideoInfoFetcher.ValueObjects.UploadedAt import UploadedAt
from NNMM.VideoInfoFetcher.ValueObjects.UploadedAtList import UploadedAtList
from NNMM.VideoInfoFetcher.ValueObjects.UploadedURL import UploadedURL
from NNMM.VideoInfoFetcher.ValueObjects.Userid import Userid
from NNMM.VideoInfoFetcher.ValueObjects.Username import Username
from NNMM.VideoInfoFetcher.ValueObjects.UsernameList import UsernameList
from NNMM.VideoInfoFetcher.ValueObjects.Videoid import Videoid
from NNMM.VideoInfoFetcher.ValueObjects.VideoidList import VideoidList
from NNMM.VideoInfoFetcher.ValueObjects.VideoURL import VideoURL
from NNMM.VideoInfoFetcher.ValueObjects.VideoURLList import VideoURLList
from NNMM.VideoInfoFetcher.VideoInfoFetcherBase import SourceType, VideoInfoFetcherBase

RSS_PATH = "./test/rss/"


# テスト用具体化ProcessBase
class ConcreteVideoInfoFetcher(VideoInfoFetcherBase):
    
    def __init__(self, url: str, source_type: SourceType = SourceType.HTML) -> None:
        super().__init__(url, source_type)

    async def _fetch_videoinfo(self) -> list[dict]:
        return ["test_fetch_videoinfo"]


class TestVideoInfoFetcherBase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if Path(RSS_PATH).exists():
            shutil.rmtree(RSS_PATH)
        pass

    def _get_url_set(self) -> list[str]:
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

    def _get_mylist_url_set(self) -> list[str]:
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
        return self._get_url_set()

    def _get_videoinfo_set(self, mylist_url: str) -> list[tuple[str, str, str]]:
        """動画情報セットを返す
        """
        mylist_url_info = self._get_mylist_url_set()
        m_range = {
            mylist_url_info[0]: range(1, 10),
            mylist_url_info[1]: range(1, 10),
            mylist_url_info[2]: range(1, 5),
            mylist_url_info[3]: range(5, 10),
            mylist_url_info[4]: range(1, 10),
        }.get(mylist_url, range(1, 10))

        pattern = r"https://www.nicovideo.jp/user/([0-9]{8})/.*"
        userid = Userid(re.findall(pattern, mylist_url)[0])
        n = userid.id[0]

        res = []
        src_df = "%Y-%m-%dT%H:%M:%S%z"
        dst_df = "%Y-%m-%d %H:%M:%S"
        for i in m_range:
            video_id = Videoid(f"sm{n}00000{i:02}")
            video_info = self._get_videoinfo(video_id.id)
            uploaded_at = video_info["uploaded_at"]

            rd = datetime.strptime(uploaded_at.dt_str, dst_df)
            rd += timedelta(minutes=1)
            registered_at = RegisteredAt(rd.strftime(dst_df))

            video_info["uploaded_at"] = uploaded_at
            video_info["registered_at"] = registered_at
            res.append(video_info)

        return res

    def _get_videoinfo(self, video_id: str) -> list[tuple[str, str, str]]:
        """動画情報を返す
        """
        # video_idのパターンはsm{投稿者id}00000{動画識別2桁}
        pattern = r"sm([0-9]{1})00000([0-9]{2})"
        n, m = re.findall(pattern, video_id)[0]
        title = f"動画タイトル{n}_{m}"
        uploaded_at = f"2022-04-29 0{n}:{m}:00"
        video_url = "https://www.nicovideo.jp/watch/" + video_id
        user_id = n * 8
        username = f"動画投稿者{n}"

        res = {
            "video_id": Videoid(video_id),            # 動画ID [sm12345678]
            "title": Title(title),                    # 動画タイトル [テスト動画]
            "uploaded_at": UploadedAt(uploaded_at),   # 投稿日時 [%Y-%m-%d %H:%M:%S]
            "video_url": VideoURL.create(video_url),  # 動画URL [https://www.nicovideo.jp/watch/sm12345678]
            "user_id": Userid(user_id),               # 投稿者id [投稿者1]
            "username": Username(username),           # 投稿者 [投稿者1]
        }
        return res

    def _get_xml_from_api(self, video_id: str) -> str:
        """APIから返ってくる動画情報セットxmlを返す
        """
        video_info = self._get_videoinfo(video_id)
        title = video_info.get("title").name
        watch_url = video_info.get("video_url").original_url
        user_id = video_info.get("user_id").id
        user_nickname = video_info.get("username").name

        src_df = "%Y-%m-%dT%H:%M:%S+0900"
        dst_df = "%Y-%m-%d %H:%M:%S"
        first_retrieve = video_info.get("uploaded_at").dt_str
        first_retrieve = datetime.strptime(first_retrieve, dst_df).strftime(src_df)

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

    def _make_api_response_mock(self, request_url, status_code: int = 200, error_target: str = ""):
        mock = MagicMock()

        pattern = "^https://ext.nicovideo.jp/api/getthumbinfo/(sm[0-9]+)$"
        video_id = re.findall(pattern, request_url)[0]
        xml = self._get_xml_from_api(video_id)
        html = HTML(html=xml)

        mock.html = html
        return mock

    def _make_api_session_response_mock(self, mock, status_code: int = 200, error_target: str = "") -> tuple[AsyncMock, MagicMock]:
        async def ReturnSessionResponse(request_url: str,
                                        do_rendering: bool,
                                        parse_features: str = "html.parser",
                                        session: AsyncHTMLSession = None) -> tuple[AsyncMock, MagicMock]:
            ar_session = AsyncMock()
            if error_target == "HTTPError":
                raise HTTPError
            if status_code == 503:
                return (ar_session, None)

            r_response = self._make_api_response_mock(request_url, status_code, error_target)
            return (ar_session, r_response)

        mock.side_effect = ReturnSessionResponse
        return mock

    def test_VideoInfoFetcherBaseInit(self):
        """VideoInfoFetcherBase の初期化後の状態をテストする
        """
        # 正常系
        source_type = SourceType.HTML
        urls = self._get_url_set()
        for url in urls:
            cvif = ConcreteVideoInfoFetcher(url)

            if UploadedURL.is_valid(url):
                expect_url = UploadedURL.create(url)
            elif MylistURL.is_valid(url):
                expect_url = MylistURL.create(url)

            self.assertEqual(expect_url, cvif.url)
            self.assertEqual(source_type, cvif.source_type)

            API_URL_BASE = "https://ext.nicovideo.jp/api/getthumbinfo/"
            self.assertEqual(API_URL_BASE, VideoInfoFetcherBase.API_URL_BASE)

            MAX_RETRY_NUM = 5
            self.assertEqual(MAX_RETRY_NUM, VideoInfoFetcherBase.MAX_RETRY_NUM)

        # 異常系
        # urlが不正
        url = "不正なURL"
        with self.assertRaises(ValueError):
            cvif = ConcreteVideoInfoFetcher(url)

    def test_get_session_response(self):
        """_get_session_response のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.logger.error"))
            mockas = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.AsyncHTMLSession"))
            mockpp = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.pyppeteer.launch"))
            mocksl = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.asyncio.sleep"))

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
            url = self._get_url_set()[0]
            cvif = ConcreteVideoInfoFetcher(url)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_session_response(cvif.url.non_query_url, True, "html.parser", None))
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

            assertMockCall(cvif.url.non_query_url, True, None)

            # do_renderingがFalse, sessionがNone
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_session_response(cvif.url.non_query_url, False, "html.parser", None))
            expect = (session, response)
            self.assertEqual(expect, actual)
            assertMockCall(url, False, None)

            # do_renderingがTrue, sessionがNoneでない
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_session_response(cvif.url.non_query_url, True, "html.parser", session))
            expect = (session, response)
            self.assertEqual(expect, actual)
            assertMockCall(url, True, session)

            # do_renderingがFalse, sessionがNoneでない
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_session_response(cvif.url.non_query_url, False, "html.parser", session))
            expect = (session, response)
            self.assertEqual(expect, actual)
            assertMockCall(url, False, session)

            # リトライして成功するパターン
            session.get.side_effect = MakeReturnGet(MAX_RETRY_NUM - 1, False)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_session_response(cvif.url.non_query_url, True, "html.parser", None))
            expect = (session, response)
            self.assertEqual(expect, actual)

            # TODO::"lxml-xml" 指定時のテスト

            # 異常系
            # MAX_RETRY_NUM回リトライしたが失敗したパターン
            session.get.side_effect = MakeReturnGet(MAX_RETRY_NUM, False)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_session_response(cvif.url.non_query_url, True, "html.parser", None))
            expect = (session, None)
            self.assertEqual(expect, actual)

            # responseの取得に成功したがresponse.html.lxmlが存在しないパターン
            session.get.side_effect = MakeReturnGet(0, True)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_session_response(cvif.url.non_query_url, True, "html.parser", None))
            expect = (session, None)
            self.assertEqual(expect, actual)

    def test_get_videoinfo_from_api(self):
        """_get_videoinfo_from_api のテスト
        """
        with ExitStack() as stack:
            mockapises = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.VideoInfoFetcherBase._get_session_response"))

            # 正常系
            mockapises = self._make_api_session_response_mock(mockapises, 200)

            expect = {}
            mylist_url = self._get_url_set()[0]
            video_info_list = self._get_videoinfo_set(mylist_url)
            video_id_list = [video_info["video_id"] for video_info in video_info_list]
            title_list = [video_info["title"] for video_info in video_info_list]
            uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
            video_url_list = [video_info["video_url"] for video_info in video_info_list]
            username_list = [video_info["username"] for video_info in video_info_list]
            num = len(video_id_list)

            video_id_list = VideoidList.create(video_id_list)
            title_list = TitleList.create(title_list)
            uploaded_at_list = UploadedAtList.create(uploaded_at_list)
            video_url_list = VideoURLList.create(video_url_list)
            username_list = UsernameList.create(username_list)
            
            expect = {
                "no": list(range(1, num + 1)),          # No. [1, ..., len()-1]
                "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
                "title_list": title_list,               # 動画タイトルリスト [テスト動画]
                "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                "username_list": username_list,         # 投稿者リスト [投稿者1]
            }

            cvif = ConcreteVideoInfoFetcher(mylist_url)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_videoinfo_from_api(video_id_list))
            self.assertEqual(expect, actual.to_dict())

            # 異常系
            # _get_session_response に失敗
            mockapises = self._make_api_session_response_mock(mockapises, 503)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            with self.assertRaises(ValueError):
                actual = loop.run_until_complete(cvif._get_videoinfo_from_api(video_id_list))

    def test_abstractmethod_fetch_videoinfo(self):
        """_fetch_videoinfo のテスト
        """
        url = self._get_url_set()[0]
        cvif = ConcreteVideoInfoFetcher(url)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        actual = loop.run_until_complete(cvif._fetch_videoinfo())
        self.assertEqual(["test_fetch_videoinfo"], actual)

    def test_classmethod_fetch_videoinfo(self):
        """fetch_videoinfo のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.logger.error"))

            # 正常系
            url = self._get_url_set()[0]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(ConcreteVideoInfoFetcher.fetch_videoinfo(url))
            self.assertEqual(["test_fetch_videoinfo"], actual)

            # 異常系
            # VideoInfoFetcherBase の fetch_videoinfo を直接呼んでも内部でインスタンス化できないので失敗する
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(VideoInfoFetcherBase.fetch_videoinfo(url))
            self.assertEqual([], actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
