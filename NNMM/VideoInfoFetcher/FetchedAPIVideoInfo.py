# coding: utf-8
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pprint import pprint


@dataclass
class FetchedAPIVideoInfo():
    no: list[int]                       # No. [1, ..., len()-1]
    video_id_list: list[str]            # 動画IDリスト [sm12345678]
    title_list: list[str]               # 動画タイトルリスト [テスト動画]
    uploaded_at_list: list[str]         # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
    video_url_list: list[str]           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
    username_list: list[str]            # 投稿者リスト [投稿者1]

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    VIDEO_ID_PATTERN = r"sm[0-9]"
    VIDEO_URL_PATTERN = r"https://www.nicovideo.jp/watch/(sm[0-9]+)"

    def __post_init__(self):
        self._is_valid()
        pass

    def _is_valid(self) -> bool | TypeError | ValueError:
        """バリデーション

        Returns:
            bool: すべての値が正常ならTrue, 一つでも不正ならTypeError|ValueError
        """
        if not all([isinstance(self.video_id_list, list),
                    isinstance(self.title_list, list),
                    isinstance(self.uploaded_at_list, list),
                    isinstance(self.video_url_list, list),
                    isinstance(self.username_list, list)]):
            raise TypeError("(*_list) must be list[str].")
        num = len(self.no)
        if not all([len(self.video_id_list) == num,
                    len(self.title_list) == num,
                    len(self.uploaded_at_list) == num,
                    len(self.video_url_list) == num,
                    len(self.username_list) == num]):
            raise ValueError("There are different size (*_list).")

        zipped_list = zip(self.video_id_list,
                          self.title_list,
                          self.uploaded_at_list,
                          self.video_url_list,
                          self.username_list)
        for video_id, title, uploaded_at, video_url, username in zipped_list:
            if not re.search(FetchedAPIVideoInfo.VIDEO_ID_PATTERN, video_id):
                raise ValueError(f"video_id is invalid, must be {FetchedAPIVideoInfo.VIDEO_ID_PATTERN}.")
            if title == "":
                raise ValueError(f"title must be non-empty str.")
            # 日付形式が正しく変換されるかチェック
            dt = datetime.strptime(uploaded_at, FetchedAPIVideoInfo.DESTINATION_DATETIME_FORMAT)
            if not re.search(FetchedAPIVideoInfo.VIDEO_URL_PATTERN, video_url):
                raise ValueError(f"video_url is invalid, must be {FetchedAPIVideoInfo.VIDEO_URL_PATTERN}.")
            if username == "":
                raise ValueError(f"username must be non-empty str.")
        return True

    def to_dict(self) -> dict:
        return asdict(self)


if __name__ == "__main__":
    fvi_api = FetchedAPIVideoInfo([1], ["sm12345678"], ["テスト動画"], ["2022-05-06 00:00:01"],
                                  ["https://www.nicovideo.jp/watch/sm12345678"], ["投稿者1"])
    pprint(fvi_api.to_dict())
