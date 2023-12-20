from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UpdatedAt():
    """更新日時

    更新日時はマイリストを更新した日時を表す
        "マイリストの更新"は「そのマイリストに含まれている
        Video情報が1つでも追加/更新されたとき」と定義する
    基本的に作成日より未来かつ、確認日時と同値か過去となる

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数がDESTINATION_DATETIME_FORMAT パターンでない場合

    Returns:
        UpdatedAt: 作成日時
    """
    _datetime: str

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self) -> None:
        if not isinstance(self._datetime, str):
            raise TypeError("id is not string, invalid UpdatedAt.")

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
            updated_at = UpdatedAt(dt_str)
            print(updated_at.dt_str)
        except (ValueError, TypeError) as e:
            print(e.args[0])
