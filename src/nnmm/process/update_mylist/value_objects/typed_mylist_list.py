from dataclasses import dataclass
from typing import Iterator, Self

from nnmm.process.update_mylist.value_objects.typed_mylist import TypedMylist


@dataclass(frozen=True)
class TypedMylistList:
    _list: list[TypedMylist]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise ValueError("_list must be list.")
        if not all([isinstance(m, TypedMylist) for m in self._list]):
            raise ValueError("_list element must be TypedMylist.")

    def __iter__(self) -> Iterator[TypedMylist]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> TypedMylist:
        return self._list.__getitem__(item)

    @classmethod
    def create(cls, typed_mylist_list: list[TypedMylist]) -> Self:
        return cls(typed_mylist_list)


if __name__ == "__main__":
    pass
