from dataclasses import dataclass
from typing import Iterator, Self

from nnmm.process.value_objects.mylist_row import MylistRow
from nnmm.video_info_fetcher.value_objects.showname import Showname


@dataclass(frozen=True)
class MylistRowList:
    _list: list[MylistRow]

    def __post_init__(self) -> None:
        """空リストは許容する"""
        if not isinstance(self._list, list):
            raise ValueError(f"_list must be list.")
        if not all([isinstance(r, MylistRow) for r in self._list]):
            raise ValueError(f"_list element must be MylistRow.")

    def __iter__(self) -> Iterator[MylistRow]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> MylistRow:
        return self._list.__getitem__(item)

    def __setitem__(self, key, value):
        return self._list.__setitem__(key, value)

    def to_name_list(self) -> list[str]:
        return [row.name for row in self._list]

    @classmethod
    def create(cls, mylist_row_list: list[str]) -> Self:
        """マイリスト行リストインスタンスを作成する

        Args:
            mylist_row_list (list[str]]):
                マイリスト行を表す文字列リストのリスト
                主に画面の list_widget の要素の配列を受け取る
                空リストは許容する

        Raises:
            ValueError: mylist_row_list がlistでない

        Returns:
            Self: MylistRowList インスタンス
        """
        if not isinstance(mylist_row_list, list):
            raise ValueError(f"mylist_row_list must be list.")
        return cls([MylistRow.create(row) for row in mylist_row_list])


if __name__ == "__main__":
    NUM = 5
    row_list = [
        [
            f"投稿者{i}さんの投稿動画",
        ]
        for i in range(1, NUM + 1)
    ]
    mylist_row_list = MylistRowList.create(row_list)
    print(mylist_row_list)
    name_list = mylist_row_list.to_name_list()
    print(name_list)
