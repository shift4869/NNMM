from dataclasses import dataclass
from typing import Self

from NNMM.video_info_fetcher.value_objects.showname import Showname


@dataclass(frozen=True)
class MylistRow(Showname):
    NEW_MARK = "*:"

    def __init__(self, showname: str):
        super().__init__(showname)
        object.__setattr__(self, "_name", self.without_new_mark_name())

    def is_new_mark(self) -> bool:
        return self._name.startswith(self.NEW_MARK)

    def without_new_mark_name(self) -> str:
        if self.is_new_mark():
            return str(self._name[len(self.NEW_MARK) :])
        return str(self._name)

    def with_new_mark_name(self) -> str:
        if self.is_new_mark():
            return str(self._name)
        return str(self.NEW_MARK + self._name)

    @classmethod
    def create(cls, showname: Showname | str) -> Self:
        """選択されたマイリストを表すインスタンスを作成する

        Args:
            showname_list (Showname | str):
                選択されたマイリストを表す文字列 or Showname
                主に画面の values["-LIST-"] を受け取る
                空文字列は許容されない

        Raises:
            ValueError: showname が Showname | str でない

        Returns:
            Self: SelectedMylist インスタンス
        """
        if not isinstance(showname, Showname | str):
            raise ValueError(f"showname must be Showname or str.")
        if isinstance(showname, Showname):
            showname: str = showname.name
        if showname == "":
            raise ValueError(f"showname must be non-empty.")
        if showname.startswith(cls.NEW_MARK):
            showname: str = str(showname[len(cls.NEW_MARK) :])
        return cls(showname)


class SelectedMylistRow(MylistRow):
    pass


if __name__ == "__main__":
    selected_mylist_row = ["投稿者1さんの投稿動画"]
    selected_mylist = MylistRow.create(selected_mylist_row)
    print(selected_mylist)

    selected_mylist_row = ["*:投稿者1さんの投稿動画"]
    selected_mylist = MylistRow.create(selected_mylist_row)
    print(selected_mylist)
