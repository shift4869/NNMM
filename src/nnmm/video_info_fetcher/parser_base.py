import asyncio
import pprint
from abc import ABC, abstractmethod
from dataclasses import dataclass

from nnmm.video_info_fetcher.value_objects.fetched_page_video_info import FetchedPageVideoInfo
from nnmm.video_info_fetcher.value_objects.mylist_url import MylistURL
from nnmm.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory
from nnmm.video_info_fetcher.value_objects.mylistid import Mylistid
from nnmm.video_info_fetcher.value_objects.myshowname import Myshowname
from nnmm.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from nnmm.video_info_fetcher.value_objects.showname import Showname
from nnmm.video_info_fetcher.value_objects.title_list import TitleList
from nnmm.video_info_fetcher.value_objects.userid import Userid
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


@dataclass
class ParserBase(ABC):
    mylist_url: MylistURL

    def __init__(self, url: str, response_text: str) -> None:
        self.mylist_url = MylistURLFactory.create(url)
        self.response_text = response_text

    def _get_mylist_url(self) -> MylistURL:
        """マイリストURL"""
        return self.mylist_url

    def _get_userid_mylistid(self) -> tuple[Userid, Mylistid]:
        """ユーザーID, マイリストID設定"""
        userid = self.mylist_url.userid
        mylistid = self.mylist_url.mylistid
        return (userid, mylistid)

    @abstractmethod
    def _get_username(self) -> Username:
        """投稿者収集"""
        raise NotImplementedError

    @abstractmethod
    def _get_showname_myshowname(self) -> tuple[Showname, Myshowname]:
        """マイリスト名収集"""
        raise NotImplementedError

    @abstractmethod
    def _get_entries(self) -> tuple[VideoidList, TitleList, RegisteredAtList, VideoURLList]:
        """エントリー収集"""
        raise NotImplementedError

    async def parse(self) -> FetchedPageVideoInfo:
        """text を解析する

        Returns:
            FetchedPageVideoInfo: 解析結果

        Raises:
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """
        # マイリストURL設定
        mylist_url = self._get_mylist_url()

        # 投稿者IDとマイリストID取得
        userid, mylistid = self._get_userid_mylistid()

        # ユーザー名を取得
        username = self._get_username()

        # マイリスト名収集
        # 投稿動画の場合はマイリスト名がないのでユーザー名と合わせて便宜上の名前に設定
        showname, myshowname = self._get_showname_myshowname()

        # 動画エントリ取得
        video_id_list, title_list, registered_at_list, video_url_list = self._get_entries()

        num = len(video_url_list)
        check_list = [
            num == len(video_url_list),
            num == len(video_id_list),
            num == len(title_list),
            num == len(registered_at_list),
        ]
        if not all(check_list):
            raise ValueError("video entry parse failed.")

        # 返り値設定
        res = {
            "no": list(range(1, num + 1)),  # No. [1, ..., len()-1]
            "userid": userid,  # ユーザーID 1234567
            "mylistid": mylistid,  # マイリストID 12345678
            "showname": showname,  # マイリスト表示名 「投稿者1さんの投稿動画」
            "myshowname": myshowname,  # マイリスト名 「投稿動画」
            "mylist_url": mylist_url,  # マイリストURL https://www.nicovideo.jp/user/11111111/video
            "video_id_list": video_id_list,  # 動画IDリスト [sm12345678]
            "title_list": title_list,  # 動画タイトルリスト [テスト動画]
            "registered_at_list": registered_at_list,  # 登録日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,  # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        }
        return FetchedPageVideoInfo(**res)


if __name__ == "__main__":
    from nnmm.video_info_fetcher.video_info_fetcher import VideoInfoFetcher

    urls = [
        # "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        # "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/12899156/series/442402",  # シリーズ
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    for url in urls:
        virf = VideoInfoFetcher(url)
        response = loop.run_until_complete(virf._get_session_response(virf.mylist_url.fetch_url))
        rp = ParserBase(url, response.text)
        fetched_page_video_info = loop.run_until_complete(rp.parse())

        pprint.pprint(fetched_page_video_info.to_dict())
    pass
