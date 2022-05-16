# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.ValueObjects.Title import Title


@dataclass(frozen=True)
class TitleList(Iterable):
    _list: list[Title]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid TitleList.")
        if self._list:
            if not all([isinstance(r, Title) for r in self._list]):
                raise ValueError(f"include not Title element, invalid TitleList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @classmethod
    def create(cls, title_list: list[Title] | list[str]) -> "TitleList":
        if not isinstance(title_list, list):
            raise TypeError("Args is not list.")
        if not title_list:
            return cls([])
        if isinstance(title_list[0], Title):
            return cls(title_list)
        if isinstance(title_list[0], str):
            return cls([Title(r) for r in title_list])
        raise ValueError("Create TitleList failed.")


if __name__ == "__main__":
    NUM = 5
    base_title = "動画タイトル{}"
    titles = [base_title.format(i) for i in range(1, NUM + 1)]

    title_list = TitleList.create([])
    title_list = TitleList.create(titles)
    for t in title_list:
        print(t)
