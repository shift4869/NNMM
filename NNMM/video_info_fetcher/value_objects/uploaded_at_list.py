from dataclasses import dataclass
from typing import Iterable

from NNMM.video_info_fetcher.value_objects.uploaded_at import UploadedAt


@dataclass(frozen=True)
class UploadedAtList(Iterable):
    """投稿日時リスト

    投稿日時についてはUploadedAt を参照
    空リストも許容する

    Raises:
        TypeError: 引数がリストでない場合
        ValueError: 引数のリストの要素が一つでもUploadedAt でない場合

    Returns:
        UploadedAtList: 投稿日時リスト
    """
    _list: list[UploadedAt]

    DESTINATION_DATETIME_FORMAT = UploadedAt.DESTINATION_DATETIME_FORMAT

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid UploadedAtList.")
        if self._list:
            if not all([isinstance(r, UploadedAt) for r in self._list]):
                raise ValueError(f"include not UploadedAt element, invalid UploadedAtList")

    def __iter__(self) -> Iterable[UploadedAt]:
        return self._list.__iter__()

    def __len__(self) -> int:
        return self._list.__len__()

    @classmethod
    def create(cls, uploaded_at_list: list[UploadedAt] | list[str]) -> "UploadedAtList":
        """UploadedAtList インスタンスを作成する

        Args:
            uploaded_at_list (list[UploadedAt] | list[str]):
                UploadedAt のリスト、またはDESTINATION_DATETIME_FORMAT パターンの文字列リスト
                空リストも許容される

        Raises:
            TypeError: uploaded_at_list がリストでない場合
            ValueError: その他インスタンス生成できない型の引数の場合

        Returns:
            UploadedAtList: 投稿日時リスト
        """
        if not isinstance(uploaded_at_list, list):
            raise TypeError("Args is not list.")
        if not uploaded_at_list:
            return cls([])
        if isinstance(uploaded_at_list[0], UploadedAt):
            return cls(uploaded_at_list)
        if isinstance(uploaded_at_list[0], str):
            return cls([UploadedAt(r) for r in uploaded_at_list])
        raise ValueError("Create UploadedAtList failed.")


if __name__ == "__main__":
    NUM = 5
    base_dt_str = "2022-05-12 00:01:0{}"
    uploaded_ats = [base_dt_str.format(i) for i in range(1, NUM + 1)]

    uploaded_at_list = UploadedAtList.create(uploaded_ats)
    for dt_str in uploaded_at_list:
        print(dt_str)

    uploaded_ats = [UploadedAt(r) for r in uploaded_ats]
    uploaded_at_list = UploadedAtList.create(uploaded_ats)
    for dt_str in uploaded_at_list:
        print(dt_str)

    uploaded_at_list = UploadedAtList.create([])
    print(len(uploaded_at_list))
