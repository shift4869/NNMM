# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.Title import Title


@dataclass
class TitleList(Iterable):
    _list: list[Title]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid TitleList.")
        if not any([isinstance(r, Title) for r in self._list]):
            raise ValueError(f"include not Title element, invalid TitleList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @classmethod
    def create(cls, title_list: list[str]) -> "TitleList":
        return cls([Title(r) for r in title_list])


if __name__ == "__main__":
    NUM = 5
    base_url = "動画タイトル{}"
    titles = [base_url.format(i) for i in range(1, NUM + 1)]

    title_list = TitleList.create(titles)
    for t in title_list:
        print(t)
