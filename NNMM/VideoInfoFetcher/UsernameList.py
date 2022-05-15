# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.Username import Username


@dataclass(frozen=True)
class UsernameList(Iterable):
    _list: list[Username]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid UsernameList.")
        if self._list:
            if not all([isinstance(r, Username) for r in self._list]):
                raise ValueError(f"include not Username element, invalid UsernameList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @classmethod
    def create(cls, username_list: list[Username] | list[str]) -> "UsernameList":
        if not isinstance(username_list, list):
            raise TypeError("Args is not list.")
        if not username_list:
            return cls([])
        if isinstance(username_list[0], Username):
            return cls(username_list)
        if isinstance(username_list[0], str):
            return cls([Username(r) for r in username_list])
        raise ValueError("Create UsernameList failed.")


if __name__ == "__main__":
    NUM = 5
    base_name = "作成者{}"
    names = [base_name.format(i) for i in range(1, NUM + 1)]

    username_list = UsernameList.create(names)
    for username in username_list:
        print(username)
