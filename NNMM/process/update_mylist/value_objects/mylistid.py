import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Mylistid():
    """マイリストID

    マイリストIDは基本的には(8桁の)数字からなる 例：12345678
    マイリストIDは空白も許容される（動画投稿ページにはマイリストIDがないため）

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数が数字のみでなく, かつ空文字列でもない場合

    Returns:
        Mylistid: マイリストID
    """
    _id: str  # マイリストID 12345678

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._id, str):
            raise TypeError("id is not string, invalid Mylistid.")
        # マイリストIDは空白も有り得る
        if not re.search(r"^[0-9]*$", self._id):
            raise ValueError(f"'{self._id}' is invalid Mylistid")

    @property
    def id(self) -> str:
        """保持しているマイリストIDを返す
        """
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
