from dataclasses import dataclass
from typing import Any, Iterator, Self

from NNMM.model import Mylist
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.value_objects.mylist_dict_list import MylistDictList
from NNMM.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from NNMM.process.update_mylist.value_objects.payload import Payload
from NNMM.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from NNMM.process.update_mylist.value_objects.typed_mylist import TypedMylist
from NNMM.process.update_mylist.value_objects.typed_mylist_list import TypedMylistList
from NNMM.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from NNMM.util import Result
from NNMM.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


@dataclass(frozen=False)
class PayloadList():
    _list: list[Payload]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise ValueError("_list must be list.")
        if not all([isinstance(m, Payload) for m in self._list]):
            raise ValueError("_list element must be Payload.")

    def __iter__(self) -> Iterator[Payload]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> Payload:
        return self._list.__getitem__(item)

    @classmethod
    def create(cls, payload_tuple_list: list[tuple[MylistWithVideoList, FetchedVideoInfo | None]]) -> Self:
        return cls([
            Payload.create(mylist_with_videolist, fetched_info)
            for mylist_with_videolist, fetched_info in payload_tuple_list
        ])

if __name__ == "__main__":
    pass

