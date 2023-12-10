from dataclasses import dataclass
from typing import Iterable

from NNMM.video_info_fetcher.value_objects.title import Title


@dataclass(frozen=True)
class TitleList(Iterable):
    """動画タイトルリスト

    動画タイトルについてはTitle を参照
    空リストも許容する

    Raises:
        TypeError: 引数がリストでない場合
        ValueError: 引数のリストの要素が一つでもTitle でない場合

    Returns:
        TitleList: 動画タイトルリスト
    """
    _list: list[Title]

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid TitleList.")
        if self._list:
            if not all([isinstance(r, Title) for r in self._list]):
                raise ValueError(f"include not Title element, invalid TitleList")

    def __iter__(self) -> Iterable[Title]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    @classmethod
    def create(cls, title_list: list[Title] | list[str]) -> "TitleList":
        """TitleList インスタンスを作成する

        Args:
            title_list (list[Title] | list[str]):
                Title のリスト、文字列リスト
                空リストも許容される

        Raises:
            TypeError: title_list がリストでない場合
            ValueError: その他インスタンス生成できない型の引数の場合

        Returns:
            TitleList: 動画タイトルリスト
        """
        if not isinstance(title_list, list):
            raise TypeError("Args is not list.")
        if not title_list:
            return cls([])
        if isinstance(title_list[0], Title):
            return cls(title_list)
        if isinstance(title_list[0], str):
            return cls([Title(r) for r in title_list])
        raise ValueError("Create TitleList failed.")


if __name__ == "__main__":
    NUM = 5
    base_title = "動画タイトル{}"
    titles = [base_title.format(i) for i in range(1, NUM + 1)]

    title_list = TitleList.create([])
    title_list = TitleList.create(titles)
    for t in title_list:
        print(t)
