# coding: utf-8
"""VideoInfoHtmlFetcher のテスト

VideoInfoHtmlFetcher の各種機能をテストする
"""

import asyncio
import re
import shutil
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from mock import MagicMock, AsyncMock, patch, call
from pathlib import Path

import freezegun
from requests_html import AsyncHTMLSession, HTML

from NNMM import GuiFunction
from NNMM import VideoInfoHtmlFetcher

RSS_PATH = "./test/rss/"


class TestVideoInfoHtmlFetcher(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if Path(RSS_PATH).exists():
            shutil.rmtree(RSS_PATH)
        pass

    def _get_url_set(self) -> list[str]:
        """urlセットを返す
        """
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def _get_mylist_url_set(self) -> list[str]:
        """mylist_urlセットを返す
        """
        mylist_url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/mylist/00000011",
            "https://www.nicovideo.jp/mylist/00000012",
            "https://www.nicovideo.jp/mylist/00000031",
        ]
        return mylist_url_info

    def _get_mylist_info_set(self, mylist_url: str) -> tuple[str, str, str]:
        """マイリスト情報セットを返す
        """
        request_url = mylist_url
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.findall(pattern, request_url):
            request_url = re.sub("/user/[0-9]+", "", request_url)

        mylist_url_info = self._get_mylist_url_set()
        mylist_info = {
            mylist_url_info[0]: ("投稿者1さんの投稿動画‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:00 +0900", "投稿者1"),
            mylist_url_info[1]: ("投稿者2さんの投稿動画‐ニコニコ動画", "Wed, 19 Oct 2021 02:00:00 +0900", "投稿者2"),
            mylist_url_info[2]: ("マイリスト 投稿者1のマイリスト1‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:01 +0900", "投稿者1"),
            mylist_url_info[3]: ("マイリスト 投稿者1のマイリスト2‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:02 +0900", "投稿者1"),
            mylist_url_info[4]: ("マイリスト 投稿者3のマイリスト1‐ニコニコ動画", "Wed, 19 Oct 2021 03:00:01 +0900", "投稿者3"),
        }
        res = mylist_info.get(request_url, ("", "", ""))
        return res

    def _get_video_info_set(self, request_url: str) -> list[tuple[str, str, str]]:
        """動画情報セットを返す
        """
        mylist_url = request_url
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.findall(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)

        mylist_url_info = self._get_mylist_url_set()
        m_range = {
            mylist_url_info[0]: range(1, 10),
            mylist_url_info[1]: range(1, 10),
            mylist_url_info[2]: range(1, 5),
            mylist_url_info[3]: range(5, 10),
            mylist_url_info[4]: range(1, 10),
        }.get(mylist_url, [])

        pattern = r"https://www.nicovideo.jp/user/([0-9]{8})/.*"
        if re.findall(pattern, request_url):
            userid = re.findall(pattern, request_url)[0]
        else:
            userid = request_url[-2]
        n = userid[0]

        res = []
        src_df = "%Y-%m-%dT%H:%M:%S%z"
        dst_df = "%Y-%m-%d %H:%M:%S"
        for i in m_range:
            video_id = f"sm{n}00000{i:02}"
            video_info = self._get_video_info(video_id)
            uploaded_at = datetime.strptime(video_info["uploaded_at"], src_df).strftime(dst_df)

            rd = datetime.strptime(video_info["uploaded_at"], src_df)
            rd += timedelta(minutes=1)
            registered_at = rd.strftime(dst_df)

            video_info["uploaded_at"] = uploaded_at
            video_info["registered_at"] = registered_at
            res.append(video_info)

        return res

    def _get_video_info(self, video_id: str) -> list[tuple[str, str, str]]:
        """動画情報を返す
        """
        # video_idのパターンはsm{投稿者id}00000{動画識別2桁}
        pattern = r"sm([0-9]{1})00000([0-9]{2})"
        n, m = re.findall(pattern, video_id)[0]
        title = f"動画タイトル{n}_{m}"
        uploaded_at = f"2022-04-29T0{n}:{m}:00+09:00"
        video_url = "https://www.nicovideo.jp/watch/" + video_id
        user_id = n * 8
        username = f"動画投稿者{n}"

        res = {
            "video_id": video_id,         # 動画ID [sm12345678]
            "title": title,               # 動画タイトル [テスト動画]
            "uploaded_at": uploaded_at,   # 投稿日時 [%Y-%m-%d %H:%M:%S]
            "video_url": video_url,       # 動画URL [https://www.nicovideo.jp/watch/sm12345678]
            "user_id": user_id,           # 投稿者id [投稿者1]
            "username": username,         # 投稿者 [投稿者1]
        }
        return res

    def _get_xml_from_api(self, video_id: str) -> str:
        """APIから返ってくる動画情報セットxmlを返す
        """
        video_info = self._get_video_info(video_id)
        title = video_info.get("title")
        first_retrieve = video_info.get("uploaded_at")
        watch_url = video_info.get("video_url")
        user_id = video_info.get("user_id")
        user_nickname = video_info.get("username")

        xml = """<?xml version="1.0" encoding="utf-8"?>
                    <nicovideo_thumb_response status="ok">
                        <thumb>"""
        xml += f"""<video_id>{video_id}</video_id>
                <title>{title}</title>
                <first_retrieve>{first_retrieve}</first_retrieve>
                <watch_url>{watch_url}</watch_url>
                <user_id>{user_id}</user_id>
                <user_nickname>{user_nickname}</user_nickname>"""
        xml += """</thumb>
                    </nicovideo_thumb_response>"""

        return xml

    def _make_response_mock(self, request_url, status_code: int = 200, error_target: str = ""):
        mock = MagicMock()

        def return_href(val):
            r_href = MagicMock()
            r_attrib = MagicMock()
            r_attrib.attrib = {"href": val}
            r_href.find = lambda key: r_attrib if key == "a" else None
            return r_href

        def return_text(val):
            r_text = MagicMock()
            r_text.text = val
            return r_text

        def return_find_class(name):
            result = []

            mylist_url = request_url
            mylist_info = self._get_mylist_info_set(mylist_url)
            video_info_list = self._get_video_info_set(mylist_url)

            src_df = "%Y-%m-%d %H:%M:%S"
            dst_df = "%Y/%m/%d %H:%M"
            if name == error_target:
                result = []
            elif name == "NC-MediaObject-main":
                result = [return_href(video_info["video_url"]) for video_info in video_info_list]
            elif name == "NC-MediaObjectTitle":
                result = [return_text(video_info["title"]) for video_info in video_info_list]
            elif name == "NC-VideoRegisteredAtText-text":
                result = [return_text(datetime.strptime(video_info["uploaded_at"], src_df).strftime(dst_df)) for video_info in video_info_list]
            elif name == "MylistItemAddition-addedAt":
                result = [return_text(datetime.strptime(video_info["registered_at"], src_df).strftime(dst_df)) for video_info in video_info_list]
            elif name == "UserDetailsHeader-nickname":
                result = [return_text(mylist_info[2])]
            elif name == "MylistHeader-name":
                result = [return_text(mylist_info[0].replace("‐ニコニコ動画", ""))]
            return result

        mock.html.lxml.find_class = return_find_class
        return mock

    def _make_api_response_mock(self, request_url, status_code: int = 200, error_target: str = ""):
        mock = MagicMock()

        pattern = "^https://ext.nicovideo.jp/api/getthumbinfo/(sm[0-9]+)$"
        video_id = re.findall(pattern, request_url)[0]
        xml = self._get_xml_from_api(video_id)
        html = HTML(html=xml)

        mock.html = html
        return mock

    def _make_session_response_mock(self, mock, status_code: int = 200, error_target: str = "") -> tuple[AsyncMock, MagicMock]:
        async def return_session_response(request_url: str,
                                          do_rendering: bool = False,
                                          parse_features: str = "html.parser",
                                          session: AsyncHTMLSession = None) -> tuple[AsyncMock, MagicMock]:
            ar_session = AsyncMock()
            if error_target == "ValueError":
                raise ValueError
            if status_code == 503:
                return (ar_session, None)

            r_response = self._make_response_mock(request_url, status_code, error_target)
            return (ar_session, r_response)

        mock.side_effect = return_session_response
        return mock

    def _make_api_session_response_mock(self, mock, status_code: int = 200, error_target: str = "") -> tuple[AsyncMock, MagicMock]:
        async def return_session_response(request_url: str, do_rendering: bool, session: AsyncHTMLSession = None) -> tuple[AsyncMock, MagicMock]:
            ar_session = AsyncMock()
            if error_target == "ValueError":
                raise ValueError
            if status_code == 503:
                return (ar_session, None)

            r_response = self._make_api_response_mock(request_url, status_code, error_target)
            return (ar_session, r_response)

        mock.side_effect = return_session_response
        return mock

    def _make_analysis_html_mock(self, mock, url: str = "", kind: str = ""):
        url_type = GuiFunction.GetURLType(url)
        mylist_url = url

        mylist_info = self._get_mylist_info_set(mylist_url)
        video_info_list = self._get_video_info_set(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        registered_at_list = [video_info["registered_at"] for video_info in video_info_list]

        if url_type == "uploaded":
            username = mylist_info[2]
            showname = f"{username}さんの投稿動画"
            myshowname = "投稿動画"
        elif url_type == "mylist":
            username = mylist_info[2]
            myshowname = mylist_info[0].replace("‐ニコニコ動画", "")
            showname = f"「{myshowname}」-{username}さんのマイリスト"

        html_result = {
            "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
            "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        }

        def return_html(lxml):
            if kind == "AttributeError":
                raise AttributeError
            return html_result

        mock.side_effect = return_html
        return mock

    def _make_get_videoinfo_from_api_mock(self, mock, url: str = "", kind: str = ""):
        mylist_url = url

        video_info_list = self._get_video_info_set(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        video_id_list = [video_info["video_id"] for video_info in video_info_list]
        video_url_list = [video_info["video_url"] for video_info in video_info_list]
        username_list = [video_info["username"] for video_info in video_info_list]

        api_result = {
            "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
            "title_list": title_list,               # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
            "username_list": username_list,         # 投稿者リスト [投稿者1]
        }

        if kind == "TitleError":
            api_result["title_list"] = [t + "_不正なタイトル名" for t in title_list]
        if kind == "VideoUrlError":
            api_result["video_url_list"] = [v + "_不正なタイトル名" for v in video_url_list]
        if kind == "UsernameError":
            api_result["username_list"] = []

        def return_api(v):
            if kind == "ValueError":
                raise ValueError
            return api_result

        mock.side_effect = return_api
        return mock

    def _make_expect_result(self, url):
        url_type = GuiFunction.GetURLType(url)
        mylist_url = url

        mylist_info = self._get_mylist_info_set(mylist_url)
        video_info_list = self._get_video_info_set(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        registered_at_list = [video_info["registered_at"] for video_info in video_info_list]
        video_id_list = [video_info["video_id"] for video_info in video_info_list]
        video_url_list = [video_info["video_url"] for video_info in video_info_list]
        username_list = [video_info["username"] for video_info in video_info_list]

        if url_type == "uploaded":
            username = mylist_info[2]
            showname = f"{username}さんの投稿動画"
            myshowname = "投稿動画"
        elif url_type == "mylist":
            username = mylist_info[2]
            myshowname = mylist_info[0].replace("‐ニコニコ動画", "")
            showname = f"「{myshowname}」-{username}さんのマイリスト"

        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
        res = []
        for video_id, title, uploaded_at, registered_at, username, video_url in zip(video_id_list, title_list, uploaded_at_list, registered_at_list, username_list, video_url_list):
            # 出力インターフェイスチェック
            value_list = [-1, video_id, title, username, "", uploaded_at, registered_at, video_url, mylist_url, showname, myshowname]
            if len(table_cols) != len(value_list):
                continue

            # 登録
            res.append(dict(zip(table_cols, value_list)))

        # No.を付記する
        for i, _ in enumerate(res):
            res[i]["no"] = i + 1

        return res

    def test_init(self):
        """VideoInfoHtmlFetcher の初期化後の状態をテストする
        """
        source_type = "html"
        urls = self._get_url_set()
        for url in urls:
            vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)

            self.assertEqual(source_type, vihf.source_type)

            # 探索対象のクラスタグ定数
            TCT_TITLE = "NC-MediaObjectTitle"
            TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
            TCT_USERNAME = "UserDetailsHeader-nickname"
            TCT_REGISTERED = "MylistItemAddition-addedAt"
            TCT_MYSHOWNAME = "MylistHeader-name"
            self.assertEqual(TCT_TITLE, vihf.TCT_TITLE)
            self.assertEqual(TCT_UPLOADED, vihf.TCT_UPLOADED)
            self.assertEqual(TCT_USERNAME, vihf.TCT_USERNAME)
            self.assertEqual(TCT_REGISTERED, vihf.TCT_REGISTERED)
            self.assertEqual(TCT_MYSHOWNAME, vihf.TCT_MYSHOWNAME)

            # エラーメッセージ定数
            MSG_TITLE = f"title parse failed. '{TCT_TITLE}' is not found."
            MSG_UPLOADED1 = f"uploaded_at parse failed. '{TCT_UPLOADED}' is not found."
            MSG_UPLOADED2 = "uploaded_at date parse failed."
            MSG_REGISTERED1 = f"registered_at parse failed. '{TCT_REGISTERED}' is not found."
            MSG_REGISTERED2 = "registered_at date parse failed."
            MSG_USERNAME = f"username parse failed. '{TCT_USERNAME}' is not found."
            MSG_MYSHOWNAME = f"myshowname parse failed. '{TCT_MYSHOWNAME}' is not found."
            self.assertEqual(MSG_TITLE, vihf.MSG_TITLE)
            self.assertEqual(MSG_UPLOADED1, vihf.MSG_UPLOADED1)
            self.assertEqual(MSG_UPLOADED2, vihf.MSG_UPLOADED2)
            self.assertEqual(MSG_REGISTERED1, vihf.MSG_REGISTERED1)
            self.assertEqual(MSG_REGISTERED2, vihf.MSG_REGISTERED2)
            self.assertEqual(MSG_USERNAME, vihf.MSG_USERNAME)
            self.assertEqual(MSG_MYSHOWNAME, vihf.MSG_MYSHOWNAME)

    def test_translate_pagedate(self):
        """_translate_pagedate のテスト
        """
        with ExitStack() as stack:
            f_now = "2022-05-01 00:50:00"
            mockfg = stack.enter_context(freezegun.freeze_time(f_now))

            url = self._get_url_set()[0]
            vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)

            # 正常系
            # "たった今" → 現在日時
            td_str = "たった今"
            actual = vihf._translate_pagedate(td_str)
            expect = f_now
            self.assertEqual(expect, actual)

            # "n分前" → 現在日時 - n分前
            src_df = "%Y-%m-%d %H:%M:%S"
            dst_df = "%Y-%m-%d %H:%M:%S"
            n = 10
            td_str = f"{n}分前"
            actual = vihf._translate_pagedate(td_str)
            expect = (datetime.strptime(f_now, src_df) + timedelta(minutes=-n)).strftime(dst_df)
            self.assertEqual(expect, actual)

            # "n時間前" → 現在日時 - n時間前
            n = 1
            td_str = f"{n}時間前"
            actual = vihf._translate_pagedate(td_str)
            expect = (datetime.strptime(f_now, src_df) + timedelta(hours=-n)).strftime(dst_df)
            self.assertEqual(expect, actual)

            # 異常系
            # 不正な文字列
            td_str = "不正な文字列"
            actual = vihf._translate_pagedate(td_str)
            self.assertEqual("", actual)

            # 空文字列
            td_str = ""
            actual = vihf._translate_pagedate(td_str)
            self.assertEqual("", actual)

            # n分前だがnが不正
            td_str = "不正分前"
            actual = vihf._translate_pagedate(td_str)
            self.assertEqual("", actual)

    def test_analysis_uploaded_page(self):
        """_analysis_uploaded_page のテスト
        """
        # 探索対象のクラスタグ定数
        TCT_TITLE = "NC-MediaObjectTitle"
        TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
        TCT_USERNAME = "UserDetailsHeader-nickname"

        # 正常系
        expect = {}
        mylist_url = self._get_url_set()[0]
        mylist_info = self._get_mylist_info_set(mylist_url)
        video_info_list = self._get_video_info_set(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        registered_at_list = uploaded_at_list

        username = mylist_info[2]
        showname = f"{username}さんの投稿動画"
        myshowname = "投稿動画"

        expect = {
            "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
            "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        }

        response = self._make_response_mock(mylist_url)
        vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(mylist_url)
        loop = asyncio.new_event_loop()
        actual = loop.run_until_complete(vihf._analysis_uploaded_page(response.html.lxml))
        self.assertEqual(expect, actual)

        # 異常系
        # 動画名収集失敗
        with self.assertRaises(AttributeError):
            response = self._make_response_mock(mylist_url, 200, TCT_TITLE)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_uploaded_page(response.html.lxml))

        # 投稿日時収集失敗
        with self.assertRaises(AttributeError):
            response = self._make_response_mock(mylist_url, 200, TCT_UPLOADED)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_uploaded_page(response.html.lxml))

        # TODO::投稿日時収集は成功するが解釈に失敗

        # 投稿者収集失敗
        with self.assertRaises(AttributeError):
            response = self._make_response_mock(mylist_url, 200, TCT_USERNAME)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_uploaded_page(response.html.lxml))

    def test_analysis_mylist_page(self):
        """_analysis_mylist_page のテスト
        """
        # 探索対象のクラスタグ定数
        TCT_TITLE = "NC-MediaObjectTitle"
        TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
        TCT_REGISTERED = "MylistItemAddition-addedAt"
        TCT_USERNAME = "UserDetailsHeader-nickname"
        TCT_MYSHOWNAME = "MylistHeader-name"

        # 正常系
        expect = {}
        mylist_url = self._get_url_set()[0]
        mylist_info = self._get_mylist_info_set(mylist_url)
        video_info_list = self._get_video_info_set(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        registered_at_list = [video_info["registered_at"] for video_info in video_info_list]

        username = mylist_info[2]
        myshowname = mylist_info[0].replace("‐ニコニコ動画", "")
        showname = f"「{myshowname}」-{username}さんのマイリスト"

        expect = {
            "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
            "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        }

        response = self._make_response_mock(mylist_url)
        vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(mylist_url)
        loop = asyncio.new_event_loop()
        actual = loop.run_until_complete(vihf._analysis_mylist_page(response.html.lxml))
        self.assertEqual(expect, actual)

        # 異常系
        # 動画名収集失敗
        with self.assertRaises(AttributeError):
            response = self._make_response_mock(mylist_url, 200, TCT_TITLE)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_mylist_page(response.html.lxml))

        # 投稿日時収集失敗
        with self.assertRaises(AttributeError):
            response = self._make_response_mock(mylist_url, 200, TCT_UPLOADED)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_mylist_page(response.html.lxml))

        # TODO::投稿日時収集は成功するが解釈に失敗

        # 登録日時収集失敗
        with self.assertRaises(AttributeError):
            response = self._make_response_mock(mylist_url, 200, TCT_REGISTERED)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_mylist_page(response.html.lxml))

        # TODO::登録日時収集は成功するが解釈に失敗

        # 投稿者収集失敗
        with self.assertRaises(AttributeError):
            response = self._make_response_mock(mylist_url, 200, TCT_USERNAME)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_mylist_page(response.html.lxml))

        # マイリスト名収集失敗
        with self.assertRaises(AttributeError):
            response = self._make_response_mock(mylist_url, 200, TCT_MYSHOWNAME)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_mylist_page(response.html.lxml))

    def test_analysis_html(self):
        """_analysis_html のテスト
        """
        with ExitStack() as stack:
            mockaup = stack.enter_context(patch("NNMM.VideoInfoHtmlFetcher.VideoInfoHtmlFetcher._analysis_uploaded_page"))
            mockamp = stack.enter_context(patch("NNMM.VideoInfoHtmlFetcher.VideoInfoHtmlFetcher._analysis_mylist_page"))

            mockaup.return_value = "_analysis_uploaded_page result"
            mockamp.return_value = "_analysis_mylist_page result"

            # 投稿動画ページ
            url = self._get_url_set()[0]
            vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
            video_id_list = []
            lxml = None
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_html(lxml))
            expect = "_analysis_uploaded_page result"
            self.assertEqual(expect, actual)
            mockaup.assert_called_once_with(lxml)
            mockaup.reset_mock()
            mockamp.assert_not_called()
            mockamp.reset_mock()

            # マイリストページ
            url = self._get_url_set()[2]
            vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._analysis_html(lxml))
            expect = "_analysis_mylist_page result"
            self.assertEqual(expect, actual)
            mockaup.assert_not_called()
            mockaup.reset_mock()
            mockamp.assert_called_once_with(lxml)
            mockamp.reset_mock()

            # 異常系
            # 不正なurlタイプ
            with self.assertRaises(ValueError):
                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                vihf.url_type = "invalid url type"
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(vihf._analysis_html(lxml))

    def test_fetch_videoinfo_from_html(self):
        """_fetch_videoinfo_from_html のテスト
        """
        with ExitStack() as stack:
            mocklw = stack.enter_context(patch("NNMM.VideoInfoHtmlFetcher.logger.warning"))
            mockses = stack.enter_context(patch("NNMM.VideoInfoHtmlFetcher.VideoInfoHtmlFetcher._get_session_response"))
            mockhtml = stack.enter_context(patch("NNMM.VideoInfoHtmlFetcher.VideoInfoHtmlFetcher._analysis_html"))
            mockhapi = stack.enter_context(patch("NNMM.VideoInfoHtmlFetcher.VideoInfoHtmlFetcher._get_videoinfo_from_api"))

            # 正常系
            # 動画情報が存在するマイリストを指定
            mockses = self._make_session_response_mock(mockses, 200)
            urls = self._get_url_set()
            for url in urls:
                mockhtml = self._make_analysis_html_mock(mockhtml, url)
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url)

                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())
                expect = self._make_expect_result(url)
                self.assertEqual(expect, actual)

            # 動画情報が1つもないマイリストを指定
            # 正確にはエラーではない(warning)が結果として空リストが返ってくる
            url = "https://www.nicovideo.jp/user/99999999/mylist/99999999"
            vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
            actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())
            self.assertEqual([], actual)

            # 異常系
            # session.getが常に失敗
            with self.assertRaises(ValueError):
                mockses = self._make_session_response_mock(mockses, 503)
                url = urls[0]
                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())

            # session.getが例外送出
            with self.assertRaises(ValueError):
                mockses = self._make_session_response_mock(mockses, 503, "ValueError")
                url = urls[0]
                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())

            # htmlからの動画情報収集に失敗
            with self.assertRaises(AttributeError):
                mockhtml = self._make_analysis_html_mock(mockhtml, url, "AttributeError")
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url)
                mockses = self._make_session_response_mock(mockses, 200)
                url = urls[0]
                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())

            # apiからの動画情報収集に失敗
            with self.assertRaises(ValueError):
                mockhtml = self._make_analysis_html_mock(mockhtml, url)
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url, "ValueError")
                mockses = self._make_session_response_mock(mockses, 200)
                url = urls[0]
                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())

            # 取得したtitleの情報がhtmlとapiで異なる
            with self.assertRaises(ValueError):
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url, "TitleError")
                mockses = self._make_session_response_mock(mockses, 200)
                url = urls[0]
                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())

            # 取得したvideo_urlの情報がhtmlとapiで異なる
            with self.assertRaises(ValueError):
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url, "VideoUrlError")
                mockses = self._make_session_response_mock(mockses, 200)
                url = urls[0]
                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())

            # username_listの大きさが不正
            with self.assertRaises(ValueError):
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url, "UsernameError")
                mockses = self._make_session_response_mock(mockses, 200)
                url = urls[0]
                vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
                actual = loop.run_until_complete(vihf._fetch_videoinfo_from_html())

            # TODO::結合時のエラーを模倣する

    def test_fetch_videoinfo(self):
        """_fetch_videoinfo のテスト
        """
        with ExitStack() as stack:
            mockfvft = stack.enter_context(patch("NNMM.VideoInfoHtmlFetcher.VideoInfoHtmlFetcher._fetch_videoinfo_from_html"))

            expect = "VideoInfoHtmlFetcher._fetch_videoinfo() called"
            mockfvft.side_effect = lambda: str(expect)

            url = self._get_url_set()[0]
            vihf = VideoInfoHtmlFetcher.VideoInfoHtmlFetcher(url)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(vihf._fetch_videoinfo())
            self.assertEqual(expect, actual)
            mockfvft.assert_called_once()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
