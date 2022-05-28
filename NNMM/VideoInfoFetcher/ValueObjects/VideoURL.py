# coding: utf-8
import re
from dataclasses import dataclass

from NNMM.VideoInfoFetcher.ValueObjects.URL import URL
from NNMM.VideoInfoFetcher.ValueObjects.Videoid import Videoid


@dataclass(frozen=True)
class VideoURL():
    """動画URL

    動画URLはVIDEO_URL_PATTERN に合致するURLを扱う
    動画再生ページが開けるURLを表す

    Raises:
        ValueError: 引数が動画URLのパターンでなかった場合

    Returns:
        VideoURL: 動画URL
    """
    url: URL

    # 対象URLのパターン
    VIDEO_URL_PATTERN = r"^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
    VIDEO_ID_PATTERN = r"sm[0-9]"

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        non_query_url = self.url.non_query_url
        if not self.is_valid(non_query_url):
            raise ValueError("URL is not Video URL.")

    @property
    def non_query_url(self) -> str:
        """クエリなしURLを返す
        """
        return self.url.non_query_url

    @property
    def original_url(self) -> str:
        """元のURLを返す
        """
        return self.url.original_url

    @property
    def fetch_url(self) -> str:
        """RSS取得用のURLを返す

        動画URLでは特にfetch用URLに加工しない
        """
        return self.url.non_query_url

    @property
    def video_url(self) -> str:
        """動画URLを返す

        クエリなしURLと同じ
        """
        return self.url.non_query_url

    @property
    def video_id(self) -> Videoid:
        """動画IDを返す

        クエリなしURLから切り出してVideoidを生成する
        """
        video_url = self.url.non_query_url
        video_id = re.findall(VideoURL.VIDEO_URL_PATTERN, video_url)[0]
        return Videoid(video_id)

    @classmethod
    def create(cls, url: str | URL) -> "VideoURL":
        """VideoURL インスタンスを作成する

        URL インスタンスを作成して
        それをもとにしてVideoURL インスタンス作成する

        Args:
            url (str | URL): 対象URLを表す文字列 or URL

        Returns:
            VideoURL: VideoURL インスタンス
        """
        return cls(URL(url))

    @classmethod
    def is_valid(cls, url: str | URL) -> bool | ValueError:
        """動画URLのパターンかどうかを返す

        このメソッドがTrueならばVideoURL インスタンスが作成できる
        また、このメソッドがTrueならば引数のurl がVideoURL の形式であることが判別できる
        (v.v.)

        Args:
            url (str | URL): チェック対象のURLを表す文字列 or URL

        Returns:
            bool: 引数がVideoURL.VIDEO_URL_PATTERN パターンに則っているならばTrue,
                  そうでないならFalse

        Raises:
            ValueError: URLインスタンスとして不正な場合
        """
        # video_url の形として正しいか
        non_query_url = URL(url).non_query_url
        if re.search(VideoURL.VIDEO_URL_PATTERN, non_query_url) is None:
            return False

        # video_url の末尾に正しい形式のvideo_id があるか
        video_url = non_query_url
        path_tail = re.findall(VideoURL.VIDEO_URL_PATTERN, video_url)[0]
        if re.search(VideoURL.VIDEO_ID_PATTERN, path_tail) is None:
            return False
        return True


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/watch/sm12345678",  # 動画URL
        "https://不正なURLアドレス/watch/sm12345678",  # 不正なURLアドレス
    ]

    for url in urls:
        if VideoURL.is_valid(url):
            u = VideoURL.create(url)
            print(u.non_query_url)
            print(u.video_id)
        else:
            print("Not Target URL : " + url)
