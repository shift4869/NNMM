import asyncio
import html
from dataclasses import dataclass
from datetime import datetime

import orjson
from bs4 import BeautifulSoup

from nnmm.util import MylistType, find_values
from nnmm.video_info_fetcher.parser_base import ParserBase
from nnmm.video_info_fetcher.value_objects.myshowname import Myshowname
from nnmm.video_info_fetcher.value_objects.registered_at import RegisteredAt
from nnmm.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from nnmm.video_info_fetcher.value_objects.showname import Showname
from nnmm.video_info_fetcher.value_objects.title import Title
from nnmm.video_info_fetcher.value_objects.title_list import TitleList
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid import Videoid
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


@dataclass
class MylistHtmlParser(ParserBase):
    soup: BeautifulSoup
    data: dict

    SOURCE_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, url: str, response_text: str) -> None:
        super().__init__(url, response_text)
        if self.mylist_url.mylist_type != MylistType.mylist:
            raise ValueError(f"url must be MylistType.mylist: {url}.")

        # マイリストAPI返り値はそのままJSON
        self.data = orjson.loads(response_text)

    def _get_username(self) -> Username:
        """投稿者収集"""
        username = find_values(self.data["data"]["mylist"]["owner"], "name", True, [], [])
        return Username(username)

    def _get_showname_myshowname(self) -> tuple[Showname, Myshowname]:
        """マイリスト名収集"""
        # マイリスト情報
        mylist_name = find_values(self.data, "name", True, ["data", "mylist"], [])
        username = self._get_username()

        myshowname = Myshowname(mylist_name)
        showname = Showname.create(MylistType.mylist, username, myshowname)
        return (showname, myshowname)

    def _get_entries(self) -> tuple[VideoidList, TitleList, RegisteredAtList, VideoURLList]:
        """エントリー収集"""
        # 動画一覧
        items = find_values(self.data, "items", True, ["data", "mylist"], [])

        video_id_list = []
        title_list = []
        registered_at_list = []
        video_url_list = []

        for item in items:
            e = item["video"]
            video_id = e["id"]
            title = e["title"]
            registered_at = e["registeredAt"]
            video_url = f"https://www.nicovideo.jp/watch/{video_id}"

            video_id_list.append(Videoid(video_id))
            title_list.append(Title(title))
            registered_at_list.append(
                RegisteredAt(
                    datetime.strptime(registered_at, self.SOURCE_DATETIME_FORMAT).strftime(
                        self.DESTINATION_DATETIME_FORMAT
                    )
                )
            )
            video_url_list.append(VideoURL.create(URL(video_url).non_query_url))

        video_id_list = VideoidList.create(video_id_list)
        title_list = TitleList.create(title_list)
        registered_at_list = RegisteredAtList.create(registered_at_list)
        video_url_list = VideoURLList.create(video_url_list)
        return (video_id_list, title_list, registered_at_list, video_url_list)


if __name__ == "__main__":
    import pprint

    from nnmm.video_info_fetcher.video_info_fetcher import VideoInfoFetcher

    urls = [
        # "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/12899156/series/442402",  # シリーズ
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    for url in urls:
        virf = VideoInfoFetcher(url)
        response = loop.run_until_complete(virf._get_session_response(virf.mylist_url.fetch_url))
        hp = MylistHtmlParser(url, response.text)
        fetched_page_video_info = loop.run_until_complete(hp.parse())

        pprint.pprint(fetched_page_video_info.to_dict())
    pass
