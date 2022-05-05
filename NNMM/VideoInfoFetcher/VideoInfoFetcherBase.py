# coding: utf-8
import asyncio
import logging.config
import pprint
import re
import traceback
import urllib.parse
from abc import ABC, abstractmethod
from datetime import datetime
from logging import INFO, getLogger

import pyppeteer
from lxml.html.soupparser import fromstring as soup_parse
from requests_html import AsyncHTMLSession, HTMLResponse

from NNMM import ConfigMain, GuiFunction


logger = getLogger("root")
logger.setLevel(INFO)


class VideoInfoFetcherBase(ABC):
    def __init__(self, url: str, source_type: str):
        # クエリ除去
        url = urllib.parse.urlunparse(
            urllib.parse.urlparse(url)._replace(query=None)
        )

        self.url = url
        self.source_type = source_type

        self.url_type = GuiFunction.GetURLType(self.url)
        if self.url_type not in ["uploaded", "mylist"]:
            raise ValueError("url_type is invalid , url is not target url.")

        # マイリストのURLならRSSが取得できるURLに加工
        self.request_url = url
        if self.url_type == "mylist":
            # "https://www.nicovideo.jp/mylist/[0-9]+/?rss=2.0" 形式でないとそのマイリストのRSSが取得できない
            pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
            self.request_url = re.sub("/user/[0-9]+", "", self.request_url)  # /user/{userid} 部分を削除

        # table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        # table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
        self.RESULT_DICT_COLS = ("no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname")
        self.API_URL_BASE = "https://ext.nicovideo.jp/api/getthumbinfo/"
        self.MAX_RETRY_NUM = 5

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
            request_url (str): 取得対象ページURL
            do_rendering (bool): 動的にレンダリングするかどうか
            session (AsyncHTMLSession, optional): 使い回すセッションがあれば指定

        Returns:
            parse_features (str): soup_parse に渡すparserを表す文字列 ["html.parser", "lxml-xml"]
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

    async def _get_videoinfo_from_api(self, video_id_list: list[str]) -> dict:
        """動画IDからAPIを通して動画情報を取得する

        Notes:
            video_id_listで渡された動画IDについてAPIを通して動画情報を取得する
            動画情報API："https://ext.nicovideo.jp/api/getthumbinfo/{動画ID}"

        Args:
            video_id_list (list[str]): 動画IDリスト

        Returns:
            dict: 解析結果をまとめた辞書
                {
                    "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
                    "title_list": title_list,               # 動画タイトルリスト [テスト動画]
                    "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                    "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                    "username_list": username_list,         # 投稿者リスト [投稿者1]
                }
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
        if not (len(title_list) == num and len(uploaded_at_list) == num and len(video_url_list) == num and len(username_list) == num):
            raise ValueError

        res = {
            "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
            "title_list": title_list,               # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
            "username_list": username_list,         # 投稿者リスト [投稿者1]
        }
        return res

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

    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/12899156/mylist/39194985",  # 中量マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/67376990",  # 少量マイリスト
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    for url in urls:
        video_list = loop.run_until_complete(VideoInfoFetcherBase.fetch_videoinfo(url, "html"))
        pprint.pprint(video_list)
        video_list = loop.run_until_complete(VideoInfoFetcherBase.fetch_videoinfo(url, "rss"))
        pprint.pprint(video_list)

    pass
