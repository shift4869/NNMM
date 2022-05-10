# coding: utf-8
"""HtmlParser のテスト

HtmlParser の各種機能をテストする
"""
import asyncio
import re
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from mock import MagicMock, AsyncMock, patch, call

import freezegun
from requests_html import HTML
from NNMM.VideoInfoFetcher.FetchedPageVideoInfo import FetchedPageVideoInfo

from NNMM.VideoInfoFetcher.HtmlParser import HtmlParser
from NNMM.VideoInfoFetcher.MylistURL import MylistURL
from NNMM.VideoInfoFetcher.UploadedURL import UploadedURL
from NNMM.VideoInfoFetcher.URL import URL


class TestHtmlParser(unittest.TestCase):
    def _get_url_set(self) -> list[str]:
        """urlセットを返す
        """
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def _get_video_info(self, n: int) -> dict:
        d = {
            "video_id": f"sm1000000{n}",
            "video_url": "https://www.nicovideo.jp/watch/" + f"sm1000000{n}",
            "title": f"動画タイトル_{n}",
            "username": f"投稿者{n}",
            "uploaded_at": f"2022/05/08 00:0{n}",
            "registered_at": f"2022/05/08 01:0{n}",
            "myshowname": f"マイリスト名{n}",
        }
        return d

    def _make_html(self, error_target="", error_value="", error_del=False) -> list[dict]:
        """html を返す

        Notes:
            HTML() で解釈できる擬似的なテキストを返す
        """
        # 日付フォーマット
        SOURCE_DATETIME_FORMAT = "%Y/%m/%d %H:%M"
        DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

        # 探索対象のクラスタグ定数
        # 投稿動画ではREGISTEREDが存在しないためUPLOADEDを代替に使う
        TCT_VIDEO_URL = "NC-MediaObject-main"
        TCT_TITLE = "NC-MediaObjectTitle"
        TCT_USERNAME = "UserDetailsHeader-nickname"
        TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
        TCT_REGISTERED = "MylistItemAddition-addedAt"
        TCT_MYSHOWNAME = "MylistHeader-name"

        NUM = 5
        html = "<div>"
        for i in range(1, NUM + 1):
            d = self._get_video_info(i)

            if error_target != "":
                d[error_target] = error_value

            video_url = d["video_url"]
            title = d["title"]
            username = d["username"]
            uploaded_at = d["uploaded_at"]
            registered_at = d["registered_at"]
            myshowname = d["myshowname"]

            html += "<div>"
            if not error_del and error_target != "video_url":
                html += f"<div class={TCT_VIDEO_URL}><a href={video_url}></div>"
            if not error_del and error_target != "title":
                html += f"<div class={TCT_TITLE}>{title}</div>"
            if not error_del and error_target != "username":
                html += f"<div class={TCT_USERNAME}>{username}</div>"
            if not error_del and error_target != "uploaded_at":
                html += f"<div class={TCT_UPLOADED}>{uploaded_at}</div>"
            if not error_del and error_target != "registered_at":
                html += f"<div class={TCT_REGISTERED}>{registered_at} マイリスト登録</div>"
            if not error_del and error_target != "myshowname":
                html += f"<div class={TCT_MYSHOWNAME}>{myshowname}</div>"
            html += "</div>"

        html += "</div>"
        return html

    def test_HtmlParserInit(self):
        """HtmlParser の初期化後の状態をテストする
        """
        urls = self._get_url_set()
        for url in urls:
            html = self._make_html()
            lxml = HTML(html=html)
            hp = HtmlParser(url, lxml.lxml)

            if UploadedURL.is_valid(url):
                mylist_url = UploadedURL.factory(url)
            elif MylistURL.is_valid(url):
                mylist_url = MylistURL.factory(url)

            self.assertEqual(mylist_url, hp.mylist_url)
            self.assertEqual(lxml.lxml, hp.lxml)

            # TODO::入力値チェックを入れる

    def test_translate_pagedate(self):
        """_translate_pagedate のテスト
        """
        with ExitStack() as stack:
            SOURCE_DATETIME_FORMAT = "%Y/%m/%d %H:%M"
            DESTINATION_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

            f_now = "2022-05-08 00:50:00"
            dt_now = datetime.strptime(f_now, DESTINATION_DATETIME_FORMAT)
            mockfg = stack.enter_context(freezegun.freeze_time(f_now))

            url = self._get_url_set()[0]
            html = self._make_html()
            lxml = HTML(html=html)
            hp = HtmlParser(url, lxml.lxml)

            # 正常系
            # たった今
            expect = f_now
            actual = hp._translate_pagedate("たった今")
            self.assertEqual(expect, actual)

            # "n分前" → 現在日時 - n分前
            n = 10
            expect = (dt_now - timedelta(minutes=n)).strftime(DESTINATION_DATETIME_FORMAT)
            actual = hp._translate_pagedate(f"{n}分前")
            self.assertEqual(expect, actual)

            # "n時間前" → 現在日時 - n時間前
            n = 1
            expect = (dt_now - timedelta(hours=n)).strftime(DESTINATION_DATETIME_FORMAT)
            actual = hp._translate_pagedate(f"{n}時間前")
            self.assertEqual(expect, actual)

            # SOURCE_DATETIME_FORMAT 形式
            registered_at = f"2022/05/08 00:01"
            expect = f"2022-05-08 00:01:00"
            actual = hp._translate_pagedate(registered_at)
            self.assertEqual(expect, actual)

    def test_get_mylist_url(self):
        """_get_mylist_url のテスト
        """
        url = self._get_url_set()[0]
        html = self._make_html()
        lxml = HTML(html=html)
        hp = HtmlParser(url, lxml.lxml)
        self.assertEqual(url, hp._get_mylist_url())

        url = self._get_url_set()[2]
        hp = HtmlParser(url, lxml.lxml)
        self.assertEqual(url, hp._get_mylist_url())

    def test_get_userid_mylistid(self):
        """_get_userid_mylistid のテスト
        """
        urls = self._get_url_set()
        html = self._make_html()
        lxml = HTML(html=html)
        for url in urls:
            if UploadedURL.is_valid(url):
                mylist_url = UploadedURL.factory(url)
            elif MylistURL.is_valid(url):
                mylist_url = MylistURL.factory(url)
            expect = None
            hp = HtmlParser(mylist_url.non_query_url, lxml.lxml)
            expect = (mylist_url.userid, mylist_url.mylistid)

            actual = hp._get_userid_mylistid()
            self.assertEqual(expect, actual)

    def test_get_video_url_list(self):
        """_get_video_url_list のテスト
        """
        url = self._get_url_set()[0]
        html = self._make_html()
        lxml = HTML(html=html)

        mylist_url = URL(url).non_query_url
        hp = HtmlParser(mylist_url, lxml.lxml)

        video_url_list = []
        pattern = FetchedPageVideoInfo.VIDEO_URL_PATTERN
        video_link_lx = lxml.lxml.find_class(HtmlParser.TCT_VIDEO_URL)
        for video_link in video_link_lx:
            a = video_link.find("a")
            if re.search(pattern, a.attrib["href"]):
                video_url_list.append(a.attrib["href"])

        expect = video_url_list
        actual = hp._get_video_url_list()
        self.assertEqual(expect, actual)

    def test_get_video_id_list(self):
        """_get_video_id_list のテスト
        """
        url = self._get_url_set()[0]
        html = self._make_html()
        lxml = HTML(html=html)

        mylist_url = URL(url).non_query_url
        hp = HtmlParser(mylist_url, lxml.lxml)

        video_url_list = []
        pattern = FetchedPageVideoInfo.VIDEO_URL_PATTERN
        video_link_lx = lxml.lxml.find_class(HtmlParser.TCT_VIDEO_URL)
        for video_link in video_link_lx:
            a = video_link.find("a")
            if re.search(pattern, a.attrib["href"]):
                video_url_list.append(a.attrib["href"])

        expect = [re.findall(pattern, s)[0] for s in video_url_list]
        actual = hp._get_video_id_list()
        self.assertEqual(expect, actual)

    def test_get_title_list(self):
        """_get_title_list のテスト
        """
        url = self._get_url_set()[0]
        html = self._make_html()
        lxml = HTML(html=html)

        mylist_url = URL(url).non_query_url
        hp = HtmlParser(mylist_url, lxml.lxml)

        title_lx = lxml.lxml.find_class(HtmlParser.TCT_TITLE)
        title_list = [str(t.text) for t in title_lx]

        expect = title_list
        actual = hp._get_title_list()
        self.assertEqual(expect, actual)

    def test_get_uploaded_at_list(self):
        """_get_uploaded_at_list のテスト
        """
        url = self._get_url_set()[0]
        html = self._make_html()
        lxml = HTML(html=html)

        mylist_url = URL(url).non_query_url
        hp = HtmlParser(mylist_url, lxml.lxml)

        uploaded_at_list = []
        uploaded_at_lx = lxml.lxml.find_class(HtmlParser.TCT_UPLOADED)
        for t in uploaded_at_lx:
            dt_str = str(t.text)
            dst = hp._translate_pagedate(dt_str)
            uploaded_at_list.append(dst)

        expect = uploaded_at_list
        actual = hp._get_uploaded_at_list()
        self.assertEqual(expect, actual)

    def test_get_registered_at_list(self):
        """_get_registered_at_list のテスト
        """
        url = self._get_url_set()[0]
        html = self._make_html()
        lxml = HTML(html=html)

        mylist_url = URL(url).non_query_url
        hp = HtmlParser(mylist_url, lxml.lxml)

        registered_at_list = []
        registered_at_lx = lxml.lxml.find_class(HtmlParser.TCT_REGISTERED)
        for t in registered_at_lx:
            dt_str = str(t.text).replace(" マイリスト登録", "")
            dst = hp._translate_pagedate(dt_str)
            registered_at_list.append(dst)

        expect = registered_at_list
        actual = hp._get_registered_at_list()
        self.assertEqual(expect, actual)

    def test_get_username(self):
        """_get_username のテスト
        """
        url = self._get_url_set()[0]
        html = self._make_html()
        lxml = HTML(html=html)

        mylist_url = URL(url).non_query_url
        hp = HtmlParser(mylist_url, lxml.lxml)

        username_lx = hp.lxml.find_class(HtmlParser.TCT_USERNAME)
        username = username_lx[0].text

        expect = username
        actual = hp._get_username()
        self.assertEqual(expect, actual)

    def test_get_showname_myshowname(self):
        """_get_showname_myshowname のテスト
        """
        urls = self._get_url_set()
        html = self._make_html()
        lxml = HTML(html=html)
        for url in urls:
            expect = None
            hp = HtmlParser(URL(url).non_query_url, lxml.lxml)
            username = hp._get_username()

            if UploadedURL.is_valid(url):
                showname = f"{username}さんの投稿動画"
                myshowname = "投稿動画"
            elif MylistURL.is_valid(url):
                myshowname_lx = lxml.lxml.find_class(HtmlParser.TCT_MYSHOWNAME)
                myshowname = myshowname_lx[0].text
                showname = f"「{myshowname}」-{username}さんのマイリスト"

            expect = (showname, myshowname)

            actual = hp._get_showname_myshowname()
            self.assertEqual(expect, actual)

    def test_parse(self):
        """parse のテスト
        """
        NUM = 5
        video_info_list = []
        for i in range(1, NUM + 1):
            d = self._get_video_info(i)
            video_info_list.append(d)

        def dt(dt_str):
            dst_date = datetime.strptime(dt_str, HtmlParser.SOURCE_DATETIME_FORMAT)
            return dst_date.strftime(HtmlParser.DESTINATION_DATETIME_FORMAT)

        video_id_list = [t["video_id"] for t in video_info_list]
        title_list = [t["title"] for t in video_info_list]
        uploaded_at_list = [dt(t["uploaded_at"]) for t in video_info_list]
        registered_at_list = [dt(t["registered_at"]) for t in video_info_list]
        video_url_list = [t["video_url"] for t in video_info_list]
        username_list = [t["username"] for t in video_info_list]
        num = len(title_list)

        loop = asyncio.new_event_loop()
        urls = self._get_url_set()
        html = self._make_html()
        lxml = HTML(html=html)
        for url in urls:
            hp = HtmlParser(URL(url).non_query_url, lxml.lxml)

            username = username_list[0]
            if UploadedURL.is_valid(url):
                mylist_url = UploadedURL.factory(url)
                userid = mylist_url.userid
                mylistid = mylist_url.mylistid  # 投稿動画の場合、マイリストIDは空文字列
                showname = f"{username}さんの投稿動画"
                myshowname = "投稿動画"
                e_registered_at_list = list(uploaded_at_list)
            elif MylistURL.is_valid(url):
                mylist_url = MylistURL.factory(url)
                userid = mylist_url.userid
                mylistid = mylist_url.mylistid
                myshowname_lx = lxml.lxml.find_class(HtmlParser.TCT_MYSHOWNAME)
                myshowname = myshowname_lx[0].text
                showname = f"「{myshowname}」-{username}さんのマイリスト"
                e_registered_at_list = list(registered_at_list)

            res = {
                "no": list(range(1, num + 1)),               # No. [1, ..., len()-1]
                "userid": userid,                            # ユーザーID 1234567
                "mylistid": mylistid,                        # マイリストID 12345678
                "showname": showname,                        # マイリスト表示名 「投稿者1さんの投稿動画」
                "myshowname": myshowname,                    # マイリスト名 「投稿動画」
                "mylist_url": mylist_url.mylist_url,         # マイリストURL https://www.nicovideo.jp/user/11111111/video
                "video_id_list": video_id_list,              # 動画IDリスト [sm12345678]
                "title_list": title_list,                    # 動画タイトルリスト [テスト動画]
                "registered_at_list": e_registered_at_list,  # 登録日時リスト [%Y-%m-%d %H:%M:%S]
                "video_url_list": video_url_list,            # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
            }
            expect = FetchedPageVideoInfo(**res)

            actual = loop.run_until_complete(hp.parse())
            self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
