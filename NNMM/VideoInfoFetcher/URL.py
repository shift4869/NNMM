# coding: utf-8
from dataclasses import dataclass
import re
import urllib.parse
from enum import Enum, auto


# URLタイプ
class URLType(Enum):
    UPLOADED = "uploaded"
    MYLIST = "mylist"


@dataclass
class URL():
    url: str
    type: URLType

    # 対象URLのパターン
    UPLOADED_URL_PATTERN = "^https://www.nicovideo.jp/user/([0-9]+)/video$"
    MYLIST_URL_PATTERN = "^https://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)$"

    def __init__(self, url: "str | URL") -> None:
        if isinstance(url, URL):
            url = url.url

        # クエリ除去
        exclude_query_url = urllib.parse.urlunparse(
            urllib.parse.urlparse(str(url))._replace(query=None)
        )
        self.url = exclude_query_url

        # 対象URLか判定
        if not self._is_valid():
            # 対象URLでなければエラー
            raise ValueError("URL is not target.")

        # URLタイプを判別して設定
        self.type = self._get_type()

    def _is_valid(self) -> bool:
        VALID_URL_PATTERN = [
            URL.UPLOADED_URL_PATTERN,
            URL.MYLIST_URL_PATTERN,
        ]
        return any([re.search(p, self.url) is not None for p in VALID_URL_PATTERN])

    def _get_type(self) -> URLType:
        if re.search(URL.UPLOADED_URL_PATTERN, self.url):
            return URLType.UPLOADED

        if re.search(URL.MYLIST_URL_PATTERN, self.url):
            return URLType.MYLIST

        raise ValueError("Getting URL type failed.")

    # def __str__(self):
    #     return self._url

    # def __repr__(self):
    #     return self._url

    # @property
    # def url(self):
    #     return self._url

    # @property
    # def type(self):
    #     return self._type


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",  # 投稿動画(クエリつき)
        "https://不正なURLアドレス/user/6063658/mylist/72036443",  # 不正なURLアドレス
    ]

    try:
        for url in urls:
            u = URL(url)
            print("Target URL : " + u.url)
    except ValueError:
        print("Not Target URL : " + url)
        pass
