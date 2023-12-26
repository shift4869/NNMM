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
    pass
