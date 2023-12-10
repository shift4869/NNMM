from dataclasses import dataclass


@dataclass(frozen=True)
class Username():
    """投稿者名

    投稿者名は動画を投稿したユーザー名を表す
        投稿動画ページの場合、投稿者 = 動画投稿者となる
            この場合は投稿動画ページにあるすべての動画の投稿者は単一である
        マイリストページの場合、そのマイリストに含まれるそれぞれの動画の作成者となる
            マイリスト作成者とマイリストに含まれる動画の投稿者とは関係がないかもしれない
    投稿者名は空文字列は許容されない

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数が空文字列の場合

    Returns:
        Username: 投稿者名
    """
    _name: str  # 投稿者名

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._name, str):
            raise TypeError("name is not string, invalid Username.")
        if self._name == "":
            raise ValueError("empty string, invalid Username")

    @property
    def name(self) -> str:
        """保持している投稿者名を返す
        """
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
