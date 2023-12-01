import asyncio
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime
from itertools import repeat
from urllib.error import HTTPError
from urllib.parse import urlparse

from mock import AsyncMock, MagicMock, patch

from NNMM.VideoInfoFetcher.ValueObjects.FetchedAPIVideoInfo import FetchedAPIVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.ValueObjects.Title import Title
from NNMM.VideoInfoFetcher.ValueObjects.TitleList import TitleList
from NNMM.VideoInfoFetcher.ValueObjects.UploadedAt import UploadedAt
from NNMM.VideoInfoFetcher.ValueObjects.UploadedAtList import UploadedAtList
from NNMM.VideoInfoFetcher.ValueObjects.UploadedURL import UploadedURL
from NNMM.VideoInfoFetcher.ValueObjects.Username import Username
from NNMM.VideoInfoFetcher.ValueObjects.UsernameList import UsernameList
from NNMM.VideoInfoFetcher.ValueObjects.VideoidList import VideoidList
from NNMM.VideoInfoFetcher.ValueObjects.VideoURL import VideoURL
from NNMM.VideoInfoFetcher.ValueObjects.VideoURLList import VideoURLList
from NNMM.VideoInfoFetcher.VideoInfoFetcherBase import SourceType, VideoInfoFetcherBase


# テスト用具体化ProcessBase
class ConcreteVideoInfoFetcher(VideoInfoFetcherBase):
    def __init__(self, url: str, source_type: SourceType = SourceType.HTML) -> None:
        super().__init__(url, source_type)

    async def _fetch_videoinfo(self) -> list[dict]:
        return ["test_fetch_videoinfo"]


class TestVideoInfoFetcherBase(unittest.TestCase):
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

    def _make_api_xml(self, index: int = 0) -> str:
        return f"""
            <?xml version="1.0" encoding="UTF-8"?>
            <nicovideo_thumb_response status="ok">
                <thumb>
                    <video_id>sm{index}</video_id>
                    <first_retrieve>2007-03-06T00:33:{index:02}+09:00</first_retrieve>
                    <title>動画タイトル_{index:02}</title>
                    <watch_url>https://www.nicovideo.jp/watch/sm{index}</watch_url>
                    <user_nickname>username_{index:02}</user_nickname>
                </thumb>
            </nicovideo_thumb_response>
        """.strip()

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
            mock_logger_error = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.logger.error"))
            mock_async_client = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.httpx.AsyncClient"))

            # 正常系
            mock_response = MagicMock()
            mock_get = AsyncMock()
            mock_get.get.side_effect = lambda url: mock_response
            mock_aenter = MagicMock()
            mock_aenter.__aenter__.side_effect = lambda: mock_get
            mock_async_client.side_effect = lambda follow_redirects, timeout, transport: mock_aenter

            url = self._get_url_set()[0]
            cvif = ConcreteVideoInfoFetcher(url)
            request_url = cvif.url.non_query_url
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_session_response(request_url))
            expect = mock_response
            self.assertEqual(expect, actual)

            # 呼び出し確認::TODO


            mock_response.reset_mock()
            mock_get.reset_mock()
            mock_aenter.reset_mock()
            mock_async_client.reset_mock()

            # 異常系
            # MAX_RETRY_NUM回リトライしたが失敗したパターン
            mock_get.get.side_effect = list(repeat(HTTPError, cvif.MAX_RETRY_NUM + 1))
            actual = loop.run_until_complete(cvif._get_session_response(request_url))
            expect = None
            self.assertEqual(expect, actual)

    def test_get_videoinfo_from_api(self):
        """_get_videoinfo_from_api のテスト TODO
        """
        with ExitStack() as stack:
            mock_logger_error = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.logger.error"))
            mock_async_client = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoFetcherBase.httpx.AsyncClient"))

            def make_response(request_url):
                mock_response = MagicMock()
                videoid = urlparse(request_url).path.split("/")[-1]
                index = int(videoid[2:])
                mock_response.text = self._make_api_xml(index)
                return mock_response
            mock_get = AsyncMock()
            mock_get.get.side_effect = lambda url: make_response(url)
            mock_aenter = MagicMock()
            mock_aenter.__aenter__.side_effect = lambda: mock_get
            mock_async_client.side_effect = lambda follow_redirects, timeout, transport: mock_aenter

            num = 3
            video_id_str_list = [f"sm{i}" for i in range(1, num + 1)]
            video_id_list = VideoidList.create(video_id_str_list)
            url = self._get_url_set()[0]
            cvif = ConcreteVideoInfoFetcher(url)

            src_df = "%Y-%m-%dT%H:%M:%S%z"
            dst_df = "%Y-%m-%d %H:%M:%S"
            title_list = [
                Title(f"動画タイトル_{i:02}")
                for i in range(1, num + 1)
            ]
            uploaded_at_list = [
                UploadedAt(
                    datetime.strptime(f"2007-03-06T00:33:{i:02}+09:00", src_df).strftime(dst_df)
                )
                for i in range(1, num + 1)
            ]
            video_url_list = [
                VideoURL.create(f"https://www.nicovideo.jp/watch/sm{i}")
                for i in range(1, num + 1)
            ]
            username_list = [
                Username(f"username_{i:02}")
                for i in range(1, num + 1)
            ]
            title_list = TitleList.create(title_list)
            uploaded_at_list = UploadedAtList.create(uploaded_at_list)
            video_url_list = VideoURLList.create(video_url_list)
            username_list = UsernameList.create(username_list)
            res = {
                "no": list(range(1, num + 1)),          # No. [1, ..., len()-1]
                "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
                "title_list": title_list,               # 動画タイトルリスト [テスト動画]
                "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                "username_list": username_list,         # 投稿者リスト [投稿者1]
            }
            expect = FetchedAPIVideoInfo(**res)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(cvif._get_videoinfo_from_api(video_id_list))
            self.assertEqual(expect, actual)

            # 呼び出し確認::TODO

            mock_get.reset_mock()
            mock_aenter.reset_mock()
            mock_async_client.reset_mock()

            # getに失敗
            mock_get.get.side_effect = ValueError
            with self.assertRaises(ValueError):
                actual = loop.run_until_complete(cvif._get_videoinfo_from_api(video_id_list))

            # 引数が不正
            video_id_list = []
            with self.assertRaises(ValueError):
                actual = loop.run_until_complete(cvif._get_videoinfo_from_api(video_id_list))

    def test_fetch_videoinfo(self):
        """_fetch_videoinfo のテスト
        """
        url = self._get_url_set()[0]
        cvif = ConcreteVideoInfoFetcher(url)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        actual = loop.run_until_complete(cvif._fetch_videoinfo())
        self.assertEqual(["test_fetch_videoinfo"], actual)

    def test_fetch_videoinfo(self):
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
