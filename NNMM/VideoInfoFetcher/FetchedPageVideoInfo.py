# coding: utf-8
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pprint import pprint


@dataclass
class FetchedPageVideoInfo():
    no: list[int]                       # No. [1, ..., len()-1]
    userid: str                         # ユーザーID 1234567
    mylistid: str                       # マイリストID 12345678
    showname: str                       # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
    myshowname: str                     # マイリスト名 「まとめマイリスト」
    mylist_url: str                     # マイリストURL https://www.nicovideo.jp/user/1234567/mylist/12345678
    video_id_list: list[str]            # 動画IDリスト [sm12345678]
    title_list: list[str]               # 動画タイトルリスト [テスト動画]
    registered_at_list: list[str]       # 登録日時リスト [%Y-%m-%d %H:%M:%S]
    video_url_list: list[str]           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]

    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    USERID_PATTERN = r"[0-9]"
    MYLISTID_PATTERN = r"[0-9]"
    VIDEO_ID_PATTERN = r"sm[0-9]"
    VIDEO_URL_PATTERN = r"https://www.nicovideo.jp/watch/sm[0-9]+"

    def __post_init__(self):
        self._is_valid()
        pass

    def _is_valid(self) -> bool | TypeError | ValueError:
        """バリデーション

        Returns:
            bool: すべての値が正常ならTrue, 一つでも不正ならTypeError|ValueError
        """
        if not all([isinstance(self.userid, str),
                    isinstance(self.mylistid, str),
                    isinstance(self.showname, str),
                    isinstance(self.myshowname, str),
                    isinstance(self.mylist_url, str)]):
            raise TypeError("(userid, mylistid, showname, myshowname, mylist_url) must be str.")
        if any([self.userid == "", self.showname == "", self.myshowname == "", self.mylist_url == ""]):
            raise ValueError("(userid, showname, myshowname, mylist_url) must be non-empty str.")

        if not all([isinstance(self.video_id_list, list),
                    isinstance(self.title_list, list),
                    isinstance(self.registered_at_list, list),
                    isinstance(self.video_url_list, list)]):
            raise TypeError("(*_list) must be list[str].")
        num = len(self.no)
        if not all([len(self.video_id_list) == num,
                    len(self.title_list) == num,
                    len(self.registered_at_list) == num,
                    len(self.video_url_list) == num]):
            raise ValueError("There are different size (*_list).")

        if not re.search(FetchedPageVideoInfo.USERID_PATTERN, self.userid):
            raise ValueError(f"userid is invalid, must be {FetchedPageVideoInfo.USERID_PATTERN}.")
        if self.mylistid != "":
            if not re.search(FetchedPageVideoInfo.MYLISTID_PATTERN, self.mylistid):
                raise ValueError(f"mylistid is invalid, must be {FetchedPageVideoInfo.MYLISTID_PATTERN}.")

        zipped_list = zip(self.video_id_list,
                          self.title_list,
                          self.registered_at_list,
                          self.video_url_list)
        for video_id, title, registered_at, video_url in zipped_list:
            if not re.search(FetchedPageVideoInfo.VIDEO_ID_PATTERN, video_id):
                raise ValueError(f"video_id is invalid, must be {FetchedPageVideoInfo.VIDEO_ID_PATTERN}.")
            if title == "":
                raise ValueError(f"title must be non-empty str.")
            # 日付形式が正しく変換されるかチェック
            dt = datetime.strptime(registered_at, FetchedPageVideoInfo.DESTINATION_DATETIME_FORMAT)
            if not re.search(FetchedPageVideoInfo.VIDEO_URL_PATTERN, video_url):
                raise ValueError(f"video_url is invalid, must be {FetchedPageVideoInfo.VIDEO_URL_PATTERN}.")
        return True

    def to_dict(self) -> dict:
        return asdict(self)


if __name__ == "__main__":
    fvi_page = FetchedPageVideoInfo([1], "1234567", "12345678",
                                    "「まとめマイリスト」-shift4869さんのマイリスト", "「まとめマイリスト」",
                                    "https://www.nicovideo.jp/user/1234567/mylist/12345678",
                                    ["sm12345678"], ["テスト動画"], ["2022-05-06 00:01:01"],
                                    ["https://www.nicovideo.jp/watch/sm12345678"])
    pprint(fvi_page.to_dict())
