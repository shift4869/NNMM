import sys
import unittest
from datetime import datetime

import orjson

from nnmm.util import MylistType, find_values
from nnmm.video_info_fetcher.series_api_response_json_parser import SeriesAPIResponseJsonParser
from nnmm.video_info_fetcher.value_objects.myshowname import Myshowname
from nnmm.video_info_fetcher.value_objects.registered_at import RegisteredAt
from nnmm.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList
from nnmm.video_info_fetcher.value_objects.series_url import SeriesURL
from nnmm.video_info_fetcher.value_objects.showname import Showname
from nnmm.video_info_fetcher.value_objects.title import Title
from nnmm.video_info_fetcher.value_objects.title_list import TitleList
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.video_url_list import VideoURLList
from nnmm.video_info_fetcher.value_objects.videoid import Videoid
from nnmm.video_info_fetcher.value_objects.videoid_list import VideoidList


class TestUploadedRSSXmlParser(unittest.TestCase):
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

    def _get_mylist_info(self, mylist_url: str) -> dict:
        urls = self._get_url_set()
        urls = [URL(url).non_query_url for url in urls]
        cols = ["mylist_url", "mylist_name", "username"]
        d = {
            urls[0]: [urls[0], "投稿者1さんの投稿動画‐ニコニコ動画", "投稿者1"],
            urls[1]: [urls[1], "投稿者2さんの投稿動画‐ニコニコ動画", "投稿者2"],
            urls[2]: [urls[2], "マイリスト テスト用マイリスト1‐ニコニコ動画", "投稿者1"],
            urls[3]: [urls[3], "マイリスト テスト用マイリスト2‐ニコニコ動画", "投稿者1"],
            urls[4]: [urls[4], "マイリスト テスト用マイリスト3‐ニコニコ動画", "投稿者3"],
            urls[5]: [urls[5], "シリーズ テスト用シリーズ1‐ニコニコ動画", "投稿者1"],
        }
        return dict(zip(cols, d[mylist_url]))

    def _get_iteminfo(self, n: int) -> dict:
        d = {
            "title": f"動画タイトル_{n}",
            "video_url": "https://www.nicovideo.jp/watch/" + f"sm1000000{n}",
            "registered_at": f"2023-12-26T12:34:5{n}+09:00",
            "video_id": f"sm1000000{n}",
        }
        return d

    def _make_json(self, mylist_url) -> list[dict]:
        """json_text を返す

        Notes:
           API経由で取得される擬似的なjsonを返す
        """
        mylist_url = URL(mylist_url).non_query_url
        mylist_info = self._get_mylist_info(mylist_url)
        mylist_name = mylist_info["mylist_name"]
        username = mylist_info["username"]

        NUM = 5
        d = self._get_iteminfo(0)
        created_at = d["registered_at"]
        detail_dict = {
            "createdAt": created_at,
            "id": 123456,
            "owner": {
                "user": {
                    "nickname": username,
                },
            },
            "title": mylist_name,
        }
        items = []
        for i in range(1, NUM + 1):
            d = self._get_iteminfo(i)

            title = d["title"]
            video_url = d["video_url"]
            registered_at = d["registered_at"]
            video_id = d["video_id"]

            items.append({
                "video": {
                    "id": video_id,
                    "owner": {
                        "id": "owner_id",
                        "name": username,
                    },
                    "registeredAt": registered_at,
                    "title": title,
                }
            })
        json_dict = {
            "data": {
                "detail": detail_dict,
                "items": items,
            }
        }
        return orjson.dumps(json_dict).decode()

    def test_init(self):
        urls = self._get_url_set()
        for url in urls:
            json_text = self._make_json(url)
            json_dict = orjson.loads(json_text)
            if SeriesURL.is_valid_mylist_url(url):
                instance = SeriesAPIResponseJsonParser(url, json_text)
                self.assertEqual(json_dict, instance.json_dict)
            else:
                with self.assertRaises(ValueError):
                    instance = SeriesAPIResponseJsonParser(url, json_text)

    def test_get_username(self):
        urls = self._get_url_set()
        for url in urls:
            if not SeriesURL.is_valid_mylist_url(url):
                continue
            json_text = self._make_json(url)
            json_dict = orjson.loads(json_text)
            instance = SeriesAPIResponseJsonParser(url, json_text)

            actual = instance._get_username()
            expect = find_values(json_dict, "nickname", True, ["data", "detail", "owner", "user"], [])
            self.assertEqual(Username(expect), actual)

    def test_get_showname_myshowname(self):
        urls = self._get_url_set()
        for url in urls:
            if not SeriesURL.is_valid_mylist_url(url):
                continue
            json_text = self._make_json(url)
            json_dict = orjson.loads(json_text)
            instance = SeriesAPIResponseJsonParser(url, json_text)

            actual = instance._get_showname_myshowname()

            username = instance._get_username()
            title = find_values(json_dict, "title", True, ["data", "detail"], [])
            myshowname = Myshowname(title)
            showname = Showname.create(MylistType.series, username, myshowname)
            expect = (showname, myshowname)
            self.assertEqual(expect, actual)

    def test_get_entries(self):
        DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
        urls = self._get_url_set()
        for url in urls:
            if not SeriesURL.is_valid_mylist_url(url):
                continue
            json_text = self._make_json(url)
            json_dict = orjson.loads(json_text)
            instance = SeriesAPIResponseJsonParser(url, json_text)

            actual = instance._get_entries()

            items_dict = find_values(json_dict, "items", True, [], [])
            video_id_list = [
                Videoid(video_id) for video_id in find_values(items_dict, "id", False, ["video"], ["owner"])
            ]
            video_url_list = [
                VideoURL.create(f"https://www.nicovideo.jp/watch/{video_id.id}") for video_id in video_id_list
            ]
            title_list = [Title(title) for title in find_values(items_dict, "title", False, [], [])]
            registered_at_list = [
                RegisteredAt(datetime.fromisoformat(registered_at).strftime(DESTINATION_DATETIME_FORMAT))
                for registered_at in find_values(items_dict, "registeredAt", False, [], [])
            ]

            video_id_list = VideoidList.create(video_id_list)
            title_list = TitleList.create(title_list)
            registered_at_list = RegisteredAtList.create(registered_at_list)
            video_url_list = VideoURLList.create(video_url_list)
            expect = (video_id_list, title_list, registered_at_list, video_url_list)
            self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
