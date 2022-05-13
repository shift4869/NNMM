# coding: utf-8
from dataclasses import dataclass, asdict
from pprint import pprint

from NNMM.VideoInfoFetcher import *


@dataclass
class FetchedPageVideoInfo():
    no: list[int]                         # No. [1, ..., len()-1]
    userid: Userid                        # ユーザーID 1234567
    mylistid: Mylistid                    # マイリストID 12345678
    showname: Showname                    # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
    myshowname: Myshowname                # マイリスト名 「まとめマイリスト」
    mylist_url: UploadedURL | MylistURL   # マイリストURL https://www.nicovideo.jp/user/1234567/mylist/12345678
    video_id_list: VideoidList            # 動画IDリスト [sm12345678]
    title_list: TitleList                 # 動画タイトルリスト [テスト動画]
    registered_at_list: RegisteredAtList  # 登録日時リスト [%Y-%m-%d %H:%M:%S]
    video_url_list: VideoURLList          # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]

    def __post_init__(self):
        self._is_valid()
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
        if not isinstance(self.registered_at_list, RegisteredAtList):
            raise TypeError("registered_at_list must be RegisteredAtList.")
        if not isinstance(self.video_url_list, VideoURLList):
            raise TypeError("video_url_list must be VideoURLList.")

        num = len(self.no)
        if not all([len(self.video_id_list) == num,
                    len(self.title_list) == num,
                    len(self.registered_at_list) == num,
                    len(self.video_url_list) == num]):
            raise ValueError("There are different size (*_list).")
        return True

    def to_dict(self) -> dict:
        # return asdict(self)  # asdictだとキーと値が文字列になるため型情報が失われる
        return self.__dict__


if __name__ == "__main__":
    userid = Userid("1234567")
    mylistid = Mylistid("12345678")
    showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
    myshowname = Myshowname("「まとめマイリスト」")
    mylist_url = MylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
    video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
    video_id_list = VideoidList.create(video_url_list.video_id_list)
    title_list = TitleList.create(["テスト動画"])
    registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
    no = list(range(1, len(video_id_list) + 1))

    fvi_page = FetchedPageVideoInfo([1], userid, mylistid, showname, myshowname, mylist_url,
                                    video_id_list, title_list, registered_at_list, video_url_list)
    pprint(fvi_page.to_dict())
