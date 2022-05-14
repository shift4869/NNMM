# coding: utf-8
from dataclasses import dataclass
from pprint import pprint
from typing import ClassVar

from NNMM.VideoInfoFetcher.RegisteredAt import RegisteredAt
from NNMM.VideoInfoFetcher.Title import Title
from NNMM.VideoInfoFetcher.Videoid import Videoid
from NNMM.VideoInfoFetcher.VideoURL import VideoURL


@dataclass(frozen=True)
class ItemInfo():
    video_id: ClassVar[Videoid]  # 動画ID sm12345678
    title: Title                 # 動画タイトル テスト動画
    registered_at: RegisteredAt  # 登録日時 %Y-%m-%d %H:%M:%S
    video_url: VideoURL          # 動画URL https://www.nicovideo.jp/watch/sm12345678

    def __post_init__(self):
        self._is_valid()
        object.__setattr__(self, "video_id", Videoid(self.video_url.video_id))
        pass

    def _is_valid(self) -> bool | TypeError | ValueError:
        """バリデーション

        Returns:
            bool: すべての値が正常ならTrue, 一つでも不正ならTypeError|ValueError
        """
        return True

    def to_dict(self) -> dict:
        return self.__dict__

    @property
    def result(self) -> dict:
        return self.to_dict()


if __name__ == "__main__":
    title = Title("テスト動画")
    registered_at = RegisteredAt("2022-05-06 00:01:01")
    video_url = VideoURL.create("https://www.nicovideo.jp/watch/sm12345678")

    fvi = ItemInfo(title, registered_at, video_url)
    pprint(fvi.to_dict())
