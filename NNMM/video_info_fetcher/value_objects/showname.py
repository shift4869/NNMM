import re
from dataclasses import dataclass
from typing import Self

from NNMM.util import MylistType
from NNMM.video_info_fetcher.value_objects.myshowname import Myshowname
from NNMM.video_info_fetcher.value_objects.username import Username


@dataclass(frozen=True)
class Showname:
    """マイリスト表示名

    実際にNNMM上でマイリストペインに表示される際の表示名

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数が表示名のパターンでない場合

    Returns:
        _type_: _description_
    """

    _name: str  # マイリスト表示名

    # 以下のどちらかの形式のみ受け付ける
    UPLOADED_PATTERN = "^(.*)さんの投稿動画$"  # {username}さんの投稿動画
    MYLIST_PATTERN = "^「(.*)」-(.*)さんのマイリスト$"  # 「{myshowname}」-{username}さんのマイリスト
    SERIES_PATTERN = "^「(.*)」-(.*)さんのシリーズ$"  # 「{myshowname}」-{username}さんのシリーズ

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        PATTERN_LIST = [self.UPLOADED_PATTERN, self.MYLIST_PATTERN, self.SERIES_PATTERN]
        if not isinstance(self._name, str):
            raise TypeError("name is not string, invalid Showname.")
        if not any([re.search(p, self._name) is not None for p in PATTERN_LIST]):
            raise ValueError(f"'{self._name}' is invalid Showname")

    @property
    def name(self) -> str:
        """保持しているマイリスト表示名を返す"""
        return self._name

    @classmethod
    def create(cls, mylist_type: MylistType, username: Username, myshowname: Myshowname | None = None) -> Self:
        """Showname インスタンスを生成する

        mylist_type に対応したマイリスト表示名を設定する

        Args:
            mylist_type (MylistType): マイリストタイプ
            username (Username): ユーザー名インスタンス
            myshowname (Myshowname, optional): マイリスト名インスタンス or None

        Returns:
            Showname: マイリスト表示名
        """
        if not isinstance(mylist_type, MylistType):
            raise ValueError("mylist_type must be MylistType.")
        if not isinstance(username, Username):
            raise ValueError("username must be Username.")
        if not isinstance(myshowname, Myshowname | None):
            raise ValueError("myshowname must be Myshowname | None.")

        if (not myshowname) and (mylist_type != MylistType.uploaded):
            raise ValueError("myshowname is None, but mylist_type is not MylistType.uploaded.")

        showname = ""
        match mylist_type:
            case MylistType.uploaded:
                # MylistType.uploaded のとき myshowname は無視される
                showname = f"{username.name}さんの投稿動画"
            case MylistType.mylist:
                showname = f"「{myshowname.name}」-{username.name}さんのマイリスト"
            case MylistType.series:
                showname = f"「{myshowname.name}」-{username.name}さんのシリーズ"
            case _:
                raise ValueError("mylist_type is invalid MylistType.")
        return cls(showname)


if __name__ == "__main__":
    usernames = [
        "投稿者1",
        "投稿者2",
        "",
        -1,
    ]
    myshownames = [
        "テスト用マイリスト1",
        "テスト用マイリスト2",
        "",
        -1,
    ]

    for username in usernames:
        try:
            showname = Showname.create(MylistType.uploaded, Username(username))
            print(showname)
        except (ValueError, TypeError) as e:
            print(e.args[0])

    for username in usernames:
        for myshowname in myshownames:
            try:
                showname = Showname.create(MylistType.mylist, Username(username), Myshowname(myshowname))
                print(showname)
            except (ValueError, TypeError) as e:
                print(e.args[0])

    for username in usernames:
        for myshowname in myshownames:
            try:
                showname = Showname.create(MylistType.series, Username(username), Myshowname(myshowname))
                print(showname)
            except (ValueError, TypeError) as e:
                print(e.args[0])
