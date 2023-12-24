from dataclasses import dataclass
from typing import Iterable

from NNMM.video_info_fetcher.value_objects.videoid import Videoid


@dataclass(frozen=True)
class VideoidList(Iterable):
    """動画IDリスト

    動画IDについてはVideoid を参照
    空リストも許容する

    Raises:
        TypeError: 引数がリストでない場合
        ValueError: 引数のリストの要素が一つでもVideoid でない場合

    Returns:
        VideoidList: 動画IDリスト
    """

    _list: list[Videoid]

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid VideoidList.")
        if self._list:
            if not all([isinstance(r, Videoid) for r in self._list]):
                raise ValueError(f"include not Videoid element, invalid VideoidList")

    def __iter__(self) -> Iterable[Videoid]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    @classmethod
    def create(cls, video_id_list: list[Videoid] | list[str]) -> "VideoidList":
        """VideoidList インスタンスを作成する

        Args:
            Videoid_list (list[Videoid] | list[str]):
                Videoid のリスト、文字列リスト
                空リストも許容される

        Raises:
            TypeError: Videoid_list がリストでない場合
            ValueError: その他インスタンス生成できない型の引数の場合

        Returns:
            VideoidList: 動画IDリスト
        """
        if not isinstance(video_id_list, list):
            raise TypeError("Args is not list.")
        if not video_id_list:
            return cls([])
        if isinstance(video_id_list[0], Videoid):
            return cls(video_id_list)
        if isinstance(video_id_list[0], str):
            return cls([Videoid(r) for r in video_id_list])
        raise ValueError("Create VideoidList failed.")


if __name__ == "__main__":
    NUM = 5
    base_id_str = "sm1000000{}"
    video_id_strs = [base_id_str.format(i) for i in range(1, NUM + 1)]

    video_id_list = VideoidList.create(video_id_strs)
    for v in video_id_list:
        print(v)
