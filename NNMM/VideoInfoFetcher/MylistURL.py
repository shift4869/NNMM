# coding: utf-8
from dataclasses import dataclass
import re

from NNMM.VideoInfoFetcher.URL import URL


@dataclass
class MylistURL():
    url: URL

    # 対象URLのパターン
    MYLIST_URL_PATTERN = "^https://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)$"

    # RSSリクエストURLサフィックス
    RSS_URL_SUFFIX = "?rss=2.0"

    def __post_init__(self) -> None:
        non_query_url = self.url.non_query_url
        if not self.is_valid(non_query_url):
            raise ValueError("URL is not Mylist URL.")

    @property
    def non_query_url(self):
        return self.url.non_query_url

    @property
    def original_url(self):
        return self.url.original_url

    @property
    def fetch_url(self):
        # "https://www.nicovideo.jp/mylist/[0-9]+/?rss=2.0" 形式でないとそのマイリストのRSSが取得できない
        non_user_url = re.sub("/user/[0-9]+", "", str(self.non_query_url))  # /user/{userid} 部分を削除
        fetch_url = non_user_url + self.RSS_URL_SUFFIX
        return fetch_url

    @property
    def mylist_url(self):
        return self.url.non_query_url

    @property
    def userid(self):
        mylist_url = self.url.non_query_url
        userid, mylistid = re.findall(MylistURL.MYLIST_URL_PATTERN, mylist_url)[0]
        return userid

    @property
    def mylistid(self):
        mylist_url = self.url.non_query_url
        userid, mylistid = re.findall(MylistURL.MYLIST_URL_PATTERN, mylist_url)[0]
        return mylistid

    @classmethod
    def create(cls, url: str) -> "MylistURL":
        return cls(URL(url))

    @classmethod
    def is_valid(cls, url: str) -> bool:
        non_query_url = URL(url).non_query_url
        return re.search(MylistURL.MYLIST_URL_PATTERN, non_query_url) is not None


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",  # 投稿動画(クエリつき)
        "https://不正なURLアドレス/user/6063658/mylist/72036443",  # 不正なURLアドレス
    ]

    for url in urls:
        if MylistURL.is_valid(url):
            u = MylistURL.create(url)
            print(u.non_query_url)
            print(u.fetch_url)
        else:
            print("Not Target URL : " + url)
