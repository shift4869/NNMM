from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CheckedAt():
    """確認日時

    確認日時はマイリストの更新を確認した日時を表す
        具体的には直近の（オート）リロード日時を表す
    基本的に作成日より未来かつ、確認日時と同値か未来となる

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数がDESTINATION_DATETIME_FORMAT パターンでない場合

    Returns:
        CheckedAt: 作成日時
    """
    _datetime: str

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self) -> None:
        if not isinstance(self._datetime, str):
            raise TypeError("id is not string, invalid CheckedAt.")

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
            checked_at = CheckedAt(dt_str)
            print(checked_at.dt_str)
        except (ValueError, TypeError) as e:
            print(e.args[0])
