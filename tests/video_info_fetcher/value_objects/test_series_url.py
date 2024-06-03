import re
import sys
import unittest
from dataclasses import FrozenInstanceError
from urllib.parse import urlencode, urlparse, urlunparse

from mock import patch

from nnmm.video_info_fetcher.value_objects.mylistid import Mylistid
from nnmm.video_info_fetcher.value_objects.series_url import SeriesURL
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.userid import Userid


class TestSeriesURL(unittest.TestCase):
    def test_init(self):
        url = URL("https://www.nicovideo.jp/user/1234567/series/123456?ref=pc_mypage_nicorepo")
        series_url = SeriesURL(url)
        self.assertEqual(url.non_query_url, series_url.non_query_url)
        self.assertEqual(url.original_url, series_url.original_url)
        self.assertEqual(r"^https://www.nicovideo.jp/user/([0-9]+)/series/([0-9]+)$", SeriesURL.SERIES_URL_PATTERN)
        self.assertEqual("https://nvapi.nicovideo.jp/v1/series/", SeriesURL.SERIES_API_BASE_URL)

        non_query_url = series_url.non_query_url
        userid, seriesid = re.findall(SeriesURL.SERIES_URL_PATTERN, non_query_url)[0]
        self.assertEqual(Userid(userid), series_url.userid)
        self.assertEqual(Mylistid(seriesid), series_url.mylistid)

        url = "https://invalid/user/1234567/series/123456"
        with self.assertRaises(ValueError):
            series_url = SeriesURL(url)

        url = "https://www.nicovideo.jp/user/1234567/series/123456"
        with self.assertRaises(FrozenInstanceError):
            series_url = SeriesURL(url)
            series_url.original_url = url + "FrozenError"

    def test_make_action_track_id(self):
        mock_choices = self.enterContext(patch("nnmm.video_info_fetcher.value_objects.series_url.random.choices"))

        def choices(p, k):
            while len(p) < k:
                p = p + p
            return p[:k]

        mock_choices.side_effect = choices
        url = "https://www.nicovideo.jp/user/1234567/series/123456"
        instance = SeriesURL(url)
        actual = instance._make_action_track_id()
        expect = "abcdefghij_012345678901234567890123"
        self.assertEqual(expect, actual)

    def test_get_fetch_url(self):
        mock_action_track_id = self.enterContext(
            patch("nnmm.video_info_fetcher.value_objects.series_url.SeriesURL._make_action_track_id")
        )
        mock_action_track_id.side_effect = lambda: "_make_action_track_id()"

        url = "https://www.nicovideo.jp/user/1234567/series/123456"
        instance = SeriesURL(url)
        actual = instance._get_fetch_url()
        mock_action_track_id.assert_called_once_with()

        base_url = SeriesURL.SERIES_API_BASE_URL + "123456"
        query_params = {
            "Content-Type": "application/xml",
            "_frontendId": 6,
            "_frontendVersion": 0,
            "actionTrackId": "_make_action_track_id()",
        }
        query_params = urlencode(query_params, doseq=True)
        expect = urlunparse(urlparse(str(base_url))._replace(query=query_params, fragment=None))
        self.assertEqual(expect, actual)
        self.assertEqual(expect, instance.fetch_url)

    def test_create(self):
        url = "https://www.nicovideo.jp/user/1234567/series/123456?ref=pc_mypage_nicorepo"
        series_url = SeriesURL.create(url)
        self.assertEqual(url, series_url.original_url)

        url = URL("https://www.nicovideo.jp/user/1234567/series/123456?ref=pc_mypage_nicorepo")
        series_url = SeriesURL.create(url)
        self.assertEqual(url.original_url, series_url.original_url)
        self.assertEqual(url.non_query_url, series_url.non_query_url)

        url = "不正なURL"
        with self.assertRaises(ValueError):
            series_url = SeriesURL.create(url)

    def test_is_valid_mylist_url(self):
        url = "https://www.nicovideo.jp/user/1234567/series/123456?ref=pc_mypage_nicorepo"
        actual = SeriesURL.is_valid_mylist_url(url)
        self.assertEqual(True, actual)

        url = URL("https://www.nicovideo.jp/user/1234567/series/123456?ref=pc_mypage_nicorepo")
        actual = SeriesURL.is_valid_mylist_url(url)
        self.assertEqual(True, actual)

        url = "https://不正なURLアドレス/user/1234567/series/123456"
        actual = SeriesURL.is_valid_mylist_url(url)
        self.assertEqual(False, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
