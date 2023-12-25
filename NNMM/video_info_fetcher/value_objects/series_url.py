import random
import re
from dataclasses import dataclass
from typing import ClassVar, Self
from urllib.parse import urlencode, urlparse, urlunparse

from NNMM.util import MylistType
from NNMM.video_info_fetcher.value_objects.mylist_url import MylistURL
from NNMM.video_info_fetcher.value_objects.mylistid import Mylistid
from NNMM.video_info_fetcher.value_objects.url import URL
from NNMM.video_info_fetcher.value_objects.userid import Userid


@dataclass(frozen=True)
class SeriesURL(MylistURL):
    """シリーズURL

    シリーズURLは SERIES_URL_PATTERN に合致するURLを扱う

    Raises:
        ValueError: 引数がシリーズURLのパターンでなかった場合

    Returns:
        SeriesURL: シリーズURL
    """

    original_url: str
    non_query_url: ClassVar[str]

    # 対象URLのパターン
    SERIES_URL_PATTERN = r"^https://www.nicovideo.jp/user/([0-9]+)/series/([0-9]+)$"
    # シリーズ取得APIのベースURL
    SERIES_API_BASE_URL = "https://nvapi.nicovideo.jp/v1/series/"

    def __init__(self, url: str | Self) -> None:
        super().__init__(url)
        non_query_url = self.non_query_url
        if not self.is_valid_mylist_url(non_query_url):
            raise ValueError("URL is not Series URL.")
        object.__setattr__(self, "mylist_type", MylistType.series)

    @property
    def fetch_url(self) -> str:
        """RSS取得用のURLを返す"""
        return self._get_fetch_url()

    @property
    def userid(self) -> Userid:
        """ユーザーIDを返す

        クエリなしURLからユーザーID部分を切り出す
        """
        non_query_url = self.non_query_url
        userid, seriesid = re.findall(SeriesURL.SERIES_URL_PATTERN, non_query_url)[0]
        return Userid(userid)

    @property
    def mylistid(self) -> Mylistid:
        """マイリストIDを返す

        クエリなしURLからシリーズID部分をマイリストIDとして切り出す
        """
        non_query_url = self.non_query_url
        userid, seriesid = re.findall(SeriesURL.SERIES_URL_PATTERN, non_query_url)[0]
        return Mylistid(seriesid)

    def _make_action_track_id(self) -> str:
        """actionTrackId を作成する

        actionTrackIdについて
            10桁のアルファベット小文字大文字数字と、
            24桁の数字をアンダースコアで接続する

        Returns:
            str: actionTrackId
        """
        first_charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        last_charset = "0123456789"
        first_str = "".join(random.choices(first_charset, k=10))
        last_str = "".join(random.choices(last_charset, k=24))
        return f"{first_str}_{last_str}"

    def _get_fetch_url(self) -> str:
        """RSS取得用のURLを返す

        シリーズページを取得する方法：参考
        https://github.com/castella-cake/niconico-peppermint-extension/blob/fd09ba26287f703c83d815e21c6775d3fe76b244/src/js/background.js#L83

        シリーズ取得のAPI
        https://nvapi.nicovideo.jp/v1/series/{series_id}?_frontendId=6&_frontendVersion=0&actionTrackId={action_track_id}
        """
        mylistid = self.mylistid
        base_url = self.SERIES_API_BASE_URL + mylistid.id
        action_track_id = self._make_action_track_id()
        query_params = {
            "Content-Type": "application/xml",
            "_frontendId": 6,
            "_frontendVersion": 0,
            "actionTrackId": action_track_id,
        }
        query_params = urlencode(query_params, doseq=True)
        fetch_url = urlunparse(urlparse(str(base_url))._replace(query=query_params, fragment=None))
        return fetch_url

    @classmethod
    def is_valid_mylist_url(cls, url: str | URL) -> bool:
        """シリーズURLのパターンかどうかを返す

        このメソッドがTrueならば SeriesURL インスタンスが作成できる
        また、このメソッドがTrueならば引数の url が SeriesURL の形式であることが判別できる
        (v.v.)

        Args:
            url (str | URL): チェック対象のURLを表す文字列 or URL

        Returns:
            bool: 引数が SeriesURL.SERIES_URL_PATTERN パターンに則っているならばTrue,
                  そうでないならFalse
        """
        try:
            non_query_url = URL(url).non_query_url
            return re.search(SeriesURL.SERIES_URL_PATTERN, non_query_url) is not None
        except Exception:
            return False

    @classmethod
    def create(cls, url: str | URL) -> Self:
        """SeriesURL インスタンスを作成する

        URL インスタンスを作成して
        それをもとにして SeriesURL インスタンス作成する

        Args:
            url (str | URL): 対象URLを表す文字列 or URL

        Returns:
            SeriesURL: SeriesURL インスタンス
        """
        return cls(URL(url))


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",
        "https://www.nicovideo.jp/user/12899156/series/442402?ref=pc_mypage_nicorepo",
        "https://不正なURLアドレス/user/6063658/mylist/72036443",
    ]

    for url in urls:
        if SeriesURL.is_valid_mylist_url(url):
            u = SeriesURL.create(url)
            print(u)
        else:
            print("Not Target URL : " + url)
