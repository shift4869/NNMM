from dataclasses import dataclass
from pprint import pprint

from NNMM.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL
from NNMM.video_info_fetcher.value_objects.mylistid import Mylistid
from NNMM.video_info_fetcher.value_objects.myshowname import Myshowname
from NNMM.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from NNMM.video_info_fetcher.value_objects.showname import Showname
from NNMM.video_info_fetcher.value_objects.title_list import TitleList
from NNMM.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from NNMM.video_info_fetcher.value_objects.userid import Userid
from NNMM.video_info_fetcher.value_objects.video_url_list import VideoURLList
from NNMM.video_info_fetcher.value_objects.videoid_list import VideoidList


@dataclass(frozen=True)
class FetchedPageVideoInfo:
    """htmlページから取得される動画情報をまとめたデータクラス

    HtmlParser, RSSParser参照

    Raises:
        TypeError: 初期化時の引数の型が不正な場合
        ValueError: List系の入力の大きさが異なる場合

    Returns:
        FetchedPageVideoInfo: htmlページから取得される動画情報
    """

    no: list[int]  # No. [1, ..., len()-1]
    userid: Userid  # ユーザーID 1234567
    mylistid: Mylistid  # マイリストID 12345678
    showname: Showname  # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
    myshowname: Myshowname  # マイリスト名 「まとめマイリスト」
    mylist_url: UploadedURL | UserMylistURL  # マイリストURL https://www.nicovideo.jp/user/1234567/mylist/12345678
    video_id_list: VideoidList  # 動画IDリスト [sm12345678]
    title_list: TitleList  # 動画タイトルリスト [テスト動画]
    registered_at_list: RegisteredAtList  # 登録日時リスト [%Y-%m-%d %H:%M:%S]
    video_url_list: VideoURLList  # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]

    def __post_init__(self) -> None:
        """初期化後処理

        バリデーションのみ
        """
        self._is_valid()

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

        if not (isinstance(self.mylist_url, UserMylistURL) or isinstance(self.mylist_url, UploadedURL)):
            raise TypeError("mylist_url must be UserMylistURL|UploadedURL.")

        if not isinstance(self.video_id_list, VideoidList):
            raise TypeError("video_id_list must be VideoidList.")
        if not isinstance(self.title_list, TitleList):
            raise TypeError("title_list must be TitleList.")
        if not isinstance(self.registered_at_list, RegisteredAtList):
            raise TypeError("registered_at_list must be RegisteredAtList.")
        if not isinstance(self.video_url_list, VideoURLList):
            raise TypeError("video_url_list must be VideoURLList.")

        num = len(self.no)
        if not all([
            len(self.video_id_list) == num,
            len(self.title_list) == num,
            len(self.registered_at_list) == num,
            len(self.video_url_list) == num,
        ]):
            raise ValueError("There are different size (*_list).")
        return True

    def to_dict(self) -> dict:
        """データクラスの項目を辞書として取得する

        値は各ValueObject が設定される

        Returns:
            dict: {データクラスの項目: 対応するValueObject}
        """
        # return asdict(self)  # asdictだとキーと値が文字列になるため型情報が失われる
        return self.__dict__


if __name__ == "__main__":
    userid = Userid("1234567")
    mylistid = Mylistid("12345678")
    showname = Showname("「まとめマイリスト」-shift4869さんのマイリスト")
    myshowname = Myshowname("「まとめマイリスト」")
    mylist_url = UserMylistURL.create("https://www.nicovideo.jp/user/1234567/mylist/12345678")
    video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
    video_id_list = VideoidList.create(video_url_list.video_id_list)
    title_list = TitleList.create(["テスト動画"])
    registered_at_list = RegisteredAtList.create(["2022-05-06 00:01:01"])
    no = list(range(1, len(video_id_list) + 1))

    fvi_page = FetchedPageVideoInfo(
        [1],
        userid,
        mylistid,
        showname,
        myshowname,
        mylist_url,
        video_id_list,
        title_list,
        registered_at_list,
        video_url_list,
    )
    pprint(fvi_page.to_dict())
