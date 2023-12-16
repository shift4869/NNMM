from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class UploadedAt():
    """投稿日時

    Notes:
        投稿日時はある動画が実際に登録された日時を表す
            投稿動画ページの場合、登録日時とほぼ一致する（投稿日時 = 登録日時）
            マイリストページの場合、投稿日時と登録日時は離れているかもしれない（投稿日時 <= 登録日時）
        基本的に投稿日時より登録日時の方が未来となる

    Raises:
        TypeError: 引数が文字列でない場合
        ValueError: 引数がDESTINATION_DATETIME_FORMAT パターンでない場合

    Returns:
        UploadedAt: 投稿日時
    """
    _datetime: str  # 投稿日時 %Y-%m-%d %H:%M:%S

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self) -> None:
        """初期化後処理

        Notes:
            バリデーションのみ
        """
        if not isinstance(self._datetime, str):
            raise TypeError("id is not string, invalid UploadedAt.")

        # 扱える日付形式かどうか変換してみて確かめる
        # 不正な文字列の場合はValueError が送出される
        _ = datetime.strptime(self._datetime, self.DESTINATION_DATETIME_FORMAT)

    @property
    def dt_str(self) -> str:
        """保持している投稿日時を返す
        """
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
