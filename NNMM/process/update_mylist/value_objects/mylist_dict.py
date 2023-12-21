from dataclasses import dataclass
from typing import Any, Self

from NNMM.model import Mylist
from NNMM.process.update_mylist.value_objects.typed_mylist import TypedMylist


@dataclass(frozen=True)
class MylistDict():
    _dict: dict

    def __post_init__(self) -> None:
        if not isinstance(self._dict, dict):
            raise ValueError("_dict must be dict.")
        self.is_valid()

    def is_valid(self) -> bool:
        """受け取った dict が Mylist の属性をキーとして含むかを調べる

        Raises:
            ValueError: dict のキーが Mylist の属性と一致しなかった場合

        Returns:
            bool: dict のキーと Mylist の属性が一致した場合True
        """
        valid_key = Mylist.__table__.c.keys()
        instance_key = list(self._dict.keys())
        if instance_key != valid_key:
            raise ValueError("_dict.keys() is invalid key.")
        return True

    def __getitem__(self, key: str) -> Any:
        return self._dict.__getitem__(key)

    def to_typed_mylist(self) -> TypedMylist:
        return TypedMylist.create(self._dict)

    @classmethod
    def create(cls, mylist_dict: dict) -> Self:
        """Mylist を表す dict のクラスを作成する

        Args:
            mylist_dict (dict): Mylist を表す dict のリスト

        Returns:
            Self: MylistDict インスタンス
        """
        return cls(mylist_dict)


if __name__ == "__main__":
    pass
