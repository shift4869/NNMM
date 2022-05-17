# coding: utf-8
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint
from typing import ClassVar

from NNMM.VideoInfoFetcher.ValueObjects.Mylistid import Mylistid
from NNMM.VideoInfoFetcher.ValueObjects.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.ValueObjects.Myshowname import Myshowname
from NNMM.VideoInfoFetcher.ValueObjects.RegisteredAtList import RegisteredAtList
from NNMM.VideoInfoFetcher.ValueObjects.Showname import Showname
from NNMM.VideoInfoFetcher.ValueObjects.TitleList import TitleList
from NNMM.VideoInfoFetcher.ValueObjects.UploadedAtList import UploadedAtList
from NNMM.VideoInfoFetcher.ValueObjects.UploadedURL import UploadedURL
from NNMM.VideoInfoFetcher.ValueObjects.Userid import Userid
from NNMM.VideoInfoFetcher.ValueObjects.UsernameList import UsernameList
from NNMM.VideoInfoFetcher.ValueObjects.VideoidList import VideoidList
from NNMM.VideoInfoFetcher.ValueObjects.VideoURLList import VideoURLList


@dataclass(frozen=True)
class FetchedVideoInfo():
    """html/rssから取得される動画情報をまとめたデータクラス

    Notes:
        VideoInfoHtmlFetcher, VideoInfoRSSFetcher 参照
        このデータクラスの情報がfetchingの最終的な出力となる
        _make_result_dict() にて以下の項目をキーとする辞書が返却される
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]

    Raises:
        TypeError: 初期化時の引数の型が不正な場合
        ValueError: List系の入力の大きさが異なる場合

    Returns:
        FetchedVideoInfo: html/rssから取得される動画情報
    """
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

    def __post_init__(self) -> None:
        """初期化後処理

        Notes:
            バリデーションとresult_dict の返り値設定を行う
        """
        self._is_valid()
        object.__setattr__(self, "result_dict", self._make_result_dict())

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
            結果の辞書 [{key=RESULT_DICT_COLS, value=キーに対応する項目(文字列)}]

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

    def to_dict(self) -> list[dict]:
        """データクラスの項目を辞書として取得する

        Notes:
            result とは異なり、値は各ValueObject が設定される

        Returns:
            dict: {データクラスの項目: 対応するValueObject}
        """
        # return asdict(self)  # asdictだとキーと値が文字列になるため型情報が失われる
        return self.__dict__

    @property
    def result(self) -> list[dict]:
        """最終的な出力結果をまとめた辞書を返す

        Notes:
            _make_result_dict()参照

        Returns:
            list[dict]: [{key=RESULT_DICT_COLS, value=キーに対応する項目(文字列)}]
        """
        return self.result_dict

    @classmethod
    def merge(cls, fvi_page: "FetchedPageVideoInfo", fvi_api: "FetchedAPIVideoInfo") -> "FetchedVideoInfo":
        """マージ

        Notes:
            FetchedPageVideoInfo とFetchedAPIVideoInfo の結果をマージして
            FetchedVideoInfo のインスタンスを作成する
            同じキーがある場合はとFetchedAPIVideoInfo の値を優先する

        Returns:
            FetchedVideoInfo: fetchingの最終的な出力となるデータクラス
        """
        d = dict(fvi_page.to_dict(), **fvi_api.to_dict())
        return FetchedVideoInfo(**d)


if __name__ == "__main__":
    from NNMM.VideoInfoFetcher.ValueObjects.FetchedAPIVideoInfo import FetchedAPIVideoInfo
    from NNMM.VideoInfoFetcher.ValueObjects.FetchedPageVideoInfo import FetchedPageVideoInfo

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

    fvi = FetchedVideoInfo([1], userid, mylistid, showname, myshowname, mylist_url,
                           video_id_list, title_list, uploaded_at_list, registered_at_list,
                           video_url_list, username_list)
    # pprint(fvi.to_dict())
    fvi_page = FetchedPageVideoInfo([1], userid, mylistid, showname, myshowname, mylist_url,
                                    video_id_list, title_list, registered_at_list, video_url_list)
    fvi_api = FetchedAPIVideoInfo([1], video_id_list, title_list, uploaded_at_list,
                                  video_url_list, username_list)
    fvi_d = FetchedVideoInfo.merge(fvi_page, fvi_api)
    print(fvi == fvi_d)
    pprint(fvi.result)
