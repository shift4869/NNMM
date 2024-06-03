import enum
from collections import namedtuple
from dataclasses import dataclass
from typing import Any, Self

from nnmm.video_info_fetcher.value_objects.mylist_url import MylistURL
from nnmm.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory
from nnmm.video_info_fetcher.value_objects.registered_at import RegisteredAt
from nnmm.video_info_fetcher.value_objects.title import Title
from nnmm.video_info_fetcher.value_objects.uploaded_at import UploadedAt
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.videoid import Videoid


class Status(enum.Enum):
    watched = ""
    not_watched = "未視聴"


fields = [
    "row_index",
    "video_id",
    "title",
    "username",
    "status",
    "uploaded_at",
    "registered_at",
    "video_url",
    "mylist_url",
]
TableRowTuple = namedtuple("TableRowTuple", fields)


@dataclass(frozen=True)
class TableRow:
    row_number: int
    video_id: Videoid
    title: Title
    username: Username
    status: Status
    uploaded_at: UploadedAt
    registered_at: RegisteredAt
    video_url: VideoURL
    mylist_url: MylistURL

    COLS_NAME = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]

    def __post_init__(self) -> None:
        if not isinstance(self.row_number, int):
            raise ValueError("row_index must be int.")
        if not isinstance(self.video_id, Videoid):
            raise ValueError("video_id must be Videoid.")
        if not isinstance(self.title, Title):
            raise ValueError("title must be Title.")
        if not isinstance(self.username, Username):
            raise ValueError("username must be Username.")
        if not isinstance(self.status, Status):
            raise ValueError("status must be Status.")
        if not isinstance(self.uploaded_at, UploadedAt):
            raise ValueError("uploaded_at must be UploadedAt.")
        if not isinstance(self.registered_at, RegisteredAt):
            raise ValueError("registered_at must be RegisteredAt.")
        if not isinstance(self.video_url, VideoURL):
            raise ValueError("video_url must be VideoURL.")
        if not isinstance(self.mylist_url, MylistURL):
            raise ValueError("mylist_url must be MylistURL.")

        # 行番号は1ベース
        if self.row_number < 1:
            raise ValueError("row_index must be row_index >= 1.")

    @property
    def fields(self) -> list[str]:
        return TableRowTuple._fields

    def keys(self) -> list[str]:
        return self.fields

    def values(self) -> list[Any]:
        return [
            self.row_number,
            self.video_id,
            self.title,
            self.username,
            self.status,
            self.uploaded_at,
            self.registered_at,
            self.video_url,
            self.mylist_url,
        ]

    def clone(self) -> Self:
        return self.create(self.to_row())

    def to_row(self) -> list[str]:
        row = [
            self.row_number,
            self.video_id.id,
            self.title.name,
            self.username.name,
            self.status.value,
            self.uploaded_at.dt_str,
            self.registered_at.dt_str,
            self.video_url.non_query_url,
            self.mylist_url.non_query_url,
        ]
        return list(map(str, row))

    def to_namedtuple(self) -> TableRowTuple:
        return TableRowTuple._make(self.values())

    def to_typed_dict(self) -> dict[str, Any]:
        return self.to_namedtuple()._asdict()

    def to_dict(self) -> dict[str, str]:
        return dict(zip(self.fields, self.to_row()))

    def replace_from_typed_value(self, **kargs: dict[str, Any]) -> Self:
        def type_check(key, value, class_):
            if not isinstance(value, class_):
                raise ValueError(f"{key} must be {class_.__name__}.")

        for key, value in kargs.items():
            match key:
                case "row_index":
                    type_check(key, value, int)
                    kargs[key] = str(value)
                case "video_id":
                    type_check(key, value, Videoid)
                    kargs[key] = str(value.id)
                case "title":
                    type_check(key, value, Title)
                    kargs[key] = str(value.name)
                case "username":
                    type_check(key, value, Username)
                    kargs[key] = str(value.name)
                case "status":
                    type_check(key, value, Status)
                    kargs[key] = str(value.value)
                case "uploaded_at":
                    type_check(key, value, UploadedAt)
                    kargs[key] = str(value.dt_str)
                case "registered_at":
                    type_check(key, value, RegisteredAt)
                    kargs[key] = str(value.dt_str)
                case "video_url":
                    type_check(key, value, VideoURL)
                    kargs[key] = str(value.non_query_url)
                case "mylist_url":
                    type_check(key, value, MylistURL)
                    kargs[key] = str(value.non_query_url)
                case invalid_key:
                    raise ValueError(f"'{invalid_key}' is not TableRow's attribute.")
        return self.replace_from_str(**kargs)

    def replace_from_str(self, **kargs: dict[str, str]) -> Self:
        current_row_dict = self.to_dict()
        new_row_dict = current_row_dict | kargs
        return self.create(list(new_row_dict.values()))

    @classmethod
    def create(cls, row: list[str]) -> Self:
        """テーブル行インスタンスを作成する

        Args:
            row (list[str]): テーブル行を表す文字列リスト

        Raises:
            ValueError: row がlist[str]でない
                        または想定された項目 cls.COLS_NAME と長さが一致しない場合

        Returns:
            Self: テーブル行インスタンス
        """
        if not isinstance(row, list):
            raise ValueError(f"row must be list.")
        if not isinstance(row[0], str | int):
            raise ValueError(f"row_number must be str | int.")
        if not all([isinstance(r, str) for r in row[1:]]):
            raise ValueError(f"all row element exclude row_number must be list[str].")
        if len(cls.COLS_NAME) != len(row):
            raise ValueError(f"row length must be {len(cls.COLS_NAME)}.")

        table_row_tuple = TableRowTuple._make(row)

        mylist_url = MylistURLFactory.create(table_row_tuple.mylist_url)

        return cls(
            int(table_row_tuple.row_index),
            Videoid(table_row_tuple.video_id),
            Title(table_row_tuple.title),
            Username(table_row_tuple.username),
            Status(table_row_tuple.status),
            UploadedAt(table_row_tuple.uploaded_at),
            RegisteredAt(table_row_tuple.registered_at),
            VideoURL.create(table_row_tuple.video_url),
            mylist_url,
        )


if __name__ == "__main__":
    s_row = [
        "1",
        "sm12346578",
        "title_1",
        "username_1",
        "",
        "2023-12-13 07:25:00",
        "2023-12-13 07:25:00",
        "https://www.nicovideo.jp/watch/sm12346578",
        "https://www.nicovideo.jp/user/11111111/video",
    ]
    table_row = TableRow.create(s_row)
    print(table_row)
    table_dict = table_row.to_dict()
    print(table_dict)
    keys = table_row.keys()
    values = table_row.values()
    table_raw_dict = table_row.to_typed_dict()
    print(dict(zip(keys, values)) == table_raw_dict)

    table_row_2 = table_row.clone()
    print(table_row == table_row_2)

    table_row_3 = table_row_2.clone()
    table_row_3.row_number = 100
    print(table_row_3 != table_row_2)
