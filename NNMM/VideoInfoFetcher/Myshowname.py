# coding: utf-8
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Myshowname():
    _name: str  # マイリスト名 「まとめマイリスト」

    def __post_init__(self) -> None:
        if not isinstance(self._name, str):
            raise TypeError("name is not string, invalid Myshowname.")
        if self._name == "":
            raise ValueError("empty string, invalid Myshowname")

    @property
    def name(self):
        return self._name


if __name__ == "__main__":
    names = [
        "テスト用マイリスト1",
        "",
        -1,
    ]

    for name in names:
        try:
            myshowname = Myshowname(name)
            print(myshowname)
        except (ValueError, TypeError) as e:
            print(e.args[0])
