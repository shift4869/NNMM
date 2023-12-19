from dataclasses import dataclass
from typing import ClassVar, Iterator, Self

from NNMM.model import Mylist
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.value_objects.mylist_dict import MylistDict
from NNMM.process.update_mylist.value_objects.mylist_dict_list import MylistDictList
from NNMM.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from NNMM.process.update_mylist.value_objects.typed_mylist import TypedMylist
from NNMM.process.update_mylist.value_objects.typed_mylist_list import TypedMylistList
from NNMM.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from NNMM.process.update_mylist.value_objects.video_dict_list import VideoDictList
from NNMM.util import Result
from NNMM.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


@dataclass(frozen=False)
class Payload():
    _mylist_with_video: MylistWithVideo
    _fetched_info: FetchedVideoInfo

    def __init__(self, mylist_with_video: MylistWithVideo, fetched_info: FetchedVideoInfo | None) -> None:
        if not isinstance(mylist_with_video, MylistWithVideo):
            raise ValueError("mylist_with_video must be MylistWithVideo.")
        self._mylist_with_video = mylist_with_video

        if not fetched_info:
            self._fetched_info = None
            return

        if not isinstance(fetched_info, FetchedVideoInfo):
            raise ValueError("fetched_info must be FetchedVideoInfo | Result.")
        self._fetched_info = fetched_info

    @property
    def mylist_with_video_list(self) -> MylistWithVideo:
        return self._mylist_with_video

    @property
    def mylist(self) -> TypedMylist:
        return self._mylist_with_video.mylist

    @property
    def video_list(self) -> TypedVideoList:
        return self._mylist_with_video.video_list

    @property
    def fetched_info(self) -> FetchedVideoInfo:
        return self._fetched_info

    @classmethod
    def create(cls, mylist_with_video: MylistWithVideo, fetched_info: FetchedVideoInfo | None) -> Self:
        return cls(mylist_with_video, fetched_info)

if __name__ == "__main__":
    pass

