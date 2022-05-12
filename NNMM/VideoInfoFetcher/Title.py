# coding: utf-8
from dataclasses import dataclass


@dataclass(frozen=True)
class Title():
    _name: str  # 動画タイトル

    def __post_init__(self) -> None:
        if not isinstance(self._name, str):
            raise TypeError("name is not string, invalid Title.")
        if self._name == "":
            raise ValueError("empty string, invalid Title")

    @property
    def name(self):
        return self._name


if __name__ == "__main__":
    names = [
        "動画タイトル1",
        "",
        -1,
    ]

    for name in names:
        try:
            title = Title(name)
            print(title)
        except (ValueError, TypeError) as e:
            print(e.args[0])
