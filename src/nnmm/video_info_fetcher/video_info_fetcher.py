import asyncio
import logging.config
import pprint
import traceback
from dataclasses import dataclass
from logging import INFO, getLogger
from pathlib import Path

import orjson

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

        Returns:
            video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照, エラー時 空リスト
        """
        # fetch_url を元に動画情報を fetch
        response = await self._get_session_response(self.mylist_url.fetch_url)
        if not response:
            raise ValueError("fetch request failed.")

        # config取得
        config = process_config.ConfigBase.get_config()
        if not config:
            raise ValueError("config read failed.")

        # fetch したデータをキャッシュファイルに保存
        userid = self.mylist_url.userid
        mylistid = self.mylist_url.mylistid
        cache_file_name = f"{userid.id}.json"
        if mylistid.id != "":
            cache_file_name = f"{userid.id}_{mylistid.id}.json"

        rd_str = config["general"].get("rss_save_path", "")
        rd_path = Path(rd_str)
        rd_path.mkdir(exist_ok=True, parents=True)
        cache_file_path = rd_path / cache_file_name
        try:
            # この段階ではまだJSONとして取得できているか分からないのでテキストとして保存
            cache_file_path.write_text(response.text, encoding="utf-8")
        except Exception:
            logger.error(f"{self.mylist_url.fetch_url}, getting failed.")
            logger.error("Cache file save failed, but continue process.")
            logger.error(traceback.format_exc())
            pass  # 仮に書き込みに失敗しても以降の処理は続行する

        # fetch した情報をもとに必要な情報を収集する
        fetched_d = await self._analysis_response_text(response.text)

        # 正常に情報が取得できた場合キャッシュファイルをJSONとして作り直す
        if cache_file_path.exists():
            data = orjson.loads(cache_file_path.read_bytes())
            cache_file_path.unlink(missing_ok=True)
            cache_file_path.write_bytes(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))

        # FetchedPageVideoInfo 型から FetchedVideoInfo 型に変換
        fetched_dict = fetched_d.to_dict()
        return FetchedVideoInfo(**fetched_dict)

    async def _fetch_videoinfo(self) -> FetchedVideoInfo:
        return await self._fetch_videoinfo_from_fetch_url()


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    process_config.ConfigBase.set_config()

    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/31784111/video",  # 投稿動画0件
        # "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/31784111/mylist/73141814",  # 0件マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
        # "https://www.nicovideo.jp/user/12899156/series/442402",  # シリーズ
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    for url in urls:
        try:
            video_list = loop.run_until_complete(VideoInfoFetcher.fetch_videoinfo(url))
            pprint.pprint(video_list)
        except Exception:
            pass
