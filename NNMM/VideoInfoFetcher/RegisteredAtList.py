# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.RegisteredAt import RegisteredAt


@dataclass
class RegisteredAtList(Iterable):
    _list: list[RegisteredAt]

    DESTINATION_DATETIME_FORMAT = RegisteredAt.DESTINATION_DATETIME_FORMAT

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid RegisteredAtList.")
        if not any([isinstance(r, RegisteredAt) for r in self._list]):
            raise ValueError(f"include not RegisteredAt element, invalid RegisteredAtList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @classmethod
    def create(cls, registered_at_list: list[str]) -> "RegisteredAtList":
        return cls([RegisteredAt(r) for r in registered_at_list])


if __name__ == "__main__":
    NUM = 5
    base_url = "2022-05-12 00:01:0{}"
    urls = [base_url.format(i) for i in range(1, NUM + 1)]

    registered_at_list = RegisteredAtList.create(urls)
    for dt_str in registered_at_list:
        print(dt_str)
