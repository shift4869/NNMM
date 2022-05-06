# coding: utf-8
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pprint import pprint
from typing import ClassVar

from NNMM.VideoInfoFetcher.FetchedAPIVideoInfo import FetchedAPIVideoInfo
from NNMM.VideoInfoFetcher.FetchedPageVideoInfo import FetchedPageVideoInfo


@dataclass
class FetchedVideoInfo():
    # table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    # table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
    no: list[int]                       # No. [1, ..., len()-1]
    userid: str                         # ユーザーID 1234567
    mylistid: str                       # マイリストID 12345678
    showname: str                       # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
    myshowname: str                     # マイリスト名 「まとめマイリスト」
    mylist_url: str                     # マイリストURL https://www.nicovideo.jp/user/1234567/mylist/12345678
    video_id_list: list[str]            # 動画IDリスト [sm12345678]
    title_list: list[str]               # 動画タイトルリスト [テスト動画]
    uploaded_at_list: list[str]         # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
    registered_at_list: list[str]       # 登録日時リスト [%Y-%m-%d %H:%M:%S]
    video_url_list: list[str]           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
    username_list: list[str]            # 投稿者リスト [投稿者1]
    result_dict: ClassVar[list[dict]]   # 結果の辞書 [{key=RESULT_DICT_COLS, value=キーに対応する上記項目}]

    RESULT_DICT_COLS = ("no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname")
    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    USERID_PATTERN = r"[0-9]"
    MYLISTID_PATTERN = r"[0-9]"
    VIDEO_ID_PATTERN = r"sm[0-9]"
    VIDEO_URL_PATTERN = r"https://www.nicovideo.jp/watch/sm[0-9]+"

    def __post_init__(self):
        self._is_valid()

        # result_dictを作成する
        self.result_dict = self._make_result_dict()
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
                    isinstance(self.uploaded_at_list, list),
                    isinstance(self.registered_at_list, list),
                    isinstance(self.video_url_list, list),
                    isinstance(self.username_list, list)]):
            raise TypeError("(*_list) must be list[str].")
        num = len(self.no)
        if not all([len(self.video_id_list) == num,
                    len(self.title_list) == num,
                    len(self.uploaded_at_list) == num,
                    len(self.registered_at_list) == num,
                    len(self.video_url_list) == num,
                    len(self.username_list) == num]):
            raise ValueError("There are different size (*_list).")

        if not re.search(FetchedVideoInfo.USERID_PATTERN, self.userid):
            raise ValueError(f"userid is invalid, must be {FetchedVideoInfo.USERID_PATTERN}.")
        if self.mylistid != "":
            if not re.search(FetchedVideoInfo.MYLISTID_PATTERN, self.mylistid):
                raise ValueError(f"mylistid is invalid, must be {FetchedVideoInfo.MYLISTID_PATTERN}.")

        zipped_list = zip(self.video_id_list,
                          self.title_list,
                          self.uploaded_at_list,
                          self.registered_at_list,
                          self.video_url_list,
                          self.username_list)
        for video_id, title, uploaded_at, registered_at, video_url, username in zipped_list:
            if not re.search(FetchedVideoInfo.VIDEO_ID_PATTERN, video_id):
                raise ValueError(f"video_id is invalid, must be {FetchedVideoInfo.VIDEO_ID_PATTERN}.")
            if title == "":
                raise ValueError(f"title must be non-empty str.")
            # 日付形式が正しく変換されるかチェック
            dt = datetime.strptime(uploaded_at, FetchedVideoInfo.DESTINATION_DATETIME_FORMAT)
            dt = datetime.strptime(registered_at, FetchedVideoInfo.DESTINATION_DATETIME_FORMAT)
            if not re.search(FetchedVideoInfo.VIDEO_URL_PATTERN, video_url):
                raise ValueError(f"video_url is invalid, must be {FetchedVideoInfo.VIDEO_URL_PATTERN}.")
            if username == "":
                raise ValueError(f"username must be non-empty str.")
        return True

    def _make_result_dict(self) -> list[dict]:
        """結果の辞書を返す

        Notes:
            結果の辞書 [{key=RESULT_DICT_COLS, value=キーに対応する項目}]

        Returns:
            list[dict]: 結果の辞書のリスト
        """
        # 結合
        res = []
        now_date = datetime.now()
        zipped_list = zip(self.no,
                          self.video_id_list,
                          self.title_list,
                          self.uploaded_at_list,
                          self.registered_at_list,
                          self.username_list,
                          self.video_url_list)
        for no, video_id, title, uploaded_at, registered_at, username, video_url in zipped_list:
            # 登録日時が未来日の場合、登録しない（投稿予約など）
            if now_date < datetime.strptime(registered_at, FetchedVideoInfo.DESTINATION_DATETIME_FORMAT):
                continue

            # 出力インターフェイスチェック
            value_list = [no, video_id, title, username, "", uploaded_at, registered_at, video_url, self.mylist_url, self.showname, self.myshowname]
            if len(FetchedVideoInfo.RESULT_DICT_COLS) != len(value_list):
                continue

            # 登録
            res.append(dict(zip(FetchedVideoInfo.RESULT_DICT_COLS, value_list)))

        # 重複削除
        seen = []
        res = [x for x in res if x["video_id"] not in seen and not seen.append(x["video_id"])]

        return res

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def result(self) -> dict:
        return self.result_dict

    @classmethod
    def merge(cls, fvi_page: "FetchedPageVideoInfo", fvi_api: "FetchedAPIVideoInfo") -> "FetchedVideoInfo":
        d = dict(fvi_page.to_dict(), **fvi_api.to_dict())
        return FetchedVideoInfo(**d)


if __name__ == "__main__":
    fvi = FetchedVideoInfo([1], "1234567", "12345678",
                           "「まとめマイリスト」-shift4869さんのマイリスト", "「まとめマイリスト」",
                           "https://www.nicovideo.jp/user/1234567/mylist/12345678",
                           ["sm12345678"], ["テスト動画"], ["2022-05-06 00:00:01"], ["2022-05-06 00:01:01"],
                           ["https://www.nicovideo.jp/watch/sm12345678"], ["投稿者1"])
    # pprint(fvi.to_dict())
    fvi_page = FetchedPageVideoInfo([1], "1234567", "12345678",
                                    "「まとめマイリスト」-shift4869さんのマイリスト", "「まとめマイリスト」",
                                    "https://www.nicovideo.jp/user/1234567/mylist/12345678",
                                    ["sm12345678"], ["テスト動画"], ["2022-05-06 00:01:01"],
                                    ["https://www.nicovideo.jp/watch/sm12345678"])
    fvi_api = FetchedAPIVideoInfo([1], ["sm12345678"], ["テスト動画"], ["2022-05-06 00:00:01"],
                                  ["https://www.nicovideo.jp/watch/sm12345678"], ["投稿者1"])
    fvi_d = FetchedVideoInfo.merge(fvi_page, fvi_api)
    print(fvi == fvi_d)
    pprint(fvi.result)
