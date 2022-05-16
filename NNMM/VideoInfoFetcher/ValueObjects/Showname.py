# coding: utf-8
import re
from dataclasses import dataclass

from NNMM.VideoInfoFetcher.ValueObjects.Myshowname import Myshowname
from NNMM.VideoInfoFetcher.ValueObjects.Username import Username


@dataclass(frozen=True)
class Showname():
    _name: str  # マイリスト表示名

    # 以下のどちらかの形式のみ受け付ける
    UPLOADED_PATTERN = "^(.*)さんの投稿動画$"  # {username}さんの投稿動画
    MYLIST_PATTERN = "^「(.*)」-(.*)さんのマイリスト$"  # 「{myshowname}」-{username}さんのマイリスト

    def __post_init__(self) -> None:
        PATTERN_LIST = [
            self.UPLOADED_PATTERN,
            self.MYLIST_PATTERN
        ]
        if not isinstance(self._name, str):
            raise TypeError("name is not string, invalid Showname.")
        if not any([re.search(p, self._name) is not None for p in PATTERN_LIST]):
            raise ValueError(f"'{self._name}' is invalid Showname")

    @property
    def name(self):
        return self._name

    @classmethod
    def create(cls, username: Username, myshowname: Myshowname | None = None) -> "Showname":
        showname = ""
        if myshowname is None:
            showname = f"{username.name}さんの投稿動画"
        if isinstance(myshowname, Myshowname):
            showname = f"「{myshowname.name}」-{username.name}さんのマイリスト"
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
            showname = Showname.create(Username(username))
            print(showname)
        except (ValueError, TypeError) as e:
            print(e.args[0])

    for username in usernames:
        for myshowname in myshownames:
            try:
                showname = Showname.create(Username(username), Myshowname(myshowname))
                print(showname)
            except (ValueError, TypeError) as e:
                print(e.args[0])
