from dataclasses import dataclass
from typing import ClassVar, Iterator, Self

from NNMM.model import Mylist
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.value_objects.mylist_dict import MylistDict
from NNMM.process.update_mylist.value_objects.mylist_dict_list import MylistDictList
from NNMM.process.update_mylist.value_objects.typed_mylist import TypedMylist
from NNMM.process.update_mylist.value_objects.typed_mylist_list import TypedMylistList
from NNMM.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from NNMM.process.update_mylist.value_objects.video_dict_list import VideoDictList


@dataclass(frozen=False)
class MylistWithVideo():
    _typed_mylist: TypedMylist
    _video_list: TypedVideoList

    def __init__(self, typed_mylist: TypedMylist, typed_video_list: TypedVideoList) -> None:
        if not isinstance(typed_mylist, TypedMylist):
            raise ValueError("typed_mylist must be TypedMylist.")
        if not isinstance(typed_video_list, TypedVideoList):
            raise ValueError("typed_video_list must be TypedVideoList.")
        self._typed_mylist = typed_mylist
        self._video_list = typed_video_list

    @property
    def mylist(self) -> TypedMylist:
        return self._typed_mylist

    @property
    def video_list(self) -> TypedVideoList:
        return self._video_list

    @classmethod
    def create(cls, typed_mylist: TypedMylist, mylist_info_db: MylistInfoDBController) -> Self:
        if not isinstance(typed_mylist, TypedMylist):
            raise ValueError("typed_mylist must be TypedMylist.")
        if not isinstance(mylist_info_db, MylistInfoDBController):
            raise ValueError("mylist_info_db must be MylistInfoDBController.")

        mylist_url = typed_mylist.url
        video_dict_list = VideoDictList.create(
            mylist_info_db.select_from_mylist_url(mylist_url)
        )
        typed_video_list = video_dict_list.to_typed_video_list()
        return cls(typed_mylist, typed_video_list)

    @classmethod
    def create_from_mylist_and_video(cls, typed_mylist: TypedMylist, typed_video_list: TypedVideoList) -> Self:
        return cls(typed_mylist, typed_video_list)

if __name__ == "__main__":
    pass

