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
        class_name = self.__class__.__name__
        raise ValueError(f"{class_name} cannot make instance, use classmethod {class_name}.create().")

    @classmethod
    def create(cls, mylist_type: MylistType, url: str, response_text: str) -> ParserBase:
        if not isinstance(mylist_type, MylistType):
            raise ValueError("mylist_type must be MylistType.")
        _class = cls._class_dict.get(mylist_type, None)
        if not _class:
            raise ValueError("mylist_type is invalid value.")
        return _class(url, response_text)


if __name__ == "__main__":
    mylist_url = "https://www.nicovideo.jp/user/11111111/series/123456"
    response_text = r'{"key": "value"}'
    parser: ParserBase = ParserFactory.create(MylistType.series, mylist_url, response_text)
    print(parser)
