from dataclasses import dataclass
from typing import Self

from NNMM.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from NNMM.process.update_mylist.value_objects.typed_mylist import TypedMylist
from NNMM.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from NNMM.util import Result
from NNMM.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


@dataclass(frozen=True)
class Payload:
    _mylist_with_video: MylistWithVideo
    _fetched_info: FetchedVideoInfo | Result

    def __init__(self, mylist_with_video: MylistWithVideo, fetched_info: FetchedVideoInfo | Result) -> None:
        """fetcher から database_updater へ受け渡すデータのペイロード を作成する

        Args:
            mylist_with_video (MylistWithVideo): マイリストとそのマイリストに紐づく動画情報
            fetched_info (FetchedVideoInfo | Result): fetch してきたデータ, fetch 失敗時は Result.failed が渡ってくる

        Raises:
            ValueError: 引数の型が不正な場合

        Returns:
            Self: Payload インスタンス
        """
        # マイリストと動画情報については型チェックのみ
        if not isinstance(mylist_with_video, MylistWithVideo):
            raise ValueError("mylist_with_video must be MylistWithVideo.")
        object.__setattr__(self, "_mylist_with_video", mylist_with_video)

        # fetched データについては Result.failed も許容する
        if not isinstance(fetched_info, FetchedVideoInfo | Result):
            raise ValueError("fetched_info must be FetchedVideoInfo | Result.")

        if isinstance(fetched_info, FetchedVideoInfo):
            # fetched データが真に FetchedVideoInfo ならば fetch 成功
            object.__setattr__(self, "_fetched_info", fetched_info)
        elif isinstance(fetched_info, Result) and fetched_info == Result.failed:
            # fetched データが Result.failed ならば fetch 失敗
            # Result.failed を格納しておき、updater 内で判定する
            object.__setattr__(self, "_fetched_info", Result.failed)
        else:
            raise ValueError("fetched_info is invalid, must be FetchedVideoInfo | Result.failed.")

    @property
    def mylist_with_video(self) -> MylistWithVideo:
        return self._mylist_with_video

    @property
    def mylist(self) -> TypedMylist:
        return self._mylist_with_video.mylist

    @property
    def video_list(self) -> TypedVideoList:
        return self._mylist_with_video.video_list

    @property
    def fetched_info(self) -> FetchedVideoInfo:
        return self._fetched_info

    @classmethod
    def create(cls, mylist_with_video: MylistWithVideo, fetched_info: FetchedVideoInfo | None) -> Self:
        """fetcher から database_updater へ受け渡すデータのペイロード を作成する

        Args:
            mylist_with_video (MylistWithVideo): マイリストとそのマイリストに紐づく動画情報
            fetched_info (FetchedVideoInfo | None): fetch してきたデータ, fetch 失敗時はNoneが渡ってくる

        Returns:
            Self: Payload
        """
        return cls(mylist_with_video, fetched_info)


if __name__ == "__main__":
    pass
