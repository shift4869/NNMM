from dataclasses import dataclass


@dataclass(frozen=True)
class MylistRowIndex():
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
    row_index = 1
    mylist_row_index = MylistRowIndex(row_index)
    print(mylist_row_index)
