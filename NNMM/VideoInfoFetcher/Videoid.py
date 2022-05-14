# coding: utf-8
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Videoid():
    _id: str  # 動画ID sm12345678

    def __post_init__(self) -> None:
        if not isinstance(self._id, str):
            raise TypeError("id is not string, invalid Videoid.")
        if not re.search("^sm[0-9]+$", self._id):
            raise ValueError(f"'{self._id}' is invalid Videoid")

    @property
    def id(self):
        return self._id


if __name__ == "__main__":
    ids = [
        "sm12345678",
        "nm12346578",
        "",
        -1,
    ]

    for id in ids:
        try:
            videoid = Videoid(id)
            print(videoid)
        except (ValueError, TypeError) as e:
            print(e.args[0])
