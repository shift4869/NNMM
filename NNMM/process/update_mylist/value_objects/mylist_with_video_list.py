from dataclasses import dataclass
from typing import Iterator, Self

from NNMM.model import Mylist
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.value_objects.mylist_dict_list import MylistDictList
from NNMM.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo


@dataclass(frozen=False)
class MylistWithVideoList():
    """複数のマイリストと、それぞれのマイリストが保持する動画情報をそれぞれ取得して紐づける

    MylistWithVideo の List を表す
    """    
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
        """複数のマイリストと、それぞれのマイリストが保持する動画情報をそれぞれ取得して紐づける

        Args:
            mylist_list (list[dict] | list[Mylist]): マイリストorマイリストを表す辞書 のリスト
            mylist_info_db (MylistInfoDBController): MylistInfo 取得用DBコントローラ

        Raises:
            ValueError: 引数の型が不正な場合

        Returns:
            Self: MylistWithVideoList インスタンス
        """
        if not isinstance(mylist_list, list):
            raise ValueError("mylist_list must be list.")
        is_all_mylist_info = all([isinstance(mylist_info, Mylist) for mylist_info in mylist_list])
        is_all_dict = all([isinstance(mylist_info, dict) for mylist_info in mylist_list])
        if not (is_all_mylist_info or is_all_dict):
            raise ValueError("all mylist_list element must be Mylist or dict.")

        if is_all_mylist_info:
            # mylist_list が list[Mylist] で渡ってきた場合
            # list[dict] に揃えて扱う
            mylist_list: list[dict] = [mylist.to_dict() for mylist in mylist_list]

        mylist_dict_list = MylistDictList.create(mylist_list)
        typed_mylist_list = mylist_dict_list.to_typed_mylist_list()

        return cls([
            MylistWithVideo.create(typed_mylist, mylist_info_db)
            for typed_mylist in typed_mylist_list
        ])


if __name__ == "__main__":
    pass

