import asyncio
import pprint
import re
from dataclasses import dataclass
from datetime import datetime

import xmltodict

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
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


@dataclass
class MylistRSSXmlParser(ParserBase):
    xml_dict: dict

    SOURCE_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, url: str, response_text: str) -> None:
        super().__init__(url, response_text)
        if self.mylist_url.mylist_type != MylistType.mylist:
            raise ValueError(f"url must be MylistType.mylist: {url}.")
        self.xml_dict = xmltodict.parse(response_text)

    def _get_username(self) -> Username:
        """投稿者収集"""
        username = find_values(self.xml_dict, "dc:creator", True, [], [])
        return Username(username)

    def _get_showname_myshowname(self) -> tuple[Showname, Myshowname]:
        """マイリスト名収集"""
        username = self._get_username()

        # タイトルから取得
        page_title = find_values(self.xml_dict, "title", True, ["rss", "channel"], ["item"])
        pattern = "^マイリスト (.*)‐ニコニコ動画$"
        myshowname = Myshowname(re.findall(pattern, page_title)[0])
        showname = Showname.create(MylistType.mylist, username, myshowname)
        return (showname, myshowname)

    def _get_entries(self) -> tuple[VideoidList, TitleList, RegisteredAtList, VideoURLList]:
        """エントリー収集"""
        items_dict = find_values(self.xml_dict, "item", True, [], [])
        video_url_list = [
            VideoURL.create(URL(video_url).non_query_url)
            for video_url in find_values(items_dict, "link", False, [], [])
        ]
        video_id_list = [video_url.video_id for video_url in video_url_list]
        title_list = [Title(title) for title in find_values(items_dict, "title", False, [], [])]
        registered_at_list = [
            RegisteredAt(
                datetime.strptime(pub_date, self.SOURCE_DATETIME_FORMAT).strftime(self.DESTINATION_DATETIME_FORMAT)
            )
            for pub_date in find_values(items_dict, "pubDate", False, [], [])
        ]

        video_id_list = VideoidList.create(video_id_list)
        title_list = TitleList.create(title_list)
        registered_at_list = RegisteredAtList.create(registered_at_list)
        video_url_list = VideoURLList.create(video_url_list)
        return (video_id_list, title_list, registered_at_list, video_url_list)


if __name__ == "__main__":
    from nnmm.video_info_fetcher.video_info_fetcher import VideoInfoFetcher

    urls = [
        # "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        # "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/12899156/series/442402",  # シリーズ
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    for url in urls:
        virf = VideoInfoFetcher(url)
        response = loop.run_until_complete(virf._get_session_response(virf.mylist_url.fetch_url))
        rp = MylistRSSXmlParser(url, response.text)
        fetched_page_video_info = loop.run_until_complete(rp.parse())

        pprint.pprint(fetched_page_video_info.to_dict())
    pass
