from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Self

from nnmm.util import MylistType
from nnmm.video_info_fetcher.value_objects.mylistid import Mylistid
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.userid import Userid


@dataclass(frozen=True)
class MylistURL(URL, ABC):
    """マイリストURLベース

    マイリストURLを表す基幹クラス
    このクラスは直接インスタンス化されない
    マイリストURLは以下の種類に細分化される
        ・投稿動画を表すURL
        ・ユーザーマイリストを表すURL
        ・シリーズを表すを表すURL

    Raises:
        ValueError: 引数がマイリストURLのパターンでなかった場合

    Returns:
        MylistURL: マイリストURL
    """

    original_url: str
    non_query_url: ClassVar[str]
    mylist_type: ClassVar[MylistType]

    def __init__(self, url: str | Self) -> None:
        super().__init__(url)
        object.__setattr__(self, "mylist_type", MylistType.none)

    @property
    @abstractmethod
    def fetch_url(self) -> str:
        """RSS取得用のURLを返す

        実際にfetchできるページアドレスの形式で返す
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def userid(self) -> Userid:
        """ユーザーIDを返す"""
        raise NotImplementedError

    @property
    @abstractmethod
    def mylistid(self) -> Mylistid:
        """マイリストIDを返す"""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def is_valid_mylist_url(cls, url: str | URL) -> bool:
        """マイリストURLの形式として正しいかを返す"""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def create(cls, url: str | URL) -> Self:
        raise NotImplementedError


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
