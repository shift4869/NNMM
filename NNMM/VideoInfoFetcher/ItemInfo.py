# coding: utf-8
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pprint import pprint


@dataclass
class ItemInfo():
    video_id: str            # 動画ID sm12345678
    title: str               # 動画タイトル テスト動画
    registered_at: str       # 登録日時 %Y-%m-%d %H:%M:%S
    video_url: str           # 動画URL https://www.nicovideo.jp/watch/sm12345678

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    VIDEO_ID_PATTERN = r"sm[0-9]"
    VIDEO_URL_PATTERN = r"https://www.nicovideo.jp/watch/(sm[0-9]+)"

    def __post_init__(self):
        self._is_valid()
        pass

    def _is_valid(self) -> bool | TypeError | ValueError:
        """バリデーション

        Returns:
            bool: すべての値が正常ならTrue, 一つでも不正ならTypeError|ValueError
        """
        if not all([isinstance(self.video_id, str),
                    isinstance(self.title, str),
                    isinstance(self.registered_at, str),
                    isinstance(self.video_url, str)]):
            raise TypeError("(video_id, title, registered_at, video_url) must be str.")
        if any([self.video_id == "", self.title == "", self.registered_at == "", self.video_url == ""]):
            raise ValueError("(video_id, title, registered_at, video_url) must be non-empty str.")

        if not re.search(ItemInfo.VIDEO_ID_PATTERN, self.video_id):
            raise ValueError(f"video_id is invalid, must be {ItemInfo.VIDEO_ID_PATTERN}.")
        # 日付形式が正しく変換されるかチェック
        dt = datetime.strptime(self.registered_at, ItemInfo.DESTINATION_DATETIME_FORMAT)
        if not re.search(ItemInfo.VIDEO_URL_PATTERN, self.video_url):
            raise ValueError(f"video_url is invalid, must be {ItemInfo.VIDEO_URL_PATTERN}.")
        return True

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def result(self) -> dict:
        return self.to_dict()


if __name__ == "__main__":
    fvi = ItemInfo("sm12345678", "テスト動画", "2022-05-06 00:01:01",
                   "https://www.nicovideo.jp/watch/sm12345678")
    pprint(fvi.to_dict())
