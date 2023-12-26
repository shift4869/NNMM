import sys
import unittest
import warnings

from mock import MagicMock, patch

from NNMM.video_info_fetcher.parser_base import ParserBase
from NNMM.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory
from NNMM.video_info_fetcher.value_objects.myshowname import Myshowname
from NNMM.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from NNMM.video_info_fetcher.value_objects.showname import Showname
from NNMM.video_info_fetcher.value_objects.title_list import TitleList
from NNMM.video_info_fetcher.value_objects.username import Username
from NNMM.video_info_fetcher.value_objects.video_url_list import VideoURLList
from NNMM.video_info_fetcher.value_objects.videoid_list import VideoidList


class ConcreteParser(ParserBase):
    def _get_username(self) -> Username:
        return "username"

    def _get_showname_myshowname(self) -> tuple[Showname, Myshowname]:
        return "showname", "myshowname"

    def _get_entries(self) -> tuple[VideoidList, TitleList, RegisteredAtList, VideoURLList]:
        return VideoidList([]), TitleList([]), RegisteredAtList([]), VideoURLList([])


class TestParserBase(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        warnings.simplefilter("ignore", ResourceWarning)

    def _get_url_set(self) -> list[str]:
        """urlセットを返す"""
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
            "https://www.nicovideo.jp/user/11111111/series/123456",
        ]
        return url_info

    def test_init(self):
        response_text = "response_text"
        urls = self._get_url_set()
        for url in urls:
            instance = ConcreteParser(url, response_text)

            mylist_url = MylistURLFactory.create(url)
            self.assertEqual(mylist_url, instance.mylist_url)
            self.assertEqual(response_text, instance.response_text)

    def test_get_mylist_url(self):
        response_text = "response_text"
        urls = self._get_url_set()
        for url in urls:
            instance = ConcreteParser(url, response_text)

            actual = instance._get_mylist_url()
            mylist_url = MylistURLFactory.create(url)
            self.assertEqual(mylist_url, actual)

    def test_get_userid_mylistid(self):
        response_text = "response_text"
        urls = self._get_url_set()
        for url in urls:
            instance = ConcreteParser(url, response_text)

            actual = instance._get_userid_mylistid()
            mylist_url = MylistURLFactory.create(url)
            userid = mylist_url.userid
            mylistid = mylist_url.mylistid
            expect = (userid, mylistid)
            self.assertEqual(expect, actual)

    async def test_parse(self):
        mock_fetched_page_video_info = self.enterContext(
            patch("NNMM.video_info_fetcher.parser_base.FetchedPageVideoInfo")
        )

        def f(**kwargs):
            return kwargs

        mock_fetched_page_video_info.side_effect = f
        response_text = "response_text"
        urls = self._get_url_set()
        for url in urls:
            instance = ConcreteParser(url, response_text)

            actual = await instance.parse()
            mylist_url = MylistURLFactory.create(url)
            userid = mylist_url.userid
            mylistid = mylist_url.mylistid

            expect = {
                "no": [],
                "userid": userid,
                "mylistid": mylistid,
                "showname": "showname",
                "myshowname": "myshowname",
                "mylist_url": mylist_url,
                "video_id_list": VideoidList([]),
                "title_list": TitleList([]),
                "registered_at_list": RegisteredAtList([]),
                "video_url_list": VideoURLList([]),
            }
            self.assertEqual(expect, actual)

        mock_get_entries = MagicMock()
        mock_get_entries.side_effect = lambda: (["1", "2"], TitleList([]), RegisteredAtList([]), VideoURLList([]))
        url = urls[0]
        with self.assertRaises(ValueError):
            instance = ConcreteParser(url, response_text)
            instance._get_entries = mock_get_entries
            actual = await instance.parse()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
