import sys
import unittest

from mock import call, patch

from nnmm.util import MylistType
from nnmm.video_info_fetcher.mylist_rss_xml_parser import MylistRSSXmlParser
from nnmm.video_info_fetcher.parser_factory import ParserFactory
from nnmm.video_info_fetcher.series_api_response_json_parser import SeriesAPIResponseJsonParser
from nnmm.video_info_fetcher.uploaded_rss_xml_parser import UploadedRSSXmlParser


class TestParserFactory(unittest.TestCase):
    def test_init(self):
        class_dict = ParserFactory._class_dict
        self.assertEqual(
            {
                MylistType.uploaded: UploadedRSSXmlParser,
                MylistType.mylist: MylistRSSXmlParser,
                MylistType.series: SeriesAPIResponseJsonParser,
            },
            class_dict,
        )

        with self.assertRaises(ValueError):
            instance = ParserFactory()

    def test_create(self):
        mock_dict = self.enterContext(patch("nnmm.video_info_fetcher.parser_factory.ParserFactory._class_dict"))
        response_text = "response_text"
        url = "url"
        for mylist_type in MylistType:
            if mylist_type == MylistType.none:
                continue
            mock_dict.reset_mock()
            actual = ParserFactory.create(mylist_type, url, response_text)
            self.assertEqual(
                [call.get(mylist_type, None), call.get().__bool__(), call.get()(url, response_text)],
                mock_dict.mock_calls,
            )

        with self.assertRaises(ValueError):
            actual = ParserFactory.create("invalid_type", url, response_text)

        mock_dict.get.side_effect = lambda key, d: None
        with self.assertRaises(ValueError):
            actual = ParserFactory.create(MylistType.none, url, response_text)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
