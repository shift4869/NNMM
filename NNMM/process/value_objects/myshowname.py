from dataclasses import dataclass


@dataclass(frozen=True)
class Myshowname:
    """マイリスト名

    Notes:
        マイリスト名はマイリストの名前を表す
            投稿動画ページの場合、"投稿動画" をマイリスト名とする
            マイリストページの場合、そのマイリストの名前とする

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数が空文字列の場合

    Returns:
        Myshowname: マイリスト名
    """

    _name: str  # マイリスト名 「まとめマイリスト」

    def __post_init__(self) -> None:
        """初期化後処理

        Notes:
            バリデーションのみ
        """
        if not isinstance(self._name, str):
            raise TypeError("name is not string, invalid Myshowname.")
        if self._name == "":
            raise ValueError("empty string, invalid Myshowname")

    @property
    def name(self) -> str:
        """保持しているマイリスト名を返す"""
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
