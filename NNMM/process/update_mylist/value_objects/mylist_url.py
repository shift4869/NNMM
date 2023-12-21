import re
from dataclasses import dataclass

from NNMM.process.update_mylist.value_objects.mylistid import Mylistid
from NNMM.process.update_mylist.value_objects.url import URL
from NNMM.process.update_mylist.value_objects.userid import Userid


@dataclass(frozen=True)
class MylistURL:
    """マイリストURL

    マイリストURLはMYLIST_URL_PATTERN に合致するURLを扱う
    （投稿動画でなく）作成されたマイリストのURLを表す

    Raises:
        ValueError: 引数がマイリストURLのパターンでなかった場合

    Returns:
        MylistURL: マイリストURL
    """

    url: URL

    # 対象URLのパターン
    MYLIST_URL_PATTERN = "^https://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)$"

    # RSSリクエストURLサフィックス
    RSS_URL_SUFFIX = "?rss=2.0"

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        non_query_url = self.url.non_query_url
        if not self.is_valid(non_query_url):
            raise ValueError("URL is not Mylist URL.")

    @property
    def non_query_url(self) -> str:
        """クエリなしURLを返す"""
        return self.url.non_query_url

    @property
    def original_url(self) -> str:
        """元のURLを返す"""
        return self.url.original_url

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
    def mylist_url(self) -> str:
        """マイリストURLを返す

        クエリなしURLと同じ
        """
        return self.url.non_query_url

    @property
    def userid(self) -> Userid:
        """ユーザーIDを返す

        クエリなしURLからユーザーID部分を切り出す
        """
        mylist_url = self.url.non_query_url
        userid, mylistid = re.findall(MylistURL.MYLIST_URL_PATTERN, mylist_url)[0]
        return Userid(userid)

    @property
    def mylistid(self) -> Mylistid:
        """マイリストIDを返す

        クエリなしURLからマイリストID部分を切り出す
        """
        mylist_url = self.url.non_query_url
        userid, mylistid = re.findall(MylistURL.MYLIST_URL_PATTERN, mylist_url)[0]
        return Mylistid(mylistid)

    @classmethod
    def create(cls, url: str | URL) -> "MylistURL":
        """MylistURL インスタンスを作成する

        URL インスタンスを作成して
        それをもとにしてMylistURL インスタンス作成する

        Args:
            url (str | URL): 対象URLを表す文字列 or URL

        Returns:
            MylistURL: MylistURL インスタンス
        """
        return cls(URL(url))

    @classmethod
    def is_valid(cls, url: str | URL) -> bool:
        """マイリストURLのパターンかどうかを返す

        このメソッドがTrueならばMylistURL インスタンスが作成できる
        また、このメソッドがTrueならば引数のurl がMylistURL の形式であることが判別できる
        (v.v.)

        Args:
            url (str | URL): チェック対象のURLを表す文字列 or URL

        Returns:
            bool: 引数がMylistURL.MYLIST_URL_PATTERN パターンに則っているならばTrue,
                  そうでないならFalse
        """
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
