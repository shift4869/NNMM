# coding: utf-8
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Mylistid():
    _id: str  # マイリストID 12345678

    def __post_init__(self) -> None:
        if not isinstance(self._id, str):
            raise TypeError("id is not string, invalid Mylistid.")
        # マイリストIDは空白も有り得る
        if not re.search("^[0-9]*$", self._id):
            raise ValueError(f"'{self._id}' is invalid Mylistid")

    @property
    def id(self):
        return self._id


if __name__ == "__main__":
    ids = [
        "72036443",
        "",
        "-1",
        72036443,
    ]

    for id in ids:
        try:
            mylistid = Mylistid(id)
            print(mylistid)
        except (ValueError, TypeError) as e:
            print(e.args[0])
