import asyncio
import pprint
import re
from dataclasses import dataclass
from datetime import datetime

import xmltodict

from NNMM.util import find_values
from NNMM.video_info_fetcher.value_objects.fetched_page_video_info import FetchedPageVideoInfo
from NNMM.video_info_fetcher.value_objects.mylist_url import MylistURL
from NNMM.video_info_fetcher.value_objects.mylistid import Mylistid
from NNMM.video_info_fetcher.value_objects.myshowname import Myshowname
from NNMM.video_info_fetcher.value_objects.registered_at import RegisteredAt
from NNMM.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from NNMM.video_info_fetcher.value_objects.showname import Showname
from NNMM.video_info_fetcher.value_objects.title import Title
from NNMM.video_info_fetcher.value_objects.title_list import TitleList
from NNMM.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from NNMM.video_info_fetcher.value_objects.userid import Userid
from NNMM.video_info_fetcher.value_objects.username import Username
from NNMM.video_info_fetcher.value_objects.video_url import VideoURL
from NNMM.video_info_fetcher.value_objects.video_url_list import VideoURLList
from NNMM.video_info_fetcher.value_objects.videoid_list import VideoidList


@dataclass
class RSSParser:
    mylist_url: UploadedURL | MylistURL
    xml_dict: dict

    SOURCE_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, url: str, xml_text: str) -> None:
        if UploadedURL.is_valid(url):
            self.mylist_url = UploadedURL.create(url)
        elif MylistURL.is_valid(url):
            self.mylist_url = MylistURL.create(url)
        self.xml_dict = xmltodict.parse(xml_text)

    def _get_mylist_url(self) -> UploadedURL | MylistURL:
        """マイリストURL"""
        return self.mylist_url

    def _get_userid_mylistid(self) -> tuple[Userid, Mylistid]:
        """ユーザーID, マイリストID設定"""
        userid = self.mylist_url.userid
        mylistid = self.mylist_url.mylistid
        return (userid, mylistid)

    def _get_username(self) -> Username:
        """投稿者収集"""
        if isinstance(self.mylist_url, UploadedURL):
            # タイトルからユーザー名を取得
            title = find_values(self.xml_dict, "title", True, ["rss", "channel"], [])
            pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
            username = re.findall(pattern, title)[0]
        elif isinstance(self.mylist_url, MylistURL):
            username = find_values(self.xml_dict, "dc:creator", True, [], [])
        return Username(username)

    def _get_showname_myshowname(self) -> tuple[Showname, Myshowname]:
        """マイリスト名収集"""
        username = self._get_username()
        if isinstance(self.mylist_url, UploadedURL):
            myshowname = Myshowname("投稿動画")
            showname = Showname.create(username, None)
            return (showname, myshowname)
        elif isinstance(self.mylist_url, MylistURL):
            # マイリストの場合はタイトルから取得
            page_title = find_values(self.xml_dict, "title", True, ["rss", "channel"], ["item"])
            pattern = "^マイリスト (.*)‐ニコニコ動画$"
            myshowname = Myshowname(re.findall(pattern, page_title)[0])
            showname = Showname.create(username, myshowname)
            return (showname, myshowname)
        raise AttributeError("(showname, myshowname) parse failed.")

    async def parse(self) -> FetchedPageVideoInfo:
        """投稿動画ページのhtmlを解析する

        Returns:
            FetchedPageVideoInfo: 解析結果

        Raises:
            AttributeError: html解析失敗時
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """
        # マイリストURL設定
        mylist_url = self._get_mylist_url()

        # 投稿者IDとマイリストID取得
        userid, mylistid = self._get_userid_mylistid()

        # ユーザー名を取得
        username = self._get_username()

        # マイリスト名収集
        # 投稿動画の場合はマイリスト名がないのでユーザー名と合わせて便宜上の名前に設定
        showname, myshowname = self._get_showname_myshowname()

        # 動画エントリ取得
        items_dict = find_values(self.xml_dict, "item", True, [], [])
        video_url_list = [VideoURL.create(video_url) for video_url in find_values(items_dict, "link", False, [], [])]
        video_id_list = [video_url.video_id for video_url in video_url_list]
        title_list = [Title(title) for title in find_values(items_dict, "title", False, [], [])]
        registered_at_list = [
            RegisteredAt(
                datetime.strptime(pub_date, self.SOURCE_DATETIME_FORMAT).strftime(self.DESTINATION_DATETIME_FORMAT)
            )
            for pub_date in find_values(items_dict, "pubDate", False, [], [])
        ]
        num = len(video_url_list)
        check_list = [
            num == len(video_url_list),
            num == len(video_id_list),
            num == len(title_list),
            num == len(registered_at_list),
        ]
        if not all(check_list):
            raise ValueError("video entry parse failed.")

        # ValueObjectに変換
        video_id_list = VideoidList.create(video_id_list)
        title_list = TitleList.create(title_list)
        registered_at_list = RegisteredAtList.create(registered_at_list)
        video_url_list = VideoURLList.create(video_url_list)

        # 返り値設定
        res = {
            "no": list(range(1, num + 1)),  # No. [1, ..., len()-1]
            "userid": userid,  # ユーザーID 1234567
            "mylistid": mylistid,  # マイリストID 12345678
            "showname": showname,  # マイリスト表示名 「投稿者1さんの投稿動画」
            "myshowname": myshowname,  # マイリスト名 「投稿動画」
            "mylist_url": mylist_url,  # マイリストURL https://www.nicovideo.jp/user/11111111/video
            "video_id_list": video_id_list,  # 動画IDリスト [sm12345678]
            "title_list": title_list,  # 動画タイトルリスト [テスト動画]
            "registered_at_list": registered_at_list,  # 登録日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,  # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        }
        return FetchedPageVideoInfo(**res)


if __name__ == "__main__":
    from NNMM.video_info_fetcher.video_info_rss_fetcher import VideoInfoRssFetcher

    urls = [
        # "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    for url in urls:
        virf = VideoInfoRssFetcher(url)
        response = loop.run_until_complete(virf._get_session_response(virf.mylist_url.fetch_url))
        rp = RSSParser(url, response.text)
        soup_d = loop.run_until_complete(rp.parse())

        pprint.pprint(soup_d.to_dict())
    pass
