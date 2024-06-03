import asyncio
import logging.config
import pprint
import traceback
from dataclasses import dataclass
from logging import INFO, getLogger
from pathlib import Path

from nnmm.process import config as process_config
from nnmm.video_info_fetcher.parser_base import ParserBase
from nnmm.video_info_fetcher.parser_factory import ParserFactory
from nnmm.video_info_fetcher.value_objects.fetched_page_video_info import FetchedPageVideoInfo
from nnmm.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo
from nnmm.video_info_fetcher.video_info_fetcher_base import VideoInfoFetcherBase

logger = getLogger(__name__)
logger.setLevel(INFO)


@dataclass
class VideoInfoFetcher(VideoInfoFetcherBase):
    def __init__(self, url: str):
        super().__init__(url)

    async def _analysis_response_text(self, response_text: str) -> FetchedPageVideoInfo:
        try:
            mylist_url = self.mylist_url.non_query_url
            mylist_type = self.mylist_url.mylist_type
            parser: ParserBase = ParserFactory.create(mylist_type, mylist_url, response_text)
            res = await parser.parse()
        except Exception:
            logger.error(f"{self.mylist_url.non_query_url}: response text parse error.")
            raise ValueError("response text analysis failed.")
        return res

    async def _fetch_videoinfo_from_fetch_url(self) -> FetchedVideoInfo:
        """投稿動画/マイリストページアドレスから掲載されている動画の情報を取得する

        Notes:
            self.RESULT_DICT_COLS をキーとする情報を辞書で返す
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                               "投稿日時", "登録日時", "動画URL",
                               "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
            table_cols = ["no", "video_id", "title", "username", "status",
                          "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
            RSSは取得が速い代わりに最大30件までしか情報を取得できない

        Returns:
            video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照, エラー時 空リスト
        """
        # fetch_url を元に動画情報を fetch
        response = await self._get_session_response(self.mylist_url.fetch_url)
        if not response:
            raise ValueError("fetch request failed.")

        # RSS/APIから必要な情報を収集する
        fetched_d = await self._analysis_response_text(response.text)

        userid = fetched_d.userid
        mylistid = fetched_d.mylistid
        video_id_list = fetched_d.video_id_list

        # 動画IDについてAPIを通して情報を取得する
        api_d = await self._get_videoinfo_from_api(video_id_list)

        # バリデーション
        if fetched_d.title_list != api_d.title_list:
            raise ValueError("video title from fetched data and from api is different.")
        if fetched_d.video_url_list != api_d.video_url_list:
            raise ValueError("video url from fetched data and from api is different.")

        # config取得
        config = process_config.ConfigBase.get_config()
        if not config:
            raise ValueError("config read failed.")

        # fetch したデータを保存
        # THINK:: jsonをfetchしてもxmlで保存される
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
            logger.error(f"{self.mylist_url.fetch_url}, getting failed.")
            logger.error("RSS file save failed, but continue process.")
            logger.error(traceback.format_exc())
            pass  # 仮に書き込みに失敗しても以降の処理は続行する

        # 結合
        video_d = FetchedVideoInfo.merge(fetched_d, api_d)
        return video_d

    async def _fetch_videoinfo(self) -> FetchedVideoInfo:
        return await self._fetch_videoinfo_from_fetch_url()


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    process_config.ConfigBase.set_config()

    urls = [
        # "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        # "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
        "https://www.nicovideo.jp/user/12899156/series/442402",  # シリーズ
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    for url in urls:
        try:
            video_list = loop.run_until_complete(VideoInfoFetcher.fetch_videoinfo(url))
            pprint.pprint(video_list)
        except Exception:
            pass
