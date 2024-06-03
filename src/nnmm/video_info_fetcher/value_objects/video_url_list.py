from dataclasses import dataclass
from typing import Iterable

from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.videoid import Videoid


@dataclass(frozen=True)
class VideoURLList(Iterable):
    """動画URLリスト

    動画URLについてはVideoURL を参照
    空リストも許容する

    Raises:
        TypeError: 引数がリストでない場合
        ValueError: 引数のリストの要素が一つでもVideoURL でない場合

    Returns:
        VideoURLList: 動画URLリスト
    """

    _list: list[VideoURL]

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid VideoURLList.")
        if self._list:
            if not all([isinstance(r, VideoURL) for r in self._list]):
                raise ValueError(f"include not VideoURL element, invalid VideoURLList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @property
    def video_id_list(self) -> list[Videoid]:
        """動画IDリストを返す"""
        return [v.video_id for v in self._list]

    @classmethod
    def create(cls, video_url_list: list[VideoURL] | list[str]) -> "VideoURLList":
        """VideoURLList インスタンスを作成する

        Args:
            VideoURL_list (list[VideoURL] | list[str]):
                VideoURL のリスト、文字列リスト
                空リストも許容される

        Raises:
            TypeError: VideoURL_list がリストでない場合
            ValueError: その他インスタンス生成できない型の引数の場合

        Returns:
            VideoURLList: 投稿者名リスト
        """
        if not isinstance(video_url_list, list):
            raise TypeError("Args is not list.")
        if not video_url_list:
            return cls([])
        if isinstance(video_url_list[0], VideoURL):
            return cls(video_url_list)
        if isinstance(video_url_list[0], str):
            return cls([VideoURL.create(r) for r in video_url_list])
        raise ValueError("Create VideoURLList failed.")


if __name__ == "__main__":
    NUM = 5
    base_url = "https://www.nicovideo.jp/watch/sm1000000{}"
    urls = [base_url.format(i) for i in range(1, NUM + 1)]

    video_url_list = VideoURLList.create(urls)
    for v in video_url_list:
        print(v)
    for vid in video_url_list.video_id_list:
        print(vid)
