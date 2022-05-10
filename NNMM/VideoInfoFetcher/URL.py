# coding: utf-8
from dataclasses import dataclass
from typing import ClassVar
import urllib.parse


@dataclass
class URL():
    non_query_url: str
    original_url: ClassVar[str]

    def __init__(self, url: "str | URL") -> None:
        if isinstance(url, URL):
            url = url.url

        if not self.is_valid(url):
            raise ValueError("args is not URL string.")

        # クエリ除去
        non_query_url = urllib.parse.urlunparse(
            urllib.parse.urlparse(str(url))._replace(query=None)
        )
        self.non_query_url = non_query_url
        self.original_url = url

    @classmethod
    def is_valid(self, estimated_url: str):
        p = urllib.parse.urlparse(estimated_url)
        return len(p.scheme) > 0


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",  # 投稿動画(クエリつき)
        "https://不正なURLアドレス/user/6063658/mylist/72036443",  # 不正なURLアドレス
    ]

    for url in urls:
        u = URL(url)
        print(u)
        print(u.original_url)
