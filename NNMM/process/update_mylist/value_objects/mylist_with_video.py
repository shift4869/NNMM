from dataclasses import dataclass
from typing import Self

from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.value_objects.typed_mylist import TypedMylist
from NNMM.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from NNMM.process.update_mylist.value_objects.video_dict_list import VideoDictList


@dataclass(frozen=False)
class MylistWithVideo:
    """マイリストと、そのマイリストが保持する動画情報を紐づけたクラス"""

    _typed_mylist: TypedMylist
    _video_list: TypedVideoList

    def __post_init__(self) -> None:
        if not isinstance(self._typed_mylist, TypedMylist):
            raise ValueError("_typed_mylist must be TypedMylist.")
        if not isinstance(self._video_list, TypedVideoList):
            raise ValueError("_video_list must be TypedVideoList.")

    @property
    def mylist(self) -> TypedMylist:
        return self._typed_mylist

    @property
    def video_list(self) -> TypedVideoList:
        return self._video_list

    @classmethod
    def create(cls, typed_mylist: TypedMylist, mylist_info_db: MylistInfoDBController) -> Self:
        """マイリストと、そのマイリストが保持する動画情報を取得して紐づける

        Args:
            typed_mylist (TypedMylist): マイリスト
            mylist_info_db (MylistInfoDBController): MylistInfo 取得用DBコントローラ

        Raises:
            ValueError: 引数の型が不正な場合

        Returns:
            Self: _description_
        """
        if not isinstance(typed_mylist, TypedMylist):
            raise ValueError("typed_mylist must be TypedMylist.")
        if not isinstance(mylist_info_db, MylistInfoDBController):
            raise ValueError("mylist_info_db must be MylistInfoDBController.")

        mylist_url = typed_mylist.url.non_query_url
        video_dict_list = VideoDictList.create(mylist_info_db.select_from_mylist_url(mylist_url))
        typed_video_list = video_dict_list.to_typed_video_list()
        return cls(typed_mylist, typed_video_list)


if __name__ == "__main__":
    pass
