# coding: utf-8
from dataclasses import dataclass

from NNMM.VideoInfoFetcher.URL import *


@dataclass
class FetchURL():
    original_url: str  # もとのURL（クエリがあるかもしれない）
    url: URL  # もとのURL（URLオブジェクト、クエリなし）
    type: URLType  # もとのURLのタイプ
    request_url: str  # リクエスト用のURL（クエリがあるかもしれない）

    def __init__(self, url: str) -> None:
        self.original_url = str(url)
        self.url = URL(url)
        self.type = self.url.type
        self.request_url = self._get_request_url()

    def _get_request_url(self) -> str:
        if self.type == URLType.MYLIST:
            # "https://www.nicovideo.jp/mylist/[0-9]+/?rss=2.0" 形式でないとそのマイリストのRSSが取得できない
            request_url = re.sub("/user/[0-9]+", "", str(self.original_url))  # /user/{userid} 部分を削除
            return request_url
        return str(self.original_url)


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",  # 投稿動画(クエリつき)
        "https://www.nicovideo.jp/user/6063658/mylist/72036443?ref=pc_mypage_nicorepo",  # テスト用マイリスト(クエリつき)
        "https://不正なURLアドレス/user/6063658/mylist/72036443",  # 不正なURLアドレス
    ]

    try:
        for url in urls:
            f = FetchURL(url)
            print("original_url : " + f.original_url)
            print("url          : " + str(f.url))
            print("request_url  : " + f.request_url)
            print("")
    except ValueError:
        print("Not Target URL : " + str(url))
        pass
