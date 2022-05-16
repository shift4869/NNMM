# coding: utf-8
from dataclasses import dataclass


@dataclass(frozen=True)
class Username():
    _name: str  # マイリスト作成者名

    def __post_init__(self) -> None:
        if not isinstance(self._name, str):
            raise TypeError("name is not string, invalid Username.")
        if self._name == "":
            raise ValueError("empty string, invalid Username")

    @property
    def name(self):
        return self._name


if __name__ == "__main__":
    names = [
        "作成者1",
        "",
        -1,
    ]

    for name in names:
        try:
            username = Username(name)
            print(username)
        except (ValueError, TypeError) as e:
            print(e.args[0])
