# coding: utf-8
from dataclasses import dataclass
from pprint import pprint

from NNMM.VideoInfoFetcher.TitleList import TitleList
from NNMM.VideoInfoFetcher.UploadedAtList import UploadedAtList
from NNMM.VideoInfoFetcher.UsernameList import UsernameList
from NNMM.VideoInfoFetcher.VideoidList import VideoidList
from NNMM.VideoInfoFetcher.VideoURLList import VideoURLList


@dataclass(frozen=True)
class FetchedAPIVideoInfo():
    no: list[int]                     # No. [1, ..., len()-1]
    video_id_list: VideoidList        # 動画IDリスト [sm12345678]
    title_list: TitleList             # 動画タイトルリスト [テスト動画]
    uploaded_at_list: UploadedAtList  # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
    video_url_list: VideoURLList      # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
    username_list: UsernameList       # 投稿者リスト [投稿者1]

    def __post_init__(self):
        self._is_valid()
        pass

    def _is_valid(self) -> bool | TypeError | ValueError:
        """バリデーション

        Returns:
            bool: すべての値が正常ならTrue, 一つでも不正ならTypeError|ValueError
        """
        if not isinstance(self.video_id_list, VideoidList):
            raise TypeError("video_id_list must be VideoidList.")
        if not isinstance(self.title_list, TitleList):
            raise TypeError("title_list must be TitleList.")
        if not isinstance(self.uploaded_at_list, UploadedAtList):
            raise TypeError("uploaded_at_list must be UploadedAtList.")
        if not isinstance(self.video_url_list, VideoURLList):
            raise TypeError("video_url_list must be VideoURLList.")
        if not isinstance(self.username_list, UsernameList):
            raise TypeError("username_list must be UsernameList.")

        num = len(self.no)
        if not all([len(self.video_id_list) == num,
                    len(self.title_list) == num,
                    len(self.uploaded_at_list) == num,
                    len(self.video_url_list) == num,
                    len(self.username_list) == num]):
            raise ValueError("There are different size (*_list).")
        return True

    def to_dict(self) -> dict:
        # return asdict(self)  # asdictだとキーと値が文字列になるため型情報が失われる
        return self.__dict__


if __name__ == "__main__":
    title_list = TitleList.create(["テスト動画"])
    uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
    video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
    video_id_list = VideoidList.create(video_url_list.video_id_list)
    username_list = UsernameList.create(["投稿者1"])
    no = list(range(1, len(video_id_list) + 1))

    fvi_api = FetchedAPIVideoInfo([1], video_id_list, title_list, uploaded_at_list,
                                  video_url_list, username_list)
    pprint(fvi_api.to_dict())
