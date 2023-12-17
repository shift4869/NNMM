from dataclasses import dataclass
from typing import Iterator, Self

from NNMM.process.value_objects.mylist_row_index import MylistRowIndex


@dataclass(frozen=True)
class MylistRowIndexList():
    _list: list[MylistRowIndex]

    def __post_init__(self) -> None:
        """空リストは許容する
        """
        if not isinstance(self._list, list):
            raise ValueError(f"_list must be list.")
        if not all([isinstance(r, MylistRowIndex) for r in self._list]):
            raise ValueError(f"_list element must be MylistRowIndex.")

    def __iter__(self) -> Iterator[MylistRowIndex]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> MylistRowIndex:
        return self._list.__getitem__(item)

    def __setitem__(self, key, value):
        return self._list.__setitem__(key, value)

    def to_int_list(self) -> list[int]:
        return [int(row_index) for row_index in self._list]

    @classmethod
    def create(cls, mylist_row_index_list: list[int]) -> Self:
        """マイリストインデックスリストインスタンスを作成する

        Args:
            mylist_row_index_list: (list[int]):
                マイリストインデックスを表す数値リストのリスト
                主に画面の window["-LIST-"].get_indexes() を受け取る
                空リストは許容する

        Raises:
            ValueError: mylist_row_index_list がlistでない

        Returns:
            Self: MylistRowIndexList インスタンス
        """
        if not isinstance(mylist_row_index_list, list):
            raise ValueError(f"mylist_row_index_list must be list.")
        return cls(
            [MylistRowIndex(row_index) for row_index in mylist_row_index_list]
        )


class SelectedMylistRowIndexList(MylistRowIndexList):
    pass


if __name__ == "__main__":
    NUM = 5
    row_list = list(range(1, NUM + 1))
    mylist_row_list = MylistRowIndexList.create(row_list)
    print(mylist_row_list)
    int_list = mylist_row_list.to_int_list()
    print(int_list)
