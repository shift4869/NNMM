# coding: utf-8
from datetime import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class UploadedAt():
    _datetime: str  # 投稿日時 %Y-%m-%d %H:%M:%S

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self) -> None:
        if not isinstance(self._datetime, str):
            raise TypeError("id is not string, invalid UploadedAt.")

        # 扱える日付形式かどうか変換してみて確かめる
        # 不正な文字列の場合はValueError が送出される
        _ = datetime.strptime(self._datetime, self.DESTINATION_DATETIME_FORMAT)

    @property
    def dt_str(self):
        return self._datetime


if __name__ == "__main__":
    dt_list = [
        "2022-05-12 00:01:00",
        "nm12346578",
        "",
        -1,
    ]

    for dt_str in dt_list:
        try:
            uploaded_at = UploadedAt(dt_str)
            print(uploaded_at.dt_str)
        except (ValueError, TypeError) as e:
            print(e.args[0])
