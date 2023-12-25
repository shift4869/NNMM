import re
from dataclasses import dataclass
from typing import ClassVar, Self

from NNMM.util import MylistType
from NNMM.video_info_fetcher.value_objects.mylist_url import MylistURL
from NNMM.video_info_fetcher.value_objects.mylistid import Mylistid
from NNMM.video_info_fetcher.value_objects.url import URL
from NNMM.video_info_fetcher.value_objects.userid import Userid


@dataclass(frozen=True)
class UserMylistURL(MylistURL):
    """マイリストURL

    マイリストURLは USER_MYLIST_URL_PATTERN に合致するURLを扱う
    （投稿動画でなく）作成されたマイリストのURLを表す

    Raises:
        ValueError: 引数がマイリストURLのパターンでなかった場合

    Returns:
        UserMylistURL: マイリストURL
    """

    original_url: str
    non_query_url: ClassVar[str]

    # 対象URLのパターン
    USER_MYLIST_URL_PATTERN = "^https://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)$"

    # RSSリクエストURLサフィックス
    RSS_URL_SUFFIX = "?rss=2.0"

    def __init__(self, url: str | Self) -> None:
        super().__init__(url)
        non_query_url = self.non_query_url
        if not self.is_valid_mylist_url(non_query_url):
            raise ValueError("URL is not UserMylist URL.")
        object.__setattr__(self, "mylist_type", MylistType.mylist)

    @property
    def fetch_url(self) -> str:
        """RSS取得用のURLを返す

        https://www.nicovideo.jp/mylist/[0-9]+/?rss=2.0 形式でないとそのマイリストのRSSが取得できない
        """
        # /user/{userid} 部分を削除
        non_user_url = re.sub("/user/[0-9]+", "", str(self.non_query_url))
        # サフィックスを付与
        fetch_url = non_user_url + self.RSS_URL_SUFFIX
        return fetch_url

    @property
    def userid(self) -> Userid:
        """ユーザーIDを返す

        クエリなしURLからユーザーID部分を切り出す
        """
        mylist_url = self.non_query_url
        userid, mylistid = re.findall(UserMylistURL.USER_MYLIST_URL_PATTERN, mylist_url)[0]
        return Userid(userid)

    @property
    def mylistid(self) -> Mylistid:
        """マイリストIDを返す

        クエリなしURLからマイリストID部分を切り出す
        """
        mylist_url = self.non_query_url
        userid, mylistid = re.findall(UserMylistURL.USER_MYLIST_URL_PATTERN, mylist_url)[0]
        return Mylistid(mylistid)

    @classmethod
    def is_valid_mylist_url(cls, url: str | URL) -> bool:
        """マイリストURLのパターンかどうかを返す

        このメソッドがTrueならばMylistURL インスタンスが作成できる
        また、このメソッドがTrueならば引数のurl がMylistURL の形式であることが判別できる
        (v.v.)

        Args:
            url (str | URL): チェック対象のURLを表す文字列 or URL

        Returns:
            bool: 引数がMylistURL.USER_MYLIST_URL_PATTERN パターンに則っているならばTrue,
                  そうでないならFalse
        """
        try:
            non_query_url = URL(url).non_query_url
            return re.search(UserMylistURL.USER_MYLIST_URL_PATTERN, non_query_url) is not None
        except Exception:
            return False

    @classmethod
    def create(cls, url: str | URL) -> Self:
        """UserMylistURL インスタンスを作成する

        URL インスタンスを作成して
        それをもとにしてMylistURL インスタンス作成する

        Args:
            url (str | URL): 対象URLを表す文字列 or URL

        Returns:
            UserMylistURL: UserMylistURL インスタンス
        """
        return cls(URL(url))


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",
        "https://www.nicovideo.jp/user/6063658/mylist/72036443?ref=pc_mypage_nicorepo",
        "https://不正なURLアドレス/user/6063658/mylist/72036443",
    ]

    for url in urls:
        if UserMylistURL.is_valid_mylist_url(url):
            u = UserMylistURL.create(url)
            print(u.non_query_url)
            print(u.fetch_url)
        else:
            print("Not Target URL : " + url)
