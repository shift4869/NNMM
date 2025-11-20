from dataclasses import dataclass
from typing import Iterator, Self

from nnmm.process.value_objects.table_row_index import TableRowIndex


@dataclass(frozen=True)
class TableRowIndexList:
    _list: list[TableRowIndex]

    def __post_init__(self) -> None:
        """空リストは許容する"""
        if not isinstance(self._list, list):
            raise ValueError("_list must be list.")
        if not all([isinstance(r, TableRowIndex) for r in self._list]):
            raise ValueError("_list element must be TableRowIndex.")

    def __iter__(self) -> Iterator[TableRowIndex]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> TableRowIndex:
        return self._list.__getitem__(item)

    def __setitem__(self, key, value):
        return self._list.__setitem__(key, value)

    def to_int_list(self) -> list[int]:
        return [int(row_index) for row_index in self._list]

    @classmethod
    def create(cls, table_row_index_list: list[int]) -> Self:
        """テーブル行インデックスリストインスタンスを作成する

        Args:
            table_row_index_list: (list[int]):
                テーブル行インデックスを表す数値リストのリスト
                主に画面のテーブルペインの選択行の行番号リストを受け取る
                空リストは許容する

        Raises:
            ValueError: table_row_index_list がlistでない

        Returns:
            Self: TableRowIndexList インスタンス
        """
        if not isinstance(table_row_index_list, list):
            raise ValueError(f"table_row_index_list must be list.")
        return cls([TableRowIndex(row_index) for row_index in table_row_index_list])


class SelectedTableRowIndexList(TableRowIndexList):
    pass


if __name__ == "__main__":
    NUM = 5
    row_list = list(range(1, NUM + 1))
    table_row_list = TableRowIndexList.create(row_list)
    print(table_row_list)
    int_list = table_row_list.to_int_list()
    print(int_list)
