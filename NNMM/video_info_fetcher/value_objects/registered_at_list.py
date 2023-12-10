from dataclasses import dataclass
from typing import Iterable

from NNMM.video_info_fetcher.value_objects.registered_at import RegisteredAt


@dataclass(frozen=True)
class RegisteredAtList(Iterable):
    """登録日時リスト

    登録日時についてはRegisteredAt を参照
    空リストも許容する

    Raises:
        TypeError: 引数がリストでない場合
        ValueError: 引数のリストの要素が一つでもRegisteredAt でない場合

    Returns:
        RegisteredAtList: 登録日時リスト
    """
    _list: list[RegisteredAt]

    DESTINATION_DATETIME_FORMAT = RegisteredAt.DESTINATION_DATETIME_FORMAT

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid RegisteredAtList.")
        if self._list:
            if not all([isinstance(r, RegisteredAt) for r in self._list]):
                raise ValueError(f"include not RegisteredAt element, invalid RegisteredAtList")

    def __iter__(self) -> Iterable[RegisteredAt]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    @classmethod
    def create(cls, registered_at_list: list[RegisteredAt] | list[str]) -> "RegisteredAtList":
        """RegisteredAtList インスタンスを作成する

        Args:
            registered_at_list (list[RegisteredAt] | list[str]):
                RegisteredAt のリスト、またはDESTINATION_DATETIME_FORMAT パターンの文字列リスト
                空リストも許容される

        Raises:
            TypeError: registered_at_list がリストでない場合
            ValueError: その他インスタンス生成できない型の引数の場合

        Returns:
            RegisteredAtList: 登録日時リスト
        """
        if not isinstance(registered_at_list, list):
            raise TypeError("Args is not list.")
        if not registered_at_list:
            return cls([])
        if isinstance(registered_at_list[0], RegisteredAt):
            return cls(registered_at_list)
        if isinstance(registered_at_list[0], str):
            return cls([RegisteredAt(r) for r in registered_at_list])
        raise ValueError("Create RegisteredAtList failed.")


if __name__ == "__main__":
    NUM = 5
    base_dt_str = "2022-05-12 00:01:0{}"
    registered_ats = [base_dt_str.format(i) for i in range(1, NUM + 1)]

    registered_at_list = RegisteredAtList.create(registered_ats)
    for dt_str in registered_at_list:
        print(dt_str)
