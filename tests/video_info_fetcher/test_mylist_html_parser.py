import sys
import unittest

import orjson

from nnmm.video_info_fetcher.mylist_html_parser import MylistHtmlParser


class TestMylistHtmlParser(unittest.TestCase):
    def setUp(self):
        self.mylist_url = "https://www.nicovideo.jp/user/6063658/mylist/72036443"
        self.response_text = self._make_response_text()
        return super().setUp()

    def _make_response_text(self):
        return orjson.dumps({
            "data": {
                "mylist": {
                    "name": "テストマイリスト",
                    "owner": {
                        "name": "テストユーザー",
                    },
                    "items": [
                        {
                            "video": {
                                "id": "sm9",
                                "title": "テスト動画",
                                "registeredAt": "2024-01-02T03:04:05+09:00",
                                "owner": {
                                    "name": "投稿者",
                                },
                            }
                        }
                    ],
                }
            }
        }).decode()

    def test_init(self):
        parser = MylistHtmlParser(
            self.mylist_url,
            self.response_text,
        )

        self.assertEqual(parser.data["data"]["mylist"]["name"], "テストマイリスト")

    def test_get_username(self):
        parser = MylistHtmlParser(
            self.mylist_url,
            self.response_text,
        )
        actual = parser._get_username().name
        self.assertEqual("テストユーザー", actual)

    def test_get_showname_myshowname(self):
        parser = MylistHtmlParser(
            self.mylist_url,
            self.response_text,
        )

        showname, myshowname = parser._get_showname_myshowname()

        self.assertEqual("テストマイリスト", myshowname.name)
        self.assertEqual("「テストマイリスト」-テストユーザーさんのマイリスト", showname.name)

    def test_get_entries(self):
        parser = MylistHtmlParser(
            self.mylist_url,
            self.response_text,
        )

        (
            video_ids,
            titles,
            mylist_ats,
            video_urls,
            usernames,
        ) = parser._get_entries()

        self.assertEqual("sm9", video_ids._list[0].id)
        self.assertEqual("テスト動画", titles._list[0].name)
        self.assertEqual("2024-01-02 03:04:05", mylist_ats._list[0]._datetime)
        self.assertEqual("https://www.nicovideo.jp/watch/sm9", video_urls._list[0].non_query_url)
        self.assertEqual("投稿者", usernames._list[0].name)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
