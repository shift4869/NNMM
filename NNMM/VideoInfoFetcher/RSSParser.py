# coding: utf-8
import asyncio
import pprint
import re
from dataclasses import dataclass
from datetime import datetime

from bs4 import BeautifulSoup, Tag

from NNMM.VideoInfoFetcher.ValueObjects.FetchedPageVideoInfo import FetchedPageVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.ItemInfo import ItemInfo
from NNMM.VideoInfoFetcher.ValueObjects.Mylistid import Mylistid
from NNMM.VideoInfoFetcher.ValueObjects.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.ValueObjects.Myshowname import Myshowname
from NNMM.VideoInfoFetcher.ValueObjects.RegisteredAt import RegisteredAt
from NNMM.VideoInfoFetcher.ValueObjects.RegisteredAtList import RegisteredAtList
from NNMM.VideoInfoFetcher.ValueObjects.Showname import Showname
from NNMM.VideoInfoFetcher.ValueObjects.Title import Title
from NNMM.VideoInfoFetcher.ValueObjects.TitleList import TitleList
from NNMM.VideoInfoFetcher.ValueObjects.UploadedURL import UploadedURL
from NNMM.VideoInfoFetcher.ValueObjects.Userid import Userid
from NNMM.VideoInfoFetcher.ValueObjects.Username import Username
from NNMM.VideoInfoFetcher.ValueObjects.VideoidList import VideoidList
from NNMM.VideoInfoFetcher.ValueObjects.VideoURL import VideoURL
from NNMM.VideoInfoFetcher.ValueObjects.VideoURLList import VideoURLList


@dataclass
class RSSParser():
    mylist_url: UploadedURL | MylistURL
    soup: BeautifulSoup

    # 日付フォーマット
    SOURCE_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, url: str, soup: BeautifulSoup):
        if UploadedURL.is_valid(url):
            self.mylist_url = UploadedURL.create(url)
        elif MylistURL.is_valid(url):
            self.mylist_url = MylistURL.create(url)
        self.soup = soup

    def _get_iteminfo(self, item_lx: Tag) -> ItemInfo:
        """一つのentryから動画ID, 動画タイトル, 投稿日時, 動画URLを抽出する

        Notes:
            投稿日時は "%Y-%m-%d %H:%M:%S" のフォーマットで返す
            抽出結果のチェックはしない

        Args:
            item_lx (bs4.element.Tag): soup.find_allで取得されたitemタグ

        Returns:
            ItemInfo: 動画ID, 動画タイトル, 登録日時, 動画URL

        Raises:
            AttributeError, TypeError: エントリパース失敗時
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """
        RP = RSSParser

        title = Title(item_lx.find("title").text)

        link_lx = item_lx.find("link")
        video_url = VideoURL.create(link_lx.text)

        pubDate_lx = item_lx.find("pubDate")
        dst = datetime.strptime(pubDate_lx.text, RP.SOURCE_DATETIME_FORMAT)
        registered_at = RegisteredAt(dst.strftime(RP.DESTINATION_DATETIME_FORMAT))

        return ItemInfo(title, registered_at, video_url)

    def _get_mylist_url(self) -> UploadedURL | MylistURL:
        """マイリストURL
        """
        return self.mylist_url

    def _get_userid_mylistid(self) -> tuple[Userid, Mylistid]:
        """ユーザーID, マイリストID設定
        """
        userid = self.mylist_url.userid
        mylistid = self.mylist_url.mylistid
        return (userid, mylistid)

    def _get_username(self) -> Username:
        """投稿者収集
        """
        if isinstance(self.mylist_url, UploadedURL):
            # タイトルからユーザー名を取得
            title_lx = self.soup.find_all("title")
            pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
            username = re.findall(pattern, title_lx[0].text)[0]
        elif isinstance(self.mylist_url, MylistURL):
            creator_lx = self.soup.find_all("dc:creator")
            username = creator_lx[0].text
        return Username(username)

    def _get_showname_myshowname(self) -> tuple[Showname, Myshowname]:
        """マイリスト名収集
        """
        username = self._get_username()
        if isinstance(self.mylist_url, UploadedURL):
            myshowname = Myshowname("投稿動画")
            showname = Showname.create(username, None)
            return (showname, myshowname)
        elif isinstance(self.mylist_url, MylistURL):
            # マイリストの場合はタイトルから取得
            title_lx = self.soup.find_all("title")
            pattern = "^マイリスト (.*)‐ニコニコ動画$"
            page_title = title_lx[0].text
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
        video_id_list = []
        title_list = []
        registered_at_list = []
        video_url_list = []
        items_lx = self.soup.find_all("item")
        for item in items_lx:
            # 動画エントリパース
            iteminfo = self._get_iteminfo(item)
            video_id = iteminfo.video_id
            title = iteminfo.title
            registered_at = iteminfo.registered_at
            video_url = iteminfo.video_url

            # 格納
            video_id_list.append(video_id)
            title_list.append(title)
            registered_at_list.append(registered_at)
            video_url_list.append(video_url)

        # ValueObjectに変換
        video_id_list = VideoidList.create(video_id_list)
        title_list = TitleList.create(title_list)
        registered_at_list = RegisteredAtList.create(registered_at_list)
        video_url_list = VideoURLList.create(video_url_list)

        # 返り値設定
        num = len(title_list)
        res = {
            "no": list(range(1, num + 1)),              # No. [1, ..., len()-1]
            "userid": userid,                           # ユーザーID 1234567
            "mylistid": mylistid,                       # マイリストID 12345678
            "showname": showname,                       # マイリスト表示名 「投稿者1さんの投稿動画」
            "myshowname": myshowname,                   # マイリスト名 「投稿動画」
            "mylist_url": mylist_url,                   # マイリストURL https://www.nicovideo.jp/user/11111111/video
            "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        }
        return FetchedPageVideoInfo(**res)


if __name__ == "__main__":
    from NNMM.VideoInfoFetcher.VideoInfoRssFetcher import VideoInfoRssFetcher
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
        soup = BeautifulSoup(response.text, "lxml-xml")

        rp = RSSParser(url, soup)
        soup_d = loop.run_until_complete(rp.parse())

        pprint.pprint(soup_d.to_dict())
    pass
