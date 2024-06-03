from dataclasses import dataclass
from typing import Iterator, Self

from nnmm.process.value_objects.table_row import TableRow, TableRowTuple


@dataclass(frozen=True)
class TableRowList:
    _list: list[TableRow]

    COLS_NAME = TableRow.COLS_NAME

    def __post_init__(self) -> None:
        """空リストは許容する"""
        if not isinstance(self._list, list):
            raise ValueError(f"_list must be list.")
        if not all([isinstance(r, TableRow) for r in self._list]):
            raise ValueError(f"_list element must be TableRow.")

    def __iter__(self) -> Iterator[TableRow]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> TableRow:
        return self._list.__getitem__(item)

    def __setitem__(self, key, value):
        return self._list.__setitem__(key, value)

    def to_table_data(self) -> list[list[str]]:
        return [row.to_row() for row in self._list]

    def to_table_row_list(self) -> list[TableRowTuple]:
        return [row.to_namedtuple() for row in self._list]

    @classmethod
    def create(cls, table_row_list: list[list[str]]) -> Self:
        """テーブル行リストインスタンスを作成する

        Args:
            table_row_list (list[list[str]]):
                テーブル行を表す文字列リストのリスト
                主に画面の window["-TABLE-"].Values を受け取る
                空リストは許容する

        Raises:
            ValueError: table_row_list がlistでない

        Returns:
            Self: TableRowList インスタンス
        """
        if not isinstance(table_row_list, list):
            raise ValueError(f"table_row_list must be list.")
        return cls([TableRow.create(row) for row in table_row_list])


class SelectedTableRowList(TableRowList):
    pass


if __name__ == "__main__":
    NUM = 5
    row_list = [
        [
            f"{i}",
            f"sm1234657{i}",
            f"title_{i}",
            f"username_{i}",
            "",
            "2023-12-13 07:25:00",
            "2023-12-13 07:25:00",
            "https://www.nicovideo.jp/watch/sm12346578",
            "https://www.nicovideo.jp/user/11111111/video",
        ]
        for i in range(1, NUM + 1)
    ]
    table_row_list = TableRowList.create(row_list)
    print(table_row_list)
    table_data = table_row_list.to_table_data()
    print(table_data)
    table_row_list = table_row_list.to_table_row_list()
    print(table_row_list)
    table_row_list[0] = table_row_list[0]._replace(row_index=100)
    print(table_row_list)
