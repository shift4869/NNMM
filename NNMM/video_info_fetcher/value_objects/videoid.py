import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Videoid():
    """動画ID

    動画IDは基本的には(sm + 数字)からなる 例：sm12345678
    動画IDは空文字列は許容されない

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数が動画IDでない場合

    Returns:
        Videoid: 動画ID
    """
    _id: str  # 動画ID sm12345678

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._id, str):
            raise TypeError("id is not string, invalid Videoid.")
        if not re.search("^sm[0-9]+$", self._id):
            raise ValueError(f"'{self._id}' is invalid Videoid")

    @property
    def id(self) -> str:
        """保持している動画IDを返す
        """
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
