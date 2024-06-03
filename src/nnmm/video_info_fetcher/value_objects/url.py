import re
import urllib.parse
from dataclasses import dataclass
from typing import ClassVar, Self


@dataclass(frozen=True)
class URL:
    """URL

    URL を表す文字列を受け取る
    引数がURL_PATTERN と一致する場合にURL として受け入れる
    日本語含みのURLは対象外とする

    Raises:
        ValueError: 引数がURL_PATTERN と一致しない文字列の場合

    Returns:
        URL: URLを表すValueObject
    """

    original_url: str  # もとのURL
    non_query_url: ClassVar[str]  # クエリなしURL

    URL_PATTERN = r"^https?://[a-zA-Z0-9_/:%#$&\?\(\)~\.=\+\-]+"

    def __init__(self, url: str | Self) -> None:
        """初期化処理

        Args:
            url (str | URL): 対象となるURL文字列（候補）
        """
        # 引数の型を str に合わせる
        if isinstance(url, URL):
            url: str = url.original_url

        # 先頭が大文字のHから始まっていたら小文字にする
        if url.startswith("H"):
            url: str = "h" + url[1:]

        # h抜きなら補完する
        if url.startswith("t"):
            url: str = "h" + url

        if not self.is_valid(url):
            raise ValueError("args is not URL string.")

        # クエリ除去
        non_query_url = urllib.parse.urlunparse(urllib.parse.urlparse(str(url))._replace(query=None, fragment=None))
        object.__setattr__(self, "non_query_url", non_query_url)
        object.__setattr__(self, "original_url", url)

    @classmethod
    def is_valid(self, estimated_url: str) -> bool:
        """URLのパターンかどうかを返す

        このメソッドがTrueならばURL インスタンスが作成できる
        また、このメソッドがTrueならば引数のestimated_url が真にURL の形式であることが判別できる
        (v.v.)

        Args:
            estimated_url (str): チェック対象の候補URLを表す文字列

        Returns:
            bool: 引数がURL.URL_PATTERN パターンに則っているならばTrue,
                  そうでないならFalse
        """
        return re.search(URL.URL_PATTERN, estimated_url) is not None


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
            print(u.non_query_url)
            print(u.original_url)
    except ValueError as e:
        print(e)
