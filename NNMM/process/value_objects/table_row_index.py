from dataclasses import dataclass


@dataclass(frozen=True)
class TableRowIndex():
    _index: int

    def __post_init__(self) -> None:
        """index は0ベース
        """
        if not isinstance(self._index, int):
            raise ValueError("row_index must be int.")

        if self._index < 0:
            raise ValueError("row_index must be row_index >= 0.")

    def __int__(self) -> int:
        return self.index

    @property
    def index(self):
        return self._index


if __name__ == "__main__":
    s_row = 1
    table_row_index = TableRowIndex(s_row)
    print(table_row_index)
