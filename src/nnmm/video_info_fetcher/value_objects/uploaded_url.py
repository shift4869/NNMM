import re
from dataclasses import dataclass
from typing import ClassVar, Self

from nnmm.util import MylistType
from nnmm.video_info_fetcher.value_objects.mylist_url import MylistURL
from nnmm.video_info_fetcher.value_objects.mylistid import Mylistid
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.userid import Userid


@dataclass(frozen=True)
class UploadedURL(MylistURL):
    """投稿ページURL

    投稿ページURLはUPLOADED_URL_PATTERN に合致するURLを扱う

    Raises:
        ValueError: 引数が投稿ページURLのパターンでなかった場合

    Returns:
        UploadedURL: 投稿ページURL
    """

    original_url: str
    non_query_url: ClassVar[str]

    # 対象URLのパターン
    UPLOADED_URL_PATTERN = "^https://www.nicovideo.jp/user/([0-9]+)/video$"

    # RSSリクエストURLサフィックス
    RSS_URL_SUFFIX = "?rss=2.0"

    def __init__(self, url: str | Self) -> None:
        super().__init__(url)
        non_query_url = self.non_query_url
        if not self.is_valid_mylist_url(non_query_url):
            raise ValueError("URL is not Uploaded URL.")
        object.__setattr__(self, "mylist_type", MylistType.uploaded)

    @property
    def fetch_url(self) -> str:
        """RSS取得用のURLを返す"""
        fetch_url = self.non_query_url + self.RSS_URL_SUFFIX
        return fetch_url

    @property
    def userid(self) -> Userid:
        """ユーザーIDを返す

        クエリなしURLからユーザーID部分を切り出す
        """
        non_query_url = self.non_query_url
        userid = re.findall(UploadedURL.UPLOADED_URL_PATTERN, non_query_url)[0]
        return Userid(userid)

    @property
    def mylistid(self) -> Mylistid:
        """マイリストIDを返す

        投稿動画の場合、マイリストIDは空文字列
        """
        return Mylistid("")

    @classmethod
    def is_valid_mylist_url(cls, url: str | URL) -> bool:
        """投稿ページURLのパターンかどうかを返す

        このメソッドがTrueならばUploadedURL インスタンスが作成できる
        また、このメソッドがTrueならば引数のurl がUploadedURL の形式であることが判別できる
        (v.v.)

        Args:
            url (str | URL): チェック対象のURLを表す文字列 or URL

        Returns:
            bool: 引数がUploadedURL.UPLOADED_URL_PATTERN パターンに則っているならばTrue,
                  そうでないならFalse
        """
        try:
            non_query_url = URL(url).non_query_url
            return re.search(UploadedURL.UPLOADED_URL_PATTERN, non_query_url) is not None
        except Exception:
            return False

    @classmethod
    def create(cls, url: str | URL) -> Self:
        """UploadedURL インスタンスを作成する

        URL インスタンスを作成して
        それをもとにして UploadedURL インスタンス作成する

        Args:
            url (str | URL): 対象URLを表す文字列 or URL

        Returns:
            UploadedURL: UploadedURL インスタンス
        """
        return cls(URL(url))


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",  # 投稿動画(クエリつき)
        "https://不正なURLアドレス/user/6063658/mylist/72036443",  # 不正なURLアドレス
    ]

    for url in urls:
        if UploadedURL.is_valid_mylist_url(url):
            u = UploadedURL.create(url)
            print(u.non_query_url)
            print(u.original_url)
        else:
            print("Not Target URL : " + url)
