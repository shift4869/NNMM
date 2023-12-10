from dataclasses import dataclass


@dataclass(frozen=True)
class Title():
    """動画タイトル

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数が空文字列の場合

    Returns:
        Title: 動画タイトル
    """
    _name: str  # 動画タイトル

    def __post_init__(self) -> None:
        """初期化後処理
        """
        if not isinstance(self._name, str):
            raise TypeError("name is not string, invalid Title.")
        if self._name == "":
            raise ValueError("empty string, invalid Title")
        object.__setattr__(self, "_name", self._name.strip())

    @property
    def name(self) -> str:
        """保持している動画タイトル名を返す
        """
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
