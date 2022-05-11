# coding: utf-8
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Userid():
    _id: str  # ユーザーID 1234567

    def __post_init__(self) -> None:
        if not isinstance(self._id, str):
            raise TypeError("id is not string, invalid Userid.")
        if not re.search("^[0-9]+$", self._id):
            raise ValueError(f"'{self._id}' is invalid Userid.")

    @property
    def id(self):
        return self._id


if __name__ == "__main__":
    ids = [
        "37896001",
        "",
        "-1",
        37896001,
    ]

    for id in ids:
        try:
            userid = Userid(id)
            print(userid)
        except (ValueError, TypeError) as e:
            print(e.args[0])
