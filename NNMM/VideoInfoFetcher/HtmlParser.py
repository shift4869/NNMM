# coding: utf-8
import asyncio
import pprint
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from requests_html import HtmlElement

from NNMM.VideoInfoFetcher.FetchedPageVideoInfo import FetchedPageVideoInfo
from NNMM.VideoInfoFetcher.Mylistid import Mylistid
from NNMM.VideoInfoFetcher.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.Myshowname import Myshowname
from NNMM.VideoInfoFetcher.RegisteredAtList import RegisteredAtList
from NNMM.VideoInfoFetcher.Showname import Showname
from NNMM.VideoInfoFetcher.TitleList import TitleList
from NNMM.VideoInfoFetcher.UploadedAtList import UploadedAtList
from NNMM.VideoInfoFetcher.UploadedURL import UploadedURL
from NNMM.VideoInfoFetcher.Userid import Userid
from NNMM.VideoInfoFetcher.Username import Username
from NNMM.VideoInfoFetcher.VideoidList import VideoidList
from NNMM.VideoInfoFetcher.VideoURL import VideoURL
from NNMM.VideoInfoFetcher.VideoURLList import VideoURLList


@dataclass
class HtmlParser():
    mylist_url: UploadedURL | MylistURL
    lxml: HtmlElement

    # 日付フォーマット
    SOURCE_DATETIME_FORMAT = "%Y/%m/%d %H:%M"
    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    # 探索対象のクラスタグ定数
    # 投稿動画ではREGISTEREDが存在しないためUPLOADEDを代替に使う
    TCT_VIDEO_URL = "NC-MediaObject-main"
    TCT_TITLE = "NC-MediaObjectTitle"
    TCT_USERNAME = "UserDetailsHeader-nickname"
    TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
    TCT_REGISTERED = "MylistItemAddition-addedAt"
    TCT_MYSHOWNAME = "MylistHeader-name"

    # エラーメッセージ定数
    MSG_VIDEO_URL = "HTML pages request is success , but video info is nothing."
    MSG_TITLE = f"title parse failed. '{TCT_TITLE}' is not found."
    MSG_UPLOADED1 = f"uploaded_at parse failed. '{TCT_UPLOADED}' is not found."
    MSG_UPLOADED2 = "uploaded_at date parse failed."
    MSG_REGISTERED1 = f"registered_at parse failed. '{TCT_REGISTERED}' is not found."
    MSG_REGISTERED2 = "registered_at date parse failed."
    MSG_USERNAME = f"username parse failed. '{TCT_USERNAME}' is not found."
    MSG_MYSHOWNAME = f"myshowname parse failed. '{TCT_MYSHOWNAME}' is not found."

    def __init__(self, url: str, lxml: HtmlElement):
        if UploadedURL.is_valid(url):
            self.mylist_url = UploadedURL.create(url)
        elif MylistURL.is_valid(url):
            self.mylist_url = MylistURL.create(url)
        self.lxml = lxml

    def _translate_pagedate(self, dt_str: str) -> str:
        """動画掲載ページにある日時を解釈する関数

        Note:
            次のいずれかが想定されている
            ["たった今","n分前","n時間前", {HP.SOURCE_DATETIME_FORMAT}形式]

        Args:
            dt_str (str): 上記の想定文字列

        Returns:
            str: 成功時 "%Y-%m-%d %H:%M:00"、失敗時 TypeError | ValueError
        """
        HP = HtmlParser
        now_date = datetime.now()
        if "今" in dt_str:
            return now_date.strftime(HP.DESTINATION_DATETIME_FORMAT)

        if "分前" in dt_str:
            pattern = "^([0-9]+)分前$"
            if re.findall(pattern, dt_str):
                minutes = int(re.findall(pattern, dt_str)[0])
                dst_date = now_date - timedelta(minutes=minutes)
                return dst_date.strftime(HP.DESTINATION_DATETIME_FORMAT)

        if "時間前" in dt_str:
            pattern = "^([0-9]+)時間前$"
            if re.findall(pattern, dt_str):
                hours = int(re.findall(pattern, dt_str)[0])
                dst_date = now_date - timedelta(hours=hours)
                return dst_date.strftime(HP.DESTINATION_DATETIME_FORMAT)

        # その他{HP.SOURCE_DATETIME_FORMAT}形式
        dst_date = datetime.strptime(dt_str, HP.SOURCE_DATETIME_FORMAT)
        return dst_date.strftime(HP.DESTINATION_DATETIME_FORMAT)

    def _get_mylist_url(self) -> UploadedURL | MylistURL:
        """マイリストURL
        """
        return self.mylist_url

    def _get_userid_mylistid(self) -> tuple[Userid, Mylistid]:
        """ユーザーID, マイリストID設定
        """
        userid = self.mylist_url.userid
        mylistid = self.mylist_url.mylistid
        return (userid, mylistid)

    def _get_video_url_list(self) -> VideoURLList:
        """すべての動画リンクを抽出
        """
        HP = HtmlParser
        video_url_list = []
        pattern = VideoURL.VIDEO_URL_PATTERN
        video_link_lx = self.lxml.find_class(HP.TCT_VIDEO_URL)
        for video_link in video_link_lx:
            a = video_link.find("a")
            if re.search(pattern, a.attrib["href"]):
                video_url = VideoURL.create(a.attrib["href"])
                video_url_list.append(video_url)
        return VideoURLList.create(video_url_list)

    def _get_video_id_list(self) -> VideoidList:
        """動画ID収集
        """
        video_url_list = self._get_video_url_list()
        video_id_list = video_url_list.video_id_list
        return VideoidList.create(video_id_list)

    def _get_title_list(self) -> TitleList:
        """動画名収集
        """
        # 全角スペースは\u3000(unicode-escape)となっている
        HP = HtmlParser
        title_list = []
        title_lx = self.lxml.find_class(HP.TCT_TITLE)
        # if title_lx == []:
        #     raise AttributeError(HP.MSG_TITLE)
        title_list = [str(t.text) for t in title_lx]
        return TitleList.create(title_list)

    def _get_uploaded_at_list(self) -> UploadedAtList:
        """投稿日時収集
        """
        HP = HtmlParser
        uploaded_at_list = []
        try:
            uploaded_at_lx = self.lxml.find_class(HP.TCT_UPLOADED)
            # if uploaded_at_lx == []:
            #     raise AttributeError(HP.MSG_UPLOADED1)

            for t in uploaded_at_lx:
                dt_str = str(t.text)
                dst = self._translate_pagedate(dt_str)
                uploaded_at_list.append(dst)
        except ValueError:
            raise ValueError(HP.MSG_UPLOADED2)
        return UploadedAtList.create(uploaded_at_list)

    def _get_registered_at_list(self) -> RegisteredAtList:
        """登録日時収集
        """
        HP = HtmlParser
        registered_at_list = []
        try:
            registered_at_lx = self.lxml.find_class(HP.TCT_REGISTERED)
            # if registered_at_lx == []:
            #     raise AttributeError(HP.MSG_REGISTERED1)

            for t in registered_at_lx:
                dt_str = str(t.text).replace(" マイリスト登録", "")
                dst = self._translate_pagedate(dt_str)
                registered_at_list.append(dst)
        except ValueError:
            raise ValueError(HP.MSG_REGISTERED2)
        return RegisteredAtList.create(registered_at_list)

    def _get_username(self) -> Username:
        """投稿者収集
        """
        HP = HtmlParser
        username_lx = self.lxml.find_class(HP.TCT_USERNAME)
        if username_lx == []:
            raise AttributeError(HP.MSG_USERNAME)
        username = username_lx[0].text
        return Username(username)

    def _get_showname_myshowname(self) -> tuple[Showname, Myshowname]:
        """マイリスト名収集
        """
        HP = HtmlParser
        username = self._get_username()
        if isinstance(self.mylist_url, UploadedURL):
            myshowname = Myshowname("投稿動画")
            showname = Showname.create(username, None)
            return (showname, myshowname)
        elif isinstance(self.mylist_url, MylistURL):
            myshowname_lx = self.lxml.find_class(HP.TCT_MYSHOWNAME)
            if myshowname_lx == []:
                raise AttributeError(HP.MSG_MYSHOWNAME)
            myshowname = Myshowname(myshowname_lx[0].text)
            showname = Showname.create(username, myshowname)
            return (showname, myshowname)
        raise AttributeError("(showname, myshowname) parse failed.")

    async def parse(self) -> FetchedPageVideoInfo:
        """投稿動画ページのhtmlを解析する

        Returns:
            FetchedPageVideoInfo: 解析結果

        Raises:
            AttributeError: html解析失敗時
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """
        HP = HtmlParser

        # マイリストURL設定
        mylist_url = self._get_mylist_url()

        # ユーザーID, マイリストID設定
        # 投稿動画の場合、マイリストIDは無し
        userid, mylistid = self._get_userid_mylistid()

        # すべての動画リンクを抽出
        video_url_list = self._get_video_url_list()

        # 動画リンク抽出は降順でないため、ソートする（ロード順？）
        # video_list.sort(reverse=True)  # 降順ソート

        # 動画ID収集
        video_id_list = self._get_video_id_list()

        # 動画名収集
        # 全角スペースは\u3000(unicode-escape)となっている
        title_list = self._get_title_list()

        # 登録日時収集
        registered_at_list = []
        if isinstance(self.mylist_url, UploadedURL):
            # 投稿動画ページは登録日時の情報がないため
            # 投稿日時を登録日時として使用する
            uploaded_at_list = self._get_uploaded_at_list()
            registered_at_list = RegisteredAtList.create([uploaded_at.dt_str for uploaded_at in uploaded_at_list])
        elif isinstance(self.mylist_url, MylistURL):
            registered_at_list = self._get_registered_at_list()

        # 投稿者収集
        username = self._get_username()

        # マイリスト名収集
        showname, myshowname = self._get_showname_myshowname()

        num = len(title_list)
        res = {
            "no": list(range(1, num + 1)),              # No. [1, ..., len()-1]
            "userid": userid,                           # ユーザーID 1234567
            "mylistid": mylistid,                       # マイリストID 12345678
            "showname": showname,                       # マイリスト表示名 「投稿者1さんの投稿動画」
            "myshowname": myshowname,                   # マイリスト名 「投稿動画」
            "mylist_url": mylist_url,                   # マイリストURL https://www.nicovideo.jp/user/11111111/video
            "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        }
        return FetchedPageVideoInfo(**res)


if __name__ == "__main__":
    from NNMM.VideoInfoFetcher.VideoInfoHtmlFetcher import VideoInfoHtmlFetcher
    urls = [
        # "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    for url in urls:
        vihf = VideoInfoHtmlFetcher(url)
        session, response = loop.run_until_complete(vihf._get_session_response(vihf.mylist_url.non_query_url, True, "html.parser", None))
        loop.run_until_complete(session.close())

        hp = HtmlParser(url, response.html.lxml)
        html_d = loop.run_until_complete(hp.parse())

        pprint.pprint(html_d.to_dict())
    pass
