# coding: utf-8
from dataclasses import dataclass
import re

from NNMM.VideoInfoFetcher.URL import URL


@dataclass
class VideoURL():
    url: URL

    # 対象URLのパターン
    VIDEO_URL_PATTERN = r"^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
    VIDEO_ID_PATTERN = r"sm[0-9]"

    # RSSリクエストURLサフィックス
    RSS_URL_SUFFIX = "?rss=2.0"

    def __post_init__(self) -> None:
        non_query_url = self.url.non_query_url
        if not self.is_valid(non_query_url):
            raise ValueError("URL is not Video URL.")

    @property
    def non_query_url(self):
        return self.url.non_query_url

    @property
    def original_url(self):
        return self.url.original_url

    @property
    def fetch_url(self):
        # 動画URLでは特にfetch用URLに加工しない
        return self.url.non_query_url

    @property
    def video_url(self):
        return self.url.non_query_url

    @property
    def video_id(self):
        video_url = self.url.non_query_url
        video_id = re.findall(VideoURL.VIDEO_URL_PATTERN, video_url)[0]
        return video_id

    @classmethod
    def factory(cls, url: str) -> "VideoURL":
        return cls(URL(url))

    @classmethod
    def is_valid(cls, url: str) -> bool:
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
            u = VideoURL.factory(url)
            print(u.non_query_url)
            print(u.video_id)
        else:
            print("Not Target URL : " + url)