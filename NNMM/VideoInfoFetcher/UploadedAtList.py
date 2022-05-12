# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.UploadedAt import UploadedAt


@dataclass
class UploadedAtList(Iterable):
    _list: list[UploadedAt]

    DESTINATION_DATETIME_FORMAT = UploadedAt.DESTINATION_DATETIME_FORMAT

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid UploadedAtList.")
        if not any([isinstance(r, UploadedAt) for r in self._list]):
            raise ValueError(f"include not UploadedAt element, invalid UploadedAtList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @classmethod
    def create(cls, uploaded_at_list: list[str]) -> "UploadedAtList":
        return cls([UploadedAt(r) for r in uploaded_at_list])


if __name__ == "__main__":
    NUM = 5
    base_url = "2022-05-12 00:01:0{}"
    urls = [base_url.format(i) for i in range(1, NUM + 1)]

    uploaded_at_list = UploadedAtList.create(urls)
    for dt_str in uploaded_at_list:
        print(dt_str)
