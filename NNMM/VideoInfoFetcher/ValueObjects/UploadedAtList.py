# coding: utf-8
from dataclasses import dataclass
from typing import Iterable

from NNMM.VideoInfoFetcher.ValueObjects.UploadedAt import UploadedAt


@dataclass(frozen=True)
class UploadedAtList(Iterable):
    _list: list[UploadedAt]

    DESTINATION_DATETIME_FORMAT = UploadedAt.DESTINATION_DATETIME_FORMAT

    def __post_init__(self) -> None:
        if not isinstance(self._list, list):
            raise TypeError("list is not list[], invalid UploadedAtList.")
        if self._list:
            if not all([isinstance(r, UploadedAt) for r in self._list]):
                raise ValueError(f"include not UploadedAt element, invalid UploadedAtList")

    def __iter__(self):
        return self._list.__iter__()

    def __len__(self):
        return self._list.__len__()

    @classmethod
    def create(cls, uploaded_at_list: list[UploadedAt] | list[str]) -> "UploadedAtList":
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
