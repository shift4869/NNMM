# coding: utf-8
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pprint import pprint

from NNMM.VideoInfoFetcher.VideoURL import VideoURL


@dataclass
class ItemInfo():
    # video_id: str            # 動画ID sm12345678
    title: str               # 動画タイトル テスト動画
    registered_at: str       # 登録日時 %Y-%m-%d %H:%M:%S
    _video_url: VideoURL      # 動画URL https://www.nicovideo.jp/watch/sm12345678

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __post_init__(self):
        self._is_valid()
        pass

    def _is_valid(self) -> bool | TypeError | ValueError:
        """バリデーション

        Returns:
            bool: すべての値が正常ならTrue, 一つでも不正ならTypeError|ValueError
        """
        if not all([isinstance(self.title, str),
                    isinstance(self.registered_at, str)]):
            raise TypeError("(title, registered_at) must be str.")
        if any([self.title == "", self.registered_at == ""]):
            raise ValueError("(title, registered_at) must be non-empty str.")

        # 日付形式が正しく変換されるかチェック
        dt = datetime.strptime(self.registered_at, ItemInfo.DESTINATION_DATETIME_FORMAT)
        return True

    def to_dict(self) -> dict:
        res = asdict(self)
        res["video_url"] = self.video_url
        res["video_id"] = self.video_id
        del res["_video_url"]
        return res

    @property
    def video_url(self) -> dict:
        return self._video_url.video_url

    @property
    def video_id(self) -> dict:
        return self._video_url.video_id

    @property
    def result(self) -> dict:
        return self.to_dict()


if __name__ == "__main__":
    fvi = ItemInfo("テスト動画", "2022-05-06 00:01:01",
                   VideoURL.create("https://www.nicovideo.jp/watch/sm12345678"))
    pprint(fvi.to_dict())
