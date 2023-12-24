from dataclasses import dataclass
from typing import Iterator, Self

from NNMM.process.update_mylist.value_objects.typed_video import TypedVideo


@dataclass(frozen=True)
class TypedVideoList:
    _list: list[TypedVideo]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise ValueError("_list must be list.")
        if not all([isinstance(m, TypedVideo) for m in self._list]):
            raise ValueError("_list element must be TypedVideo.")

    def __iter__(self) -> Iterator[TypedVideo]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> TypedVideo:
        return self._list.__getitem__(item)

    def __setitem__(self, index, value) -> None:
        return self._list.__setitem__(index, value)

    @classmethod
    def create(cls, typed_video_list: list[TypedVideo]) -> Self:
        return cls(typed_video_list)


if __name__ == "__main__":
    pass
