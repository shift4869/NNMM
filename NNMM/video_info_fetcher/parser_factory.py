from NNMM.util import MylistType
from NNMM.video_info_fetcher.mylist_rss_xml_parser import MylistRSSXmlParser
from NNMM.video_info_fetcher.parser_base import ParserBase
from NNMM.video_info_fetcher.series_api_response_json_parser import SeriesAPIResponseJsonParser
from NNMM.video_info_fetcher.uploaded_rss_xml_parser import UploadedRSSXmlParser


class ParserFactory:
    _class_dict: dict = {
        MylistType.uploaded: UploadedRSSXmlParser,
        MylistType.mylist: MylistRSSXmlParser,
        MylistType.series: SeriesAPIResponseJsonParser,
    }

    def __init__(self) -> None:
        pass

    @classmethod
    def create(cls, mylist_type: MylistType, url: str, response_text: str) -> ParserBase:
        if not isinstance(mylist_type, MylistType):
            raise ValueError("mylist_type must be MylistType.")
        _class = cls._class_dict.get(mylist_type, None)
        if not _class:
            raise ValueError("mylist_type is invalid value.")
        return _class(url, response_text)


if __name__ == "__main__":
    from NNMM.video_info_fetcher.video_info_fetcher import VideoInfoFetcher

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
