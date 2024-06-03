from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreatedAt:
    """作成日時

    作成日時はマイリストがDBに最初に登録された日時を表す
    基本的に更新日時や確認日時より過去日となる

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数がDESTINATION_DATETIME_FORMAT パターンでない場合

    Returns:
        CreatedAt: 作成日時
    """

    _datetime: str

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self) -> None:
        if not isinstance(self._datetime, str):
            raise TypeError("id is not string, invalid CreatedAt.")

        # 扱える日付形式かどうか変換してみて確かめる
        # 不正な文字列の場合はValueError が送出される
        _ = datetime.strptime(self._datetime, self.DESTINATION_DATETIME_FORMAT)

    @property
    def dt_str(self) -> str:
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
            created_at = CreatedAt(dt_str)
            print(created_at.dt_str)
        except (ValueError, TypeError) as e:
            print(e.args[0])
