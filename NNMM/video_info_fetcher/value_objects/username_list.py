from dataclasses import dataclass
from typing import Iterable

from NNMM.video_info_fetcher.value_objects.username import Username


@dataclass(frozen=True)
class UsernameList(Iterable):
    """投稿者名リスト

    投稿者名についてはUsername を参照
    空リストも許容する

    Raises:
        TypeError: 引数がリストでない場合
        ValueError: 引数のリストの要素が一つでもUsername でない場合

    Returns:
        UsernameList: 投稿者名リスト
    """

    _list: list[Username]

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid UsernameList.")
        if self._list:
            if not all([isinstance(r, Username) for r in self._list]):
                raise ValueError(f"include not Username element, invalid UsernameList")

    def __iter__(self) -> Iterable[Username]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    @classmethod
    def create(cls, username_list: list[Username] | list[str]) -> "UsernameList":
        """UsernameList インスタンスを作成する

        Args:
            Username_list (list[Username] | list[str]):
                Username のリスト、文字列リスト
                空リストも許容される

        Raises:
            TypeError: Username_list がリストでない場合
            ValueError: その他インスタンス生成できない型の引数の場合

        Returns:
            UsernameList: 投稿者名リスト
        """
        if not isinstance(username_list, list):
            raise TypeError("Args is not list.")
        if not username_list:
            return cls([])
        if isinstance(username_list[0], Username):
            return cls(username_list)
        if isinstance(username_list[0], str):
            return cls([Username(r) for r in username_list])
        raise ValueError("Create UsernameList failed.")


if __name__ == "__main__":
    NUM = 5
    base_name = "作成者{}"
    names = [base_name.format(i) for i in range(1, NUM + 1)]

    username_list = UsernameList.create(names)
    for username in username_list:
        print(username)
