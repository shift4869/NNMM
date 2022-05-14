# coding: utf-8
from dataclasses import dataclass
import re

from NNMM.VideoInfoFetcher.Mylistid import Mylistid
from NNMM.VideoInfoFetcher.URL import URL
from NNMM.VideoInfoFetcher.Userid import Userid


@dataclass
class UploadedURL():
    url: URL

    # 対象URLのパターン
    UPLOADED_URL_PATTERN = "^https://www.nicovideo.jp/user/([0-9]+)/video$"

    # RSSリクエストURLサフィックス
    RSS_URL_SUFFIX = "?rss=2.0"

    def __post_init__(self) -> None:
        non_query_url = self.url.non_query_url
        if not self.is_valid(non_query_url):
            raise ValueError("URL is not Uploaded URL.")

    @property
    def non_query_url(self) -> str:
        return self.url.non_query_url

    @property
    def original_url(self) -> str:
        return self.url.original_url

    @property
    def fetch_url(self) -> str:
        fetch_url = self.url.non_query_url + self.RSS_URL_SUFFIX
        return fetch_url

    @property
    def mylist_url(self) -> str:
        return self.url.non_query_url

    @property
    def userid(self) -> Userid:
        mylist_url = self.mylist_url
        userid = re.findall(UploadedURL.UPLOADED_URL_PATTERN, mylist_url)[0]
        return Userid(userid)

    @property
    def mylistid(self) -> Mylistid:
        return Mylistid("")  # 投稿動画の場合、マイリストIDは空文字列

    @classmethod
    def create(cls, url: str) -> "UploadedURL":
        return cls(URL(url))

    @classmethod
    def is_valid(cls, url: str) -> bool:
        non_query_url = URL(url).non_query_url
        return re.search(UploadedURL.UPLOADED_URL_PATTERN, non_query_url) is not None


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",  # 投稿動画(クエリつき)
        "https://不正なURLアドレス/user/6063658/mylist/72036443",  # 不正なURLアドレス
    ]

    for url in urls:
        if UploadedURL.is_valid(url):
            u = UploadedURL.create(url)
            print(u.non_query_url)
            print(u.original_url)
        else:
            print("Not Target URL : " + url)
