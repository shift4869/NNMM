from dataclasses import dataclass
from typing import Self

from NNMM.process.value_objects.showname import Showname


@dataclass(frozen=True)
class MylistRow(Showname):
    NEW_MARK = "*:"

    def is_new_mark(self) -> bool:
        return self._name.startswith(self.NEW_MARK)

    def without_new_mark_name(self) -> str:
        if self.is_new_mark():
            return str(self._name[len(self.NEW_MARK):])
        return str(self._name)

    def with_new_mark_name(self) -> str:
        if self.is_new_mark():
            return str(self._name)
        return str(self.NEW_MARK + self._name)

    @classmethod
    def create(cls, showname_list: list[str]) -> Self:
        """選択されたマイリストを表すインスタンスを作成する

        Args:
            showname_list (list[str]):
                選択されたマイリストを表す文字列リスト
                主に画面の values["-LIST-"] を受け取る
                showname_list は長さ1を想定しており、
                それ以降の要素は無視される
                空リストは許容されない

        Raises:
            ValueError: showname_list がlistでない

        Returns:
            Self: SelectedMylist インスタンス
        """
        if not isinstance(showname_list, list):
            raise ValueError(f"showname_list must be list.")
        if not len(showname_list) > 0:
            raise ValueError(f"showname_list must be length > 0.")

        showname = showname_list[0]
        return cls(showname)


class SelectedMylistRow(MylistRow):
    pass


if __name__ == "__main__":
    selected_mylist_row = ["投稿者1さんの投稿動画"]
    selected_mylist = MylistRow.create(selected_mylist_row)
    print(selected_mylist)
