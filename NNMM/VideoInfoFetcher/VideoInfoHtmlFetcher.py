# coding: utf-8
import asyncio
import logging.config
import pprint
from dataclasses import dataclass
from logging import INFO, getLogger

from requests_html import HtmlElement

from NNMM import ConfigMain
from NNMM.VideoInfoFetcher.HtmlParser import HtmlParser
from NNMM.VideoInfoFetcher.ValueObjects.FetchedPageVideoInfo import FetchedPageVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.FetchedVideoInfo import FetchedVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.ValueObjects.UploadedURL import UploadedURL
from NNMM.VideoInfoFetcher.VideoInfoFetcherBase import VideoInfoFetcherBase, SourceType


logger = getLogger("root")
logger.setLevel(INFO)


@dataclass
class VideoInfoHtmlFetcher(VideoInfoFetcherBase):
    mylist_url: UploadedURL | MylistURL

    def __init__(self, url: str):
        super().__init__(url, SourceType.HTML)
        if UploadedURL.is_valid(url):
            self.mylist_url = UploadedURL.create(url)
        elif MylistURL.is_valid(url):
            self.mylist_url = MylistURL.create(url)

    async def _analysis_html(self, lxml: HtmlElement) -> FetchedPageVideoInfo:
        """htmlを解析する

        Notes:
            実際の解析はHtmlParser.parse()に任せる

        Args:
            lxml (HtmlElement): 解析対象のhtml

        Returns:
            FetchedPageVideoInfo: 解析結果

        Raises:
            AttributeError | ValueError: html解析失敗時
        """
        mylist_url = self.mylist_url.non_query_url
        parser: HtmlParser = HtmlParser(mylist_url, lxml)
        res = await parser.parse()

        if not res:
            raise ValueError("html analysis failed.")

        return res

    async def _fetch_videoinfo_from_html(self) -> list[dict]:
        """リクエスト用の投稿動画/マイリストページアドレスから掲載されている動画の情報を取得する

        Notes:
            以下 をキーとする情報を辞書で返す（ FetchedVideoInfo 参照）
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
            table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
            実際に内部ブラウザでページを開き、
            レンダリングして最終的に表示されたページから動画情報をスクレイピングする
            レンダリングに時間がかかる代わりに最大100件まで取得できる

        Returns:
            FetchedVideoInfo.result (list[dict]): 動画情報をまとめた辞書リスト キーはFetchedVideoInfoを参照
        """
        # ページ取得
        session, response = await self._get_session_response(self.mylist_url.non_query_url, True, "html.parser", None)
        await session.close()
        if not response:
            raise ValueError("html request failed.")

        # 取得ページと動画IDから必要な情報を収集する
        html_d = await self._analysis_html(response.html.lxml)

        video_id_list = html_d.video_id_list
        video_url_list = html_d.video_url_list

        # 動画リンクが1つもない場合は空リストを返して終了
        if video_url_list == []:
            logger.warning("HTML pages request is success , but video info is nothing.")
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
        # "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    for url in urls:
        video_list = loop.run_until_complete(VideoInfoHtmlFetcher.fetch_videoinfo(url))
        pprint.pprint(video_list)

    pass
