from dataclasses import dataclass
from typing import Iterator, Self

from NNMM.model import Mylist
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.value_objects.mylist_dict_list import MylistDictList
from NNMM.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from NNMM.process.update_mylist.value_objects.typed_mylist_list import TypedMylistList
from NNMM.process.update_mylist.value_objects.typed_video_list import TypedVideoList


@dataclass(frozen=False)
class MylistWithVideoList():
    _list: list[MylistWithVideo]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise ValueError("_list must be list.")
        if not all([isinstance(m, MylistWithVideo) for m in self._list]):
            raise ValueError("_list element must be MylistWithVideo.")

    def __iter__(self) -> Iterator[MylistWithVideo]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> MylistWithVideo:
        return self._list.__getitem__(item)

    @classmethod
    def create(cls, mylist_list: list[dict] | list[Mylist], mylist_info_db: MylistInfoDBController) -> Self:
        if not isinstance(mylist_list, list):
            raise ValueError("mylist_list must be list.")
        is_all_mylist_info = all([isinstance(mylist_info, Mylist) for mylist_info in mylist_list])
        is_all_dict = all([isinstance(mylist_info, dict) for mylist_info in mylist_list])
        if not (is_all_mylist_info or is_all_dict):
            raise ValueError("all mylist_list element must be Mylist or dict.")

        if is_all_mylist_info:
            records_list: list[dict] = []
            for mylist in mylist_list:
                record = mylist.to_dict()
                records_list.append(record)
            mylist_list: list[dict] = records_list

        mylist_dict_list = MylistDictList.create(mylist_list)
        typed_mylist_list = mylist_dict_list.to_typed_mylist_list()

        return cls([
            MylistWithVideo.create(typed_mylist, mylist_info_db)
            for typed_mylist in typed_mylist_list
        ])

    @classmethod
    def create_from_mylist_and_video(cls, typed_mylist_list: TypedMylistList, typed_video_list: TypedVideoList) -> Self:
        if not isinstance(typed_mylist_list, TypedMylistList):
            raise ValueError("typed_mylist_list must be TypedMylistList.")
        if not isinstance(typed_video_list, TypedVideoList):
            raise ValueError("typed_video_list must be TypedVideoList.")
        return cls([
            MylistWithVideo.create_from_mylist_and_video(typed_mylist, typed_video)
            for typed_mylist, typed_video in zip(typed_mylist_list, typed_video_list, strict=True)
        ])


if __name__ == "__main__":
    pass

