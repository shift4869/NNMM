from dataclasses import dataclass
from typing import Iterator, Self

from NNMM.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from NNMM.process.update_mylist.value_objects.payload import Payload
from NNMM.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


@dataclass(frozen=True)
class PayloadList:
    """fetcher から database_updater へ受け渡すデータのペイロード のリスト

    構造は以下の通り
    _list[(
        MylistWithVideoList
            TypedMylist: 特定のマイリスト
            TypedVideoList: ↑のマイリストに紐づく動画情報（更新前）
        FetchedVideoInfo:  ↑のマイリストをもとにfetchしてきた動画情報（更新先候補）
    )]
    """

    _list: list[Payload]

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise ValueError("_list must be list.")
        if not all([isinstance(m, Payload) for m in self._list]):
            raise ValueError("_list element must be Payload.")

    def __iter__(self) -> Iterator[Payload]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    def __getitem__(self, item) -> Payload:
        return self._list.__getitem__(item)

    @classmethod
    def create(cls, payload_tuple_list: list[tuple[MylistWithVideoList, FetchedVideoInfo | None]]) -> Self:
        """fetcher から database_updater へ受け渡すデータのペイロード のリストを作成する

        Args:
            payload_tuple_list (list[tuple[MylistWithVideoList, FetchedVideoInfo  |  None]]):
                マイリストとそれに紐づく動画情報と、fetchしてきたFetchedVideoInfo のタプル のリスト
                fetch に失敗するなどした場合は Noneで渡ってくる

        Returns:
            Self: PayloadList インスタンス
        """
        return cls([
            Payload.create(mylist_with_videolist, fetched_info)
            for mylist_with_videolist, fetched_info in payload_tuple_list
        ])


if __name__ == "__main__":
    pass
