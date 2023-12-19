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
        valid_key = Mylist.__table__.c.keys()
        instance_key = list(self._dict.keys())
        if instance_key != valid_key:
            raise ValueError("_dict.keys() is invalid key.")
        return True

    def __getitem__(self, item) -> Any:
        return self._dict.__getitem__(item)

    def __setitem__(self, key, value) -> None:
        return self._dict.__setitem__(key, value)

    @property
    def mylist(self) -> Mylist:
        return Mylist(
            self._dict["id"],
            self._dict["username"],
            self._dict["mylistname"],
            self._dict["type"],
            self._dict["showname"],
            self._dict["url"],
            self._dict["created_at"],
            self._dict["updated_at"],
            self._dict["checked_at"],
            self._dict["check_interval"],
            self._dict["is_include_new"],
        )

    def to_typed_mylist(self) -> TypedMylist:
        return TypedMylist(
            self._dict["id"],
            self._dict["username"],
            self._dict["mylistname"],
            self._dict["type"],
            self._dict["showname"],
            self._dict["url"],
            self._dict["created_at"],
            self._dict["updated_at"],
            self._dict["checked_at"],
            self._dict["check_interval"],
            self._dict["is_include_new"]
        )

    @classmethod
    def create(cls, mylist_dict: dict) -> Self:
        return cls(mylist_dict)


if __name__ == "__main__":
    pass
