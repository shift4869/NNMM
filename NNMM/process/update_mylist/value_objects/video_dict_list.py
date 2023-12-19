from dataclasses import dataclass
from typing import Any, Iterator, Self

from NNMM.model import MylistInfo
from NNMM.process.update_mylist.value_objects.video_dict import VideoDict
from NNMM.process.update_mylist.value_objects.typed_video_list import TypedVideoList


@dataclass(frozen=True)
class VideoDictList():
    _list: list[VideoDict]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise ValueError("_list must be list.")
        if not all([isinstance(m, VideoDict) for m in self._list]):
            raise ValueError("_list element must be VideoDict.")

    def __iter__(self) -> Iterator[VideoDict]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> VideoDict:
        return self._list.__getitem__(item)

    def to_typed_video_list(self) -> TypedVideoList:
        return TypedVideoList.create([
            video_dict.to_typed_video() for video_dict in self._list
        ])

    @classmethod
    def create(cls, video_dict_list: list[dict]) -> Self:
        return cls([
            VideoDict.create(video_dict) for video_dict in video_dict_list
        ])


if __name__ == "__main__":
    pass
