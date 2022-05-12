# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.Videoid import Videoid


@dataclass(frozen=True)
class VideoidList(Iterable):
    _list: list[Videoid]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid VideoidList.")
        if not any([isinstance(r, Videoid) for r in self._list]):
            raise ValueError(f"include not Videoid element, invalid VideoidList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @classmethod
    def create(cls, video_id_list: list[str]) -> "VideoidList":
        return cls([Videoid(r) for r in video_id_list])


if __name__ == "__main__":
    NUM = 5
    base = "sm1000000{}"
    urls = [base.format(i) for i in range(1, NUM + 1)]

    video_id_list = VideoidList.create(urls)
    for v in video_id_list:
        print(v)
