import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Userid():
    """ユーザーID

    ユーザーIDは基本的には数字からなる 例：12345678
    ユーザーIDは空文字列は許容されない

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数が数字のみでない, もしくは空文字列でない場合

    Returns:
        Userid: ユーザーID
    """
    _id: str  # ユーザーID 1234567

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._id, str):
            raise TypeError("id is not string, invalid Userid.")
        if not re.search("^[0-9]+$", self._id):
            raise ValueError(f"'{self._id}' is invalid Userid.")

    @property
    def id(self) -> str:
        """保持しているユーザーIDを返す
        """
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
