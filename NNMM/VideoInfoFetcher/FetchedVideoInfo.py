# coding: utf-8
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pprint import pprint
from typing import ClassVar

from NNMM.VideoInfoFetcher import *


@dataclass
class FetchedVideoInfo():
    # table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    # table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
    no: list[int]                         # No. [1, ..., len()-1]
    userid: Userid                        # ユーザーID 1234567
    mylistid: Mylistid                    # マイリストID 12345678
    showname: Showname                    # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
    myshowname: Myshowname                # マイリスト名 「まとめマイリスト」
    mylist_url: UploadedURL | MylistURL   # マイリストURL https://www.nicovideo.jp/user/1234567/mylist/12345678
    video_id_list: VideoidList            # 動画IDリスト [sm12345678]
    title_list: TitleList                 # 動画タイトルリスト [テスト動画]
    uploaded_at_list: UploadedAtList      # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
    registered_at_list: RegisteredAtList  # 登録日時リスト [%Y-%m-%d %H:%M:%S]
    video_url_list: VideoURLList          # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
    username_list: UsernameList           # 投稿者リスト [投稿者1]

    result_dict: ClassVar[list[dict]]   # 結果の辞書 [{key=RESULT_DICT_COLS, value=キーに対応する上記項目}]

    RESULT_DICT_COLS = ("no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname")

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
        if not isinstance(self.userid, Userid):
            raise TypeError("userid must be Userid.")
        if not isinstance(self.mylistid, Mylistid):
            raise TypeError("mylistid must be Mylistid.")
        if not isinstance(self.showname, Showname):
            raise TypeError("showname must be Showname.")
        if not isinstance(self.myshowname, Myshowname):
            raise TypeError("myshowname must be Myshowname.")

        if not (isinstance(self.mylist_url, MylistURL) or isinstance(self.mylist_url, UploadedURL)):
            raise TypeError("mylist_url must be MylistURL|UploadedURL.")

        if not isinstance(self.video_id_list, VideoidList):
            raise TypeError("video_id_list must be VideoidList.")
        if not isinstance(self.title_list, TitleList):
            raise TypeError("title_list must be TitleList.")
        if not isinstance(self.uploaded_at_list, UploadedAtList):
            raise TypeError("uploaded_at_list must be UploadedAtList.")
        if not isinstance(self.registered_at_list, RegisteredAtList):
            raise TypeError("registered_at_list must be RegisteredAtList.")
        if not isinstance(self.video_url_list, VideoURLList):
            raise TypeError("video_url_list must be VideoURLList.")
        if not isinstance(self.username_list, UsernameList):
            raise TypeError("username_list must be UsernameList.")

        num = len(self.no)
        if not all([len(self.video_id_list) == num,
                    len(self.title_list) == num,
                    len(self.uploaded_at_list) == num,
                    len(self.registered_at_list) == num,
                    len(self.video_url_list) == num,
                    len(self.username_list) == num]):
            raise ValueError("There are different size (*_list).")

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
            if now_date < datetime.strptime(registered_at.dt_str, RegisteredAtList.DESTINATION_DATETIME_FORMAT):
                continue

            # 出力インターフェイスチェック
            value_list = [no,
                          video_id.id,
                          title.name,
                          username.name,
                          "",
                          uploaded_at.dt_str,
                          registered_at.dt_str,
                          video_url.video_url,
                          self.mylist_url.mylist_url,
                          self.showname.name,
                          self.myshowname.name]
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
    from NNMM.VideoInfoFetcher.FetchedAPIVideoInfo import FetchedAPIVideoInfo
    from NNMM.VideoInfoFetcher.FetchedPageVideoInfo import FetchedPageVideoInfo

    userid = Userid("1234567")
    mylistid = Mylistid("12345678")
    showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
    myshowname = Myshowname("「まとめマイリスト」")
    mylist_url = MylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
    title_list = TitleList.create(["テスト動画"])
    uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
    registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
    video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
    video_id_list = VideoidList.create(video_url_list.video_id_list)
    username_list = UsernameList.create(["投稿者1"])
    no = list(range(1, len(video_id_list) + 1))

    fvi = FetchedVideoInfo([1], userid, mylistid,
                           showname, myshowname,
                           mylist_url,
                           video_id_list, title_list, uploaded_at_list, registered_at_list,
                           video_url_list, username_list)
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
