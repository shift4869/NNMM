# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.VideoURL import VideoURL
from NNMM.VideoInfoFetcher.VideoidList import VideoidList


@dataclass(frozen=True)
class VideoURLList(Iterable):
    _list: list[VideoURL]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid VideoURLList.")
        if not any([isinstance(r, VideoURL) for r in self._list]):
            raise ValueError(f"include not VideoURL element, invalid VideoURLList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @property
    def video_id_list(self) -> list[str]:
        return [v.video_id for v in self._list]

    @classmethod
    def create(cls, video_url_list: list[str]) -> "VideoURLList":
        return cls([VideoURL.create(r) for r in video_url_list])


if __name__ == "__main__":
    NUM = 5
    base_url = "https://www.nicovideo.jp/watch/sm1000000{}"
    urls = [base_url.format(i) for i in range(1, NUM + 1)]

    video_url_list = VideoURLList.create(urls)
    for v in video_url_list:
        print(v)
    for vid in video_url_list.video_id_list:
        print(vid)
