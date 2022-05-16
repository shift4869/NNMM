# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.ValueObjects.RegisteredAt import RegisteredAt


@dataclass(frozen=True)
class RegisteredAtList(Iterable):
    _list: list[RegisteredAt]

    DESTINATION_DATETIME_FORMAT = RegisteredAt.DESTINATION_DATETIME_FORMAT

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid RegisteredAtList.")
        if self._list:
            if not all([isinstance(r, RegisteredAt) for r in self._list]):
                raise ValueError(f"include not RegisteredAt element, invalid RegisteredAtList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @classmethod
    def create(cls, registered_at_list: list[RegisteredAt] | list[str]) -> "RegisteredAtList":
        if not isinstance(registered_at_list, list):
            raise TypeError("Args is not list.")
        if not registered_at_list:
            return cls([])
        if isinstance(registered_at_list[0], RegisteredAt):
            return cls(registered_at_list)
        if isinstance(registered_at_list[0], str):
            return cls([RegisteredAt(r) for r in registered_at_list])
        raise ValueError("Create RegisteredAtList failed.")


if __name__ == "__main__":
    NUM = 5
    base_dt_str = "2022-05-12 00:01:0{}"
    registered_ats = [base_dt_str.format(i) for i in range(1, NUM + 1)]

    registered_at_list = RegisteredAtList.create(registered_ats)
    for dt_str in registered_at_list:
        print(dt_str)
