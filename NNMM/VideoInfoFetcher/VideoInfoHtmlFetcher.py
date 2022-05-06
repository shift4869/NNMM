# coding: utf-8
import asyncio
import logging.config
import pprint
import re
from datetime import datetime, timedelta
from logging import INFO, getLogger

from requests_html import HtmlElement

from NNMM import ConfigMain
from NNMM.VideoInfoFetcher.FetchedVideoInfo import FetchedAPIVideoInfo, FetchedPageVideoInfo, FetchedVideoInfo
from NNMM.VideoInfoFetcher.URL import URL, URLType
from NNMM.VideoInfoFetcher.VideoInfoFetcherBase import VideoInfoFetcherBase, SourceType


logger = getLogger("root")
logger.setLevel(INFO)


class VideoInfoHtmlFetcher(VideoInfoFetcherBase):
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

    def __init__(self, url: str):
        super().__init__(url, SourceType.HTML)

    def _translate_pagedate(self, td_str: str) -> str:
        """動画掲載ページにある日時を解釈する関数

        Note:
            次のいずれかが想定されている
            ["たった今","n分前","n時間前"]

        Args:
            td_str (str): 上記の想定文字列

        Returns:
            str: 成功時 "%Y-%m-%d %H:%M:00"、失敗時 空文字列
        """
        VF = VideoInfoHtmlFetcher
        try:
            now_date = datetime.now()
            if "今" in td_str:
                return now_date.strftime(VF.DESTINATION_DATETIME_FORMAT)

            if "分前" in td_str:
                pattern = "^([0-9]+)分前$"
                if re.findall(pattern, td_str):
                    minutes = int(re.findall(pattern, td_str)[0])
                    dst_date = now_date - timedelta(minutes=minutes)
                    return dst_date.strftime(VF.DESTINATION_DATETIME_FORMAT)

            if "時間前" in td_str:
                pattern = "^([0-9]+)時間前$"
                if re.findall(pattern, td_str):
                    hours = int(re.findall(pattern, td_str)[0])
                    dst_date = now_date - timedelta(hours=hours)
                    return dst_date.strftime(VF.DESTINATION_DATETIME_FORMAT)
        except Exception:
            pass
        return ""

    async def _analysis_uploaded_page(self, lxml: HtmlElement) -> FetchedPageVideoInfo:
        """投稿動画ページのhtmlを解析する

        Args:
            lxml (HtmlElement): 投稿動画ページのhtml

        Returns:
            FetchedPageVideoInfo: 解析結果

        Raises:
            AttributeError: html解析失敗時
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """
        VF = VideoInfoHtmlFetcher

        # マイリストURL設定
        mylist_url = self.url.url

        # ユーザーID, マイリストID設定
        pattern = self.url.UPLOADED_URL_PATTERN
        userid = re.findall(pattern, mylist_url)[0]
        mylistid = ""  # 投稿動画の場合、マイリストIDは無し

        # すべての動画リンクを抽出
        video_url_list = []
        pattern = FetchedAPIVideoInfo.VIDEO_URL_PATTERN  # ニコニコ動画URLの形式
        video_link_lx = lxml.find_class(VF.TCT_VIDEO_URL)
        for video_link in video_link_lx:
            a = video_link.find("a")
            if re.search(pattern, a.attrib["href"]):
                video_url_list.append(a.attrib["href"])

        # 動画リンク抽出は降順でないため、ソートする（ロード順？）
        # video_list.sort(reverse=True)  # 降順ソート

        # 動画ID収集
        pattern = FetchedAPIVideoInfo.VIDEO_URL_PATTERN  # ニコニコ動画URLの形式
        video_id_list = [re.findall(pattern, s)[0] for s in video_url_list]

        # 動画名収集
        # 全角スペースは\u3000(unicode-escape)となっている
        title_list = []
        title_lx = lxml.find_class(VF.TCT_TITLE)
        if title_lx == []:
            raise AttributeError(VF.MSG_TITLE)
        title_list = [str(t.text) for t in title_lx]

        # 登録日時収集
        # SOURCE_DATETIME_FORMAT: HTMLページに記載されている日付形式
        # DESTINATION_DATETIME_FORMAT: NNMMで扱う日付形式
        uploaded_at_list = []
        try:
            uploaded_at_lx = lxml.find_class(VF.TCT_UPLOADED)
            if uploaded_at_lx == []:
                raise AttributeError(VF.MSG_UPLOADED1)

            for t in uploaded_at_lx:
                tca = str(t.text)
                if "前" in tca or "今" in tca:
                    tca = self._translate_pagedate(tca)
                    if tca != "":
                        uploaded_at_list.append(tca)
                    else:
                        raise ValueError
                else:
                    dst = datetime.strptime(tca, VF.SOURCE_DATETIME_FORMAT)
                    uploaded_at_list.append(dst.strftime(VF.DESTINATION_DATETIME_FORMAT))
        except ValueError:
            raise ValueError(VF.MSG_UPLOADED2)
        registered_at_list = uploaded_at_list

        # 投稿者収集
        username_lx = lxml.find_class(VF.TCT_USERNAME)
        if username_lx == []:
            raise AttributeError(VF.MSG_USERNAME)
        username = username_lx[0].text

        # マイリスト名収集
        showname = f"{username}さんの投稿動画"
        myshowname = "投稿動画"

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

    async def _analysis_mylist_page(self, lxml: HtmlElement) -> FetchedPageVideoInfo:
        """マイリストページのhtmlを解析する

        Args:
            lxml (HtmlElement): マイリストページのhtml

        Returns:
            FetchedPageVideoInfo: 解析結果

        Raises:
            AttributeError: html解析失敗時
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """
        VF = VideoInfoHtmlFetcher

        # マイリストURL設定
        mylist_url = self.url.url

        # ユーザーID, マイリストID設定
        pattern = self.url.MYLIST_URL_PATTERN
        userid, mylistid = re.findall(pattern, mylist_url)[0]

        # すべての動画リンクを抽出
        video_url_list = []
        pattern = FetchedAPIVideoInfo.VIDEO_URL_PATTERN  # ニコニコ動画URLの形式
        video_link_lx = lxml.find_class(VF.TCT_VIDEO_URL)
        for video_link in video_link_lx:
            a = video_link.find("a")
            if re.search(pattern, a.attrib["href"]):
                video_url_list.append(a.attrib["href"])

        # 動画リンク抽出は降順でないため、ソートする（ロード順？）
        # video_list.sort(reverse=True)  # 降順ソート

        # 動画ID収集
        pattern = FetchedAPIVideoInfo.VIDEO_URL_PATTERN  # ニコニコ動画URLの形式
        video_id_list = [re.findall(pattern, s)[0] for s in video_url_list]

        # 動画名収集
        # 全角スペースは\u3000(unicode-escape)となっている
        title_list = []
        title_lx = lxml.find_class(VF.TCT_TITLE)
        if title_lx == []:
            raise AttributeError(VF.MSG_TITLE)
        title_list = [str(t.text) for t in title_lx]

        # 登録日時収集
        registered_at_list = []
        try:
            registered_at_lx = lxml.find_class(VF.TCT_REGISTERED)
            if registered_at_lx == []:
                raise AttributeError(VF.MSG_REGISTERED1)

            for t in registered_at_lx:
                tca = str(t.text).replace(" マイリスト登録", "")
                if "前" in tca or "今" in tca:
                    tca = self._translate_pagedate(tca)
                    if tca != "":
                        registered_at_list.append(tca)
                    else:
                        raise ValueError
                else:
                    dst = datetime.strptime(tca, VF.SOURCE_DATETIME_FORMAT)
                    registered_at_list.append(dst.strftime(VF.DESTINATION_DATETIME_FORMAT))
        except ValueError:
            raise ValueError(VF.MSG_REGISTERED2)

        # マイリスト作成者名収集
        username_lx = lxml.find_class(VF.TCT_USERNAME)
        if username_lx == []:
            raise AttributeError(VF.MSG_USERNAME)
        username = username_lx[0].text  # マイリスト作成者は元のhtmlに含まれている

        # マイリスト名収集
        showname = ""
        myshowname = ""
        myshowname_lx = lxml.find_class(VF.TCT_MYSHOWNAME)
        if myshowname_lx == []:
            raise AttributeError(VF.MSG_MYSHOWNAME)
        myshowname = myshowname_lx[0].text
        showname = f"「{myshowname}」-{username}さんのマイリスト"

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

    async def _analysis_html(self, lxml: HtmlElement) -> FetchedPageVideoInfo:
        """htmlを解析する

        Notes:
            self.url.typeから投稿動画ページかマイリストページかを識別して処理を分ける

        Args:
            lxml (HtmlElement): 解析対象のhtml

        Returns:
            FetchedPageVideoInfo: 解析結果

        Raises:
            AttributeError: html解析失敗時
            ValueError: url_typeが不正, または datetime.strptime 投稿日時解釈失敗時
        """
        res = None
        if self.url.type == URLType.UPLOADED:
            res = await self._analysis_uploaded_page(lxml)
        elif self.url.type == URLType.MYLIST:
            res = await self._analysis_mylist_page(lxml)

        if not res:
            raise ValueError("html analysis failed.")

        return res

    async def _fetch_videoinfo_from_html(self) -> list[dict]:
        """投稿動画/マイリストページアドレスから掲載されている動画の情報を取得する

        Notes:
            self.RESULT_DICT_COLS をキーとする情報を辞書で返す
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
            table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
            実際に内部ブラウザでページを開き、
            レンダリングして最終的に表示されたページから動画情報をスクレイピングする
            レンダリングに時間がかかる代わりに最大100件まで取得できる

        Returns:
            video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照, エラー時 空リスト
        """
        VF = VideoInfoHtmlFetcher
        # ページ取得
        session, response = await self._get_session_response(self.request_url.request_url, True, "html.parser", None)
        await session.close()
        if not response:
            raise ValueError("html request failed.")

        # 取得ページと動画IDから必要な情報を収集する
        html_d = await self._analysis_html(response.html.lxml)

        video_id_list = html_d.video_id_list
        video_url_list = html_d.video_url_list

        # 動画リンクが1つもない場合は空リストを返して終了
        if video_url_list == []:
            logger.warning(VF.MSG_VIDEO_URL)
            return []

        # 動画IDについてAPIを通して情報を取得する
        api_d = await self._get_videoinfo_from_api(video_id_list)

        # バリデーション
        if html_d.title_list != api_d.title_list:
            raise ValueError("video title from html and from api is different.")
        # uploaded_at はapi_dの方が精度が良いため一致はしない
        # if html_d.get("uploaded_at_list") != api_d.get("uploaded_at_list"):
        #     raise ValueError("uploaded_at from html and from api is different.")
        if video_url_list != api_d.video_url_list:
            raise ValueError("video url from html and from api is different.")

        # 結合
        video_d = FetchedVideoInfo.merge(html_d, api_d)

        return video_d.result

    async def _fetch_videoinfo(self) -> list[dict]:
        return await self._fetch_videoinfo_from_html()


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    ConfigMain.ProcessConfigBase.SetConfig()

    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/12899156/mylist/39194985",  # 中量マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/67376990",  # 少量マイリスト
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    for url in urls:
        video_list = loop.run_until_complete(VideoInfoHtmlFetcher.fetch_videoinfo(url))
        pprint.pprint(video_list)

    pass
