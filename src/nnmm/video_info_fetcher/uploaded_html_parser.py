import asyncio
import html
from dataclasses import dataclass
from datetime import datetime

import orjson
from bs4 import BeautifulSoup

from nnmm.util import MylistType, find_values
from nnmm.video_info_fetcher.parser_base import ParserBase
from nnmm.video_info_fetcher.value_objects.myshowname import Myshowname
from nnmm.video_info_fetcher.value_objects.showname import Showname
from nnmm.video_info_fetcher.value_objects.title import Title
from nnmm.video_info_fetcher.value_objects.title_list import TitleList
from nnmm.video_info_fetcher.value_objects.uploaded_at import UploadedAt
from nnmm.video_info_fetcher.value_objects.uploaded_at_list import UploadedAtList
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.username_list import UsernameList
from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid import Videoid
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


@dataclass
class UploadedHtmlParser(ParserBase):
    soup: BeautifulSoup
    data: dict

    SOURCE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, url: str, response_text: str) -> None:
        super().__init__(url, response_text)
        if self.mylist_url.mylist_type != MylistType.uploaded:
            raise ValueError(f"url must be MylistType.uploaded: {url}.")

        # 投稿動画ページも内部APIを用いるので引数はそのままJSONを想定
        self.data = orjson.loads(response_text)

    def _get_username(self) -> Username:
        """投稿者収集

        投稿動画が一つも存在しない場合は
        作成者=投稿者の情報がAPI返り値内に存在しないためエラー
        """
        items = find_values(self.data, "items", True, ["data"], [])
        if not items:
            raise ValueError(f"this url not contain video, getting failed username: {self.mylist_url.non_query_url}.")

        username = find_values(items, "name", False, [], [])[0]
        return Username(username)

    def _get_showname_myshowname(self) -> tuple[Showname, Myshowname]:
        """マイリスト名収集"""
        username = self._get_username()
        myshowname = Myshowname("投稿動画")
        showname = Showname.create(MylistType.uploaded, username, None)
        return (showname, myshowname)

    def _get_entries(self) -> tuple[VideoidList, TitleList, UploadedAtList, VideoURLList, UsernameList]:
        """エントリー収集"""
        items = find_values(self.data, "items", True, ["data", "mylist"], [])

        video_id_list = []
        title_list = []
        uploaded_at_list = []
        video_url_list = []
        username_list = []

        for item in items:
            e = item["essential"]

            video_id = e["id"]
            title = e["title"]
            uploaded_at = e["registeredAt"]
            video_url = f"https://www.nicovideo.jp/watch/{video_id}"
            username = e["owner"]["name"]

            video_id_list.append(Videoid(video_id))
            title_list.append(Title(title))
            uploaded_at_list.append(
                UploadedAt(
                    datetime.strptime(uploaded_at, self.SOURCE_DATETIME_FORMAT).strftime(
                        self.DESTINATION_DATETIME_FORMAT
                    )
                )
            )
            video_url_list.append(VideoURL.create(URL(video_url).non_query_url))
            username_list.append(username)

        video_id_list = VideoidList.create(video_id_list)
        title_list = TitleList.create(title_list)
        uploaded_at_list = UploadedAtList.create(uploaded_at_list)
        video_url_list = VideoURLList.create(video_url_list)
        username_list = UsernameList.create(username_list)
        return (video_id_list, title_list, uploaded_at_list, video_url_list, username_list)


if __name__ == "__main__":
    import pprint

    from nnmm.video_info_fetcher.video_info_fetcher import VideoInfoFetcher

    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        # "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/12899156/series/442402",  # シリーズ
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    for url in urls:
        virf = VideoInfoFetcher(url)
        response = loop.run_until_complete(virf._get_session_response(virf.mylist_url.fetch_url))
        hp = UploadedHtmlParser(url, response.text)
        fetched_page_video_info = loop.run_until_complete(hp.parse())

        pprint.pprint(fetched_page_video_info.to_dict())
    pass
