from dataclasses import dataclass
from typing import Any, Iterator, Self

from NNMM.model import Mylist
from NNMM.process.update_mylist.value_objects.mylist_dict import MylistDict
from NNMM.process.update_mylist.value_objects.typed_mylist_list import TypedMylistList


@dataclass(frozen=True)
class MylistDictList():
    _list: list[MylistDict]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise ValueError("_list must be list.")
        if not all([isinstance(m, MylistDict) for m in self._list]):
            raise ValueError("_list element must be MylistDict.")

    def __iter__(self) -> Iterator[MylistDict]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> MylistDict:
        return self._list.__getitem__(item)

    def to_typed_mylist_list(self) -> TypedMylistList:
        return TypedMylistList.create([
            mylist_dict.to_typed_mylist() for mylist_dict in self._list
        ])

    @classmethod
    def create(cls, mylist_dict_list: list[dict]) -> Self:
        return cls([
            MylistDict.create(mylist_dict) for mylist_dict in mylist_dict_list
        ])


if __name__ == "__main__":
    pass
