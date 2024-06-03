import sys
import unittest
from datetime import datetime
from itertools import repeat
from urllib.error import HTTPError
from urllib.parse import urlparse

from mock import AsyncMock, MagicMock, patch

from nnmm.util import Result
from nnmm.video_info_fetcher.value_objects.fetched_api_video_info import FetchedAPIVideoInfo
from nnmm.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo
from nnmm.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory
from nnmm.video_info_fetcher.value_objects.title import Title
from nnmm.video_info_fetcher.value_objects.title_list import TitleList
from nnmm.video_info_fetcher.value_objects.uploaded_at import UploadedAt
from nnmm.video_info_fetcher.value_objects.uploaded_at_list import UploadedAtList
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.username_list import UsernameList
from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList
from nnmm.video_info_fetcher.video_info_fetcher_base import VideoInfoFetcherBase


# テスト用具体化ProcessBase
class ConcreteVideoInfoFetcher(VideoInfoFetcherBase):
    def __init__(self, url: str) -> None:
        super().__init__(url)

    async def _fetch_videoinfo(self) -> FetchedVideoInfo:
        return "test_fetch_videoinfo"


class TestVideoInfoFetcherBase(unittest.IsolatedAsyncioTestCase):
    def _get_url_set(self) -> list[str]:
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

    def test_init(self):
        urls = self._get_url_set()
        for url in urls:
            instance = ConcreteVideoInfoFetcher(url)
            expect_url = MylistURLFactory.create(url)
            self.assertEqual(expect_url, instance.mylist_url)

            API_URL_BASE = "https://ext.nicovideo.jp/api/getthumbinfo/"
            self.assertEqual(API_URL_BASE, VideoInfoFetcherBase.API_URL_BASE)

            MAX_RETRY_NUM = 5
            self.assertEqual(MAX_RETRY_NUM, VideoInfoFetcherBase.MAX_RETRY_NUM)

        url = "https://invalid.invalid/user/11111111/video"
        with self.assertRaises(ValueError):
            instance = ConcreteVideoInfoFetcher(url)

    async def test_get_session_response(self):
        mock_logger_error = self.enterContext(patch("nnmm.video_info_fetcher.video_info_fetcher_base.logger.error"))
        mock_async_client = self.enterContext(
            patch("nnmm.video_info_fetcher.video_info_fetcher_base.httpx.AsyncClient")
        )

        # 正常系
        mock_response = MagicMock()
        mock_get = AsyncMock()
        mock_get.get.side_effect = lambda url: mock_response
        mock_aenter = MagicMock()
        mock_aenter.__aenter__.side_effect = lambda: mock_get
        mock_async_client.side_effect = lambda follow_redirects, timeout, transport: mock_aenter

        url = self._get_url_set()[0]
        instance = ConcreteVideoInfoFetcher(url)
        request_url = instance.mylist_url.non_query_url
        actual = await instance._get_session_response(request_url)
        expect = mock_response
        self.assertEqual(expect, actual)

        # 呼び出し確認::TODO

        mock_response.reset_mock()
        mock_get.reset_mock()
        mock_aenter.reset_mock()
        mock_async_client.reset_mock()

        # 異常系
        # MAX_RETRY_NUM回リトライしたが失敗したパターン
        mock_get.get.side_effect = list(repeat(HTTPError, instance.MAX_RETRY_NUM + 1))
        actual = await instance._get_session_response(request_url)
        expect = None
        self.assertEqual(expect, actual)

    async def test_get_videoinfo_from_api(self):
        mock_logger_error = self.enterContext(patch("nnmm.video_info_fetcher.video_info_fetcher_base.logger.error"))
        mock_async_client = self.enterContext(
            patch("nnmm.video_info_fetcher.video_info_fetcher_base.httpx.AsyncClient")
        )

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
        instance = ConcreteVideoInfoFetcher(url)

        src_df = "%Y-%m-%dT%H:%M:%S%z"
        dst_df = "%Y-%m-%d %H:%M:%S"
        title_list = [Title(f"動画タイトル_{i:02}") for i in range(1, num + 1)]
        uploaded_at_list = [
            UploadedAt(datetime.strptime(f"2007-03-06T00:33:{i:02}+09:00", src_df).strftime(dst_df))
            for i in range(1, num + 1)
        ]
        video_url_list = [VideoURL.create(f"https://www.nicovideo.jp/watch/sm{i}") for i in range(1, num + 1)]
        username_list = [Username(f"username_{i:02}") for i in range(1, num + 1)]
        title_list = TitleList.create(title_list)
        uploaded_at_list = UploadedAtList.create(uploaded_at_list)
        video_url_list = VideoURLList.create(video_url_list)
        username_list = UsernameList.create(username_list)
        res = {
            "no": list(range(1, num + 1)),  # No. [1, ..., len()-1]
            "video_id_list": video_id_list,  # 動画IDリスト [sm12345678]
            "title_list": title_list,  # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,  # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,  # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
            "username_list": username_list,  # 投稿者リスト [投稿者1]
        }
        expect = FetchedAPIVideoInfo(**res)

        actual = await instance._get_videoinfo_from_api(video_id_list)
        self.assertEqual(expect, actual)

        # 呼び出し確認::TODO

        mock_get.reset_mock()
        mock_aenter.reset_mock()
        mock_async_client.reset_mock()

        # getに失敗
        mock_get.get.side_effect = ValueError
        with self.assertRaises(ValueError):
            actual = await instance._get_videoinfo_from_api(video_id_list)

        # 引数が不正
        video_id_list = []
        with self.assertRaises(ValueError):
            actual = await instance._get_videoinfo_from_api(video_id_list)

    async def test__fetch_videoinfo(self):
        url = self._get_url_set()[0]
        instance = ConcreteVideoInfoFetcher(url)
        actual = await instance._fetch_videoinfo()
        self.assertEqual("test_fetch_videoinfo", actual)

    async def test_fetch_videoinfo(self):
        mock_logger_error = self.enterContext(patch("nnmm.video_info_fetcher.video_info_fetcher_base.logger.error"))

        url = self._get_url_set()[0]
        actual = await ConcreteVideoInfoFetcher.fetch_videoinfo(url)
        self.assertEqual("test_fetch_videoinfo", actual)

        # VideoInfoFetcherBase の fetch_videoinfo を直接呼んでも内部でインスタンス化できないので失敗する
        actual = await VideoInfoFetcherBase.fetch_videoinfo(url)
        self.assertEqual(Result.failed, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
