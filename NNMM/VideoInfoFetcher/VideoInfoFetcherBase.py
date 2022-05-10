# coding: utf-8
import asyncio
import logging.config
import pprint
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from logging import INFO, getLogger

import pyppeteer
from lxml.html.soupparser import fromstring as soup_parse
from requests_html import AsyncHTMLSession, HTMLResponse

from NNMM import ConfigMain
from NNMM.VideoInfoFetcher.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.URL import URL
from NNMM.VideoInfoFetcher.FetchedVideoInfo import FetchedAPIVideoInfo
from NNMM.VideoInfoFetcher.UploadedURL import UploadedURL


logger = getLogger("root")
logger.setLevel(INFO)


# URLタイプ
class SourceType(Enum):
    HTML = "html"
    RSS = "rss"


@dataclass
class VideoInfoFetcherBase(ABC):
    url: URL
    source_type: SourceType

    API_URL_BASE = "https://ext.nicovideo.jp/api/getthumbinfo/"
    MAX_RETRY_NUM = 5

    def __init__(self, url: str, source_type: SourceType):
        if UploadedURL.is_valid(url):
            self.url = UploadedURL.factory(url)
        elif MylistURL.is_valid(url):
            self.url = MylistURL.factory(url)
        self.source_type = source_type

    async def _get_session_response(self,
                                    request_url: str,
                                    do_rendering: bool = False,
                                    parse_features: str = "html.parser",
                                    session: AsyncHTMLSession = None) -> tuple[AsyncHTMLSession, HTMLResponse]:
        """非同期でページ取得する

        Notes:
            この関数で取得したAsyncHTMLSession は呼び出し側で
            await session.close() することを推奨
            接続は self.MAX_RETRY_NUM = 5 回試行する
            この回数リトライしてもページ取得できなかった場合、responseがNoneとなる

        Args:
            do_rendering (bool): 動的にレンダリングするかどうか
            parse_features (str): soup_parse に渡すparserを表す文字列 ["html.parser", "lxml-xml"]
            session (AsyncHTMLSession, optional): 使い回すセッションがあれば指定

        Returns:
            session (AsyncHTMLSession): 非同期セッション
            response (HTMLResponse): ページ取得結果のレスポンス
                                    リトライ回数超過時None
                                    正常時 response.html.lxml が非Noneであることが保証されたresponse
        """
        if not session:
            # セッション開始
            session = AsyncHTMLSession()
            browser = await pyppeteer.launch({
                "ignoreHTTPSErrors": True,
                "headless": True,
                "handleSIGINT": False,
                "handleSIGTERM": False,
                "handleSIGHUP": False
            })
            session._browser = browser

        response = None
        for _ in range(self.MAX_RETRY_NUM):
            try:
                response = await session.get(request_url)
                response.raise_for_status()

                if do_rendering:
                    await response.html.arender(sleep=2)
                response.raise_for_status()

                # if parse_features != "html.parser":
                #     response.html._lxml = soup_parse(response.html.html, features=parse_features)

                if (response is not None) and (response.html.lxml is not None):
                    break

                await asyncio.sleep(1)
            except Exception:
                logger.error(traceback.format_exc())
        else:
            response = None

        return (session, response)

    async def _get_videoinfo_from_api(self, video_id_list: list[str]) -> FetchedAPIVideoInfo:
        """動画IDからAPIを通して動画情報を取得する

        Notes:
            video_id_listで渡された動画IDについてAPIを通して動画情報を取得する
            動画情報API："https://ext.nicovideo.jp/api/getthumbinfo/{動画ID}"

        Args:
            video_id_list (list[str]): 動画IDリスト

        Returns:
            FetchedAPIVideoInfo: 解析結果
        """
        src_df = "%Y-%m-%dT%H:%M:%S%z"
        dst_df = "%Y-%m-%d %H:%M:%S"

        title_list = []
        uploaded_at_list = []
        video_url_list = []
        username_list = []
        session = None
        for video_id in video_id_list:
            url = self.API_URL_BASE + video_id
            session, response = await self._get_session_response(url, False, "lxml-xml", session)
            if response:
                thumb_lx = response.html.lxml.findall("thumb")[0]

                # 動画タイトル
                title_lx = thumb_lx.findall("title")
                title = title_lx[0].text
                title_list.append(title)

                # 投稿日時
                uploaded_at_lx = thumb_lx.findall("first_retrieve")
                uploaded_at = datetime.strptime(uploaded_at_lx[0].text, src_df).strftime(dst_df)
                uploaded_at_list.append(uploaded_at)

                # 動画URL
                video_url_lx = thumb_lx.findall("watch_url")
                video_url = video_url_lx[0].text
                video_url_list.append(video_url)

                # 投稿者
                username_lx = thumb_lx.findall("user_nickname")
                username = username_lx[0].text
                username_list.append(username)

        await session.close()

        num = len(video_id_list)
        res = {
            "no": list(range(1, num + 1)),          # No. [1, ..., len()-1]
            "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
            "title_list": title_list,               # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
            "username_list": username_list,         # 投稿者リスト [投稿者1]
        }

        return FetchedAPIVideoInfo(**res)

    @abstractmethod
    async def _fetch_videoinfo(self) -> list[dict]:
        return []

    @classmethod
    async def fetch_videoinfo(cls, url: str) -> list[dict]:
        res = []
        try:
            fetcher = cls(url)
            res = await fetcher._fetch_videoinfo()
        except Exception:
            logger.error(traceback.format_exc())
            return []

        return res


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    ConfigMain.ProcessConfigBase.SetConfig()

    class ConcreteVideoInfoFetcher(VideoInfoFetcherBase):
        def __init__(self, url: str):
            super().__init__(url, SourceType.HTML)

        async def _fetch_videoinfo(self) -> list[dict]:
            return await self._get_videoinfo_from_api(["sm9"])

    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/12899156/mylist/39194985",  # 中量マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/67376990",  # 少量マイリスト
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    for url in urls:
        video_list = loop.run_until_complete(ConcreteVideoInfoFetcher.fetch_videoinfo(url))
        pprint.pprint(video_list)

    pass
