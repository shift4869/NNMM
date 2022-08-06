# coding: utf-8
import asyncio
import logging.config
import pprint
import traceback
from dataclasses import dataclass
from logging import INFO, getLogger
from pathlib import Path

from bs4 import BeautifulSoup

from NNMM import ConfigMain
from NNMM.VideoInfoFetcher.RSSParser import RSSParser
from NNMM.VideoInfoFetcher.ValueObjects.FetchedPageVideoInfo import FetchedPageVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.FetchedVideoInfo import FetchedVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.ValueObjects.UploadedURL import UploadedURL
from NNMM.VideoInfoFetcher.VideoInfoFetcherBase import VideoInfoFetcherBase, SourceType

logger = getLogger("root")
logger.setLevel(INFO)


@dataclass
class VideoInfoRssFetcher(VideoInfoFetcherBase):
    mylist_url: UploadedURL | MylistURL

    # 日付フォーマット
    SOURCE_DATETIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
    DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(self, url: str):
        super().__init__(url, SourceType.RSS)
        if UploadedURL.is_valid(url):
            self.mylist_url = UploadedURL.create(url)
        elif MylistURL.is_valid(url):
            self.mylist_url = MylistURL.create(url)

    async def _analysis_rss(self, soup: BeautifulSoup) -> FetchedPageVideoInfo:
        """RSSを解析する

        Notes:
            url_typeから投稿動画ページかマイリストページかを識別して処理を分ける
            解析結果のdictの値の正当性はチェックしない

        Args:
            soup (BeautifulSoup): 解析対象のxml

        Returns:
            FetchedPageVideoInfo: 解析結果

        Raises:
            IndexError, TypeError: html解析失敗時
            ValueError: url_typeが不正 または html解析失敗時
        """
        mylist_url = self.mylist_url.non_query_url
        parser: RSSParser = RSSParser(mylist_url, soup)
        res = await parser.parse()

        if not res:
            raise ValueError("rss analysis failed.")

        return res

    async def _fetch_videoinfo_from_rss(self) -> list[dict]:
        """投稿動画/マイリストページアドレスから掲載されている動画の情報を取得する

        Notes:
            self.RESULT_DICT_COLS をキーとする情報を辞書で返す
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
            table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
            RSSは取得が速い代わりに最大30件までしか情報を取得できない

        Returns:
            video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照, エラー時 空リスト
        """
        VF = VideoInfoRssFetcher

        # RSS取得
        session, response = await self._get_session_response(self.mylist_url.fetch_url, False, "lxml-xml", None)
        await session.close()
        if not response:
            raise ValueError("rss request failed.")

        # RSS一時保存（DEBUG用）
        # config = ConfigMain.ProcessConfigBase.GetConfig()
        # rd_str = config["general"].get("rss_save_path", "")
        # rd_path = Path(rd_str)
        # rd_path.mkdir(exist_ok=True, parents=True)
        # with (rd_path / "current.xml").open("w", encoding="utf-8") as fout:
        #     fout.write(response.text)

        # RSSから必要な情報を収集する
        soup = BeautifulSoup(response.text, "lxml-xml")
        soup_d = await self._analysis_rss(soup)

        userid = soup_d.userid
        mylistid = soup_d.mylistid
        video_id_list = soup_d.video_id_list

        # 動画IDについてAPIを通して情報を取得する
        api_d = await self._get_videoinfo_from_api(video_id_list)

        # バリデーション
        if soup_d.title_list != api_d.title_list:
            raise ValueError("video title from rss and from api is different.")
        if soup_d.video_url_list != api_d.video_url_list:
            raise ValueError("video url from rss and from api is different.")

        # config取得
        config = ConfigMain.ProcessConfigBase.GetConfig()
        if not config:
            raise ValueError("config read failed.")

        # RSS保存
        rd_str = config["general"].get("rss_save_path", "")
        rd_path = Path(rd_str)
        rd_path.mkdir(exist_ok=True, parents=True)
        rss_file_name = f"{userid.id}.xml"
        if mylistid.id != "":
            rss_file_name = f"{userid.id}_{mylistid.id}.xml"
        try:
            with (rd_path / rss_file_name).open("w", encoding="utf-8") as fout:
                fout.write(response.text)
        except Exception:
            logger.error("RSS file save failed , but continue process.")
            logger.error(traceback.format_exc())
            pass  # 仮に書き込みに失敗しても以降の処理は続行する

        # 結合
        video_d = FetchedVideoInfo.merge(soup_d, api_d)
        return video_d.result

    async def _fetch_videoinfo(self) -> list[dict]:
        return await self._fetch_videoinfo_from_rss()


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
        video_list = loop.run_until_complete(VideoInfoRssFetcher.fetch_videoinfo(url))
        pprint.pprint(video_list)

    pass
