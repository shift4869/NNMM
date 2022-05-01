# coding: utf-8
"""GetMyListInfoFromRss のテスト

GetMyListInfoFromRss の各種機能をテストする
"""

import asyncio
import re
import shutil
import sys
import unittest
import urllib.parse
import warnings
from contextlib import ExitStack
from datetime import datetime, timedelta
from mock import MagicMock, patch, AsyncMock
from pathlib import Path
from urllib.error import HTTPError

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from requests_html import HTML

from NNMM import GuiFunction
from NNMM import GetMyListInfoFromRss

RSS_PATH = "./test/rss/"


class TestGetMyListInfoFromRss(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
        warnings.simplefilter("ignore", ResourceWarning)
        pass

    def tearDown(self):
        if Path(RSS_PATH).exists():
            shutil.rmtree(RSS_PATH)
        pass

    def __GetURLSet(self) -> list[str]:
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

    def __GetMylistURLSet(self) -> list[str]:
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

    def __GetMylistInfoSet(self, mylist_url: str) -> tuple[str, str, str]:
        """マイリスト情報セットを返す
        """
        mylist_url_info = self.__GetMylistURLSet()
        mylist_info = {
            mylist_url_info[0]: ("投稿者1さんの投稿動画‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:00 +0900", "投稿者1"),
            mylist_url_info[1]: ("投稿者2さんの投稿動画‐ニコニコ動画", "Wed, 19 Oct 2021 02:00:00 +0900", "投稿者2"),
            mylist_url_info[2]: ("マイリスト 投稿者1のマイリスト1‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:01 +0900", "投稿者1"),
            mylist_url_info[3]: ("マイリスト 投稿者1のマイリスト2‐ニコニコ動画", "Wed, 19 Oct 2021 01:00:02 +0900", "投稿者1"),
            mylist_url_info[4]: ("マイリスト 投稿者3のマイリスト1‐ニコニコ動画", "Wed, 19 Oct 2021 03:00:01 +0900", "投稿者3"),
        }
        res = mylist_info.get(mylist_url, ("", "", ""))
        return res

    def __GetVideoInfoSet(self, mylist_url: str) -> list[tuple[str, str, str]]:
        """動画情報セットを返す
        """
        mylist_url_info = self.__GetMylistURLSet()
        m_range = {
            mylist_url_info[0]: range(1, 10),
            mylist_url_info[1]: range(1, 10),
            mylist_url_info[2]: range(1, 5),
            mylist_url_info[3]: range(5, 10),
            mylist_url_info[4]: range(1, 10),
        }.get(mylist_url, range(1, 10))

        # "https://www.nicovideo.jp/user/22222222/video"
        # "https://www.nicovideo.jp/mylist/00000011"
        pattern = r"https://www.nicovideo.jp/user/([0-9]{8})/.*"
        if re.findall(pattern, mylist_url):
            userid = re.findall(pattern, mylist_url)[0]
        else:
            userid = "33333333"
        n = userid[0]

        res = []
        src_df = "%Y-%m-%dT%H:%M:%S%z"
        dst_df = "%Y-%m-%d %H:%M:%S"
        for i in m_range:
            video_id = f"sm{n}00000{i:02}"
            video_info = self.__GetVideoInfo(video_id)
            uploaded_at = datetime.strptime(video_info["uploaded_at"], src_df).strftime(dst_df)

            rd = datetime.strptime(video_info["uploaded_at"], src_df)
            rd += timedelta(minutes=1)
            registered_at = rd.strftime(dst_df)

            video_info["uploaded_at"] = uploaded_at
            video_info["registered_at"] = registered_at
            res.append(video_info)

        return res

    def __GetVideoInfo(self, video_id: str) -> list[tuple[str, str, str]]:
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

    def __GetXMLFromAPI(self, video_id: str) -> str:
        """APIから返ってくる動画情報セットxmlを返す
        """
        video_info = self.__GetVideoInfo(video_id)
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

    def __GetXMLFromRSS(self, mylist_url: str) -> str:
        """RSS取得時に返されるxmlを作成する

        Args:
            mylist_url (str): 対象マイリストURL

        Returns:
            str: 成功時 生成したxml, 失敗時 空文字列
        """
        # クエリ除去
        mylist_url = urllib.parse.urlunparse(
            urllib.parse.urlparse(mylist_url)._replace(query=None)
        )

        # マイリストのURLならRSSが取得できるURLに加工
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        # マイリスト情報加工
        title, uploaded, username = self.__GetMylistInfoSet(mylist_url)
        xml = f"""
            <?xml version="1.0" encoding="utf-8"?>
            <rss version="2.0"
                    xmlns:dc="http://purl.org/dc/elements/1.1/"
                    xmlns:atom="http://www.w3.org/2005/Atom">
            <channel>
                <title>{title}</title>
                <link>{mylist_url}?ref=rss_mylist_rss2</link>
                <description></description>
                <pubDate>{uploaded}</pubDate>
                <dc:creator>{username}</dc:creator>
        """

        # 動画情報加工
        src_df = "%Y-%m-%d %H:%M:%S"
        dst_df = "%a, %d %b %Y %H:%M:%S +0900"
        video_info = self.__GetVideoInfoSet(mylist_url)
        for item in reversed(video_info):
            title = item.get("title")
            video_url = item.get("video_url")
            registered_at = item.get("registered_at")

            rd = datetime.strptime(item["registered_at"], src_df)
            registered_at = rd.strftime(dst_df)

            xml += f"""
                <item>
                    <title>{title}</title>
                    <link>{video_url}?ref=rss_mylist_rss2</link>
                    <pubDate>{registered_at}</pubDate>
                    <description><![CDATA[<p></p>]]></description>
                </item>
            """

        xml += "</channel></rss>"
        return xml

    def __MakeEventLoopMock(self, retry_count=0, html_error=False) -> AsyncMock:
        """asyncio.get_event_loop にパッチするモックを作成する

        Notes:
            asyncのrun_in_executor の呼び出しを模倣する

        Returns:
            AsyncMock: run_in_executor が呼び出せるモック
        """
        r_response = AsyncMock()
        global count
        count = retry_count

        async def ReturnRunInExecutor(s, executor, func, args):
            r = MagicMock()
            global count
            if count <= 0:
                suffix = "?rss=2.0"
                request_url = str(args).replace(suffix, "")

                # 想定されるアドレスかどうか
                urls = self.__GetMylistURLSet()
                if request_url in urls:
                    r.text = self.__GetXMLFromRSS(request_url)
                else:
                    raise HTTPError

                if html_error:
                    raise HTTPError
            else:
                count = count - 1
                raise HTTPError
            return r
        type(r_response).run_in_executor = ReturnRunInExecutor
        return r_response

    def __MakeAPIResponseMock(self, status_code: int = 200, error_target: str = "") -> AsyncMock:
        """AsyncHTMLSession にパッチするモックを作成する（動画情報API用）
        """
        r_response = AsyncMock()

        async def ReturnGet(s, url):
            r = MagicMock()

            if error_target == "HTTPError":
                raise HTTPError
            if status_code == 503:
                return None

            pattern = "^https://ext.nicovideo.jp/api/getthumbinfo/(sm[0-9]+)$"
            video_id = re.findall(pattern, url)[0]
            xml = self.__GetXMLFromAPI(video_id)
            html = HTML(html=xml)

            r.html = html
            return r
        type(r_response).get = ReturnGet
        return r_response

    def __MakeAPISessionResponseMock(self, mock, status_code: int = 200, error_target: str = "") -> tuple[AsyncMock, MagicMock]:
        def ReturnAsyncHTMLSession():
            r_response = self.__MakeAPIResponseMock(status_code, error_target)
            return r_response

        mock.side_effect = ReturnAsyncHTMLSession
        return mock

    def __MakeConfigMock(self) -> dict:
        """Configから取得できるRSS書き出し先のパスを返すモックを作成する

        Returns:
            dict: Configアクセスを模倣する辞書
        """
        return {"general": {"rss_save_path": RSS_PATH}}

    def __MakeAnalysisSoupMock(self, mock, url: str = "", kind: str = ""):
        url_type = GuiFunction.GetURLType(url)
        mylist_url = url

        # マイリストのURLならRSSが取得できるURLに加工
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        mylist_info = self.__GetMylistInfoSet(mylist_url)
        video_info_list = self.__GetVideoInfoSet(mylist_url)
        video_id_list = [video_info["video_id"] for video_info in video_info_list]
        title_list = [video_info["title"] for video_info in video_info_list]
        registered_at_list = [video_info["registered_at"] for video_info in video_info_list]
        video_url_list = [video_info["video_url"] for video_info in video_info_list]

        if url_type == "uploaded":
            pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/video"
            userid = re.findall(pattern, url)[0]
            mylistid = ""
            username = mylist_info[2]
            showname = f"{username}さんの投稿動画"
            myshowname = "投稿動画"
        elif url_type == "mylist":
            pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)"
            userid, mylistid = re.findall(pattern, url)[0]
            username = mylist_info[2]
            myshowname = mylist_info[0].replace("‐ニコニコ動画", "")
            showname = f"「{myshowname}」-{username}さんのマイリスト"

        soup_result = {
            "userid": userid,                           # ユーザーID 1234567
            "mylistid": mylistid,                       # マイリストID 12345678
            "showname": showname,                       # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
            "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
            "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        }

        def ReturnSoup(type: str, url: str, soup: BeautifulSoup):
            if kind == "ValueError":
                raise ValueError
            return soup_result

        mock.side_effect = ReturnSoup
        return mock

    def __MakeGetUsernameFromApiMock(self, mock, url: str = "", kind: str = ""):
        mylist_url = url

        # マイリストのURLならRSSが取得できるURLに加工
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        video_info_list = self.__GetVideoInfoSet(mylist_url)
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

        def ReturnApi(v):
            if kind == "HTTPError":
                raise HTTPError
            return api_result

        mock.side_effect = ReturnApi
        return mock

    def __MakeExpectResult(self, url):
        url_type = GuiFunction.GetURLType(url)
        mylist_url = url

        # マイリストのURLならRSSが取得できるURLに加工
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        mylist_info = self.__GetMylistInfoSet(mylist_url)
        video_info_list = self.__GetVideoInfoSet(mylist_url)
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
            value_list = [-1, video_id, title, username, "", uploaded_at, registered_at, video_url, url, showname, myshowname]
            if len(table_cols) != len(value_list):
                continue

            # 登録
            res.append(dict(zip(table_cols, value_list)))

        # No.を付記する
        for i, _ in enumerate(res):
            res[i]["no"] = i + 1

        return res

    def test_GetMyListInfoFromRss(self):
        """GetMyListInfoFromRss のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.logger.warning"))
            mockcpb = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig", self.__MakeConfigMock))
            mockgel = stack.enter_context(patch("asyncio.get_event_loop"))
            mocksoup = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.AnalysisSoup"))
            mockhapi = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.GetUsernameFromApi"))

            # 正常系
            mockgel.return_value = self.__MakeEventLoopMock()
            urls = self.__GetURLSet()
            for url in urls:
                mocksoup = self.__MakeAnalysisSoupMock(mocksoup, url)
                mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url)

                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                expect = self.__MakeExpectResult(url)
                self.assertEqual(expect, actual)

            # 異常系
            # 入力URLが不正
            url = "https://不正なURL/user/11111111/video"
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
            self.assertEqual([], actual)

            # urlパース失敗
            with patch("NNMM.GuiFunction.GetURLType", lambda x: "mylist"):
                url = "https://不正なURL/user/11111111/video"
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                self.assertEqual([], actual)

            # RSS取得が常に失敗
            # with patch("NNMM.GetMyListInfoFromRss.BeautifulSoup", lambda t, p: None):
            #     url = urls[0]
            #     actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
            #     self.assertEqual([], actual)

            # config取得に失敗
            # 二重にパッチを当てても想定どおりの挙動をしてくれる
            # withの間だけconfigを返す関数を無効化する
            with patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig", lambda: None):
                url = urls[0]
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                self.assertEqual([], actual)

            # htmlからの動画情報収集に失敗
            mocksoup = self.__MakeAnalysisSoupMock(mocksoup, url, "ValueError")
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url)
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
            self.assertEqual([], actual)

            # apiからの動画情報収集に失敗
            mocksoup = self.__MakeAnalysisSoupMock(mocksoup, url)
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url, "HTTPError")
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
            self.assertEqual([], actual)

            # 取得したtitleの情報がhtmlとapiで異なる
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url, "TitleError")
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
            self.assertEqual([], actual)

            # 取得したvideo_urlの情報がhtmlとapiで異なる
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url, "VideoUrlError")
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
            self.assertEqual([], actual)

            # username_listの大きさが不正
            mockhapi = self.__MakeGetUsernameFromApiMock(mockhapi, url, "UsernameError")
            url = urls[0]
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
            self.assertEqual([], actual)

            # TODO::結合時のエラーを模倣する

    def test_GetSoupInstance(self):
        """GetSoupInstance のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.logger.error"))
            mockslp = stack.enter_context(patch("asyncio.sleep"))
            mockgel = stack.enter_context(patch("asyncio.get_event_loop"))

            MAX_RETRY_NUM = 5
            url = self.__GetURLSet()[0]
            suffix = "?rss=2.0"

            # 正常系
            # リトライなし、取得成功
            mockgel.return_value = self.__MakeEventLoopMock()
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetSoupInstance(url, suffix))
            expect = self.__GetXMLFromRSS(url)
            self.assertEqual(expect, actual[1].text)

            # リトライあり、取得成功
            mockgel.return_value = self.__MakeEventLoopMock(MAX_RETRY_NUM - 1, False)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetSoupInstance(url, suffix))
            expect = self.__GetXMLFromRSS(url)
            self.assertEqual(expect, actual[1].text)

            # 異常系
            # リトライは成功したが取得失敗
            mockgel.return_value = self.__MakeEventLoopMock(MAX_RETRY_NUM - 1, True)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetSoupInstance(url, suffix))
            expect = (None, None)
            self.assertEqual(expect, actual)

            # MAX_RETRY_NUM 回リトライしたが取得失敗
            mockgel.return_value = self.__MakeEventLoopMock(MAX_RETRY_NUM, False)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetSoupInstance(url, suffix))
            expect = (None, None)
            self.assertEqual(expect, actual)

            # 入力URLが不正
            url = "https://不正なURL/user/11111111/video"
            mockgel.return_value = self.__MakeEventLoopMock()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetSoupInstance(url, suffix))
            expect = (None, None)
            self.assertEqual(expect, actual)

            # suffixが不正
            url = self.__GetURLSet()[0]
            suffix = "?rss=atom"
            mockgel.return_value = self.__MakeEventLoopMock()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetSoupInstance(url, suffix))
            expect = (None, None)
            self.assertEqual(expect, actual)

    def test_GetItemInfo(self):
        """GetItemInfo のテスト
        """
        with ExitStack() as stack:
            # 正常系
            url = self.__GetURLSet()[0]

            def MakeItemLx(url, error_target=""):
                xml = self.__GetXMLFromRSS(url)
                if error_target != "":
                    xml = xml.replace(error_target, "invalid")
                soup = BeautifulSoup(xml, "lxml-xml")
                items_lx = soup.find_all("item")
                return items_lx[0]

            item_lx = MakeItemLx(url)

            def GetItemInfo(item):
                src_df = "%a, %d %b %Y %H:%M:%S %z"
                dst_df = "%Y-%m-%d %H:%M:%S"

                title = item.find("title").text

                link_lx = item.find("link")
                pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+"
                if re.findall(pattern, link_lx.text):
                    # クエリ除去してURL部分のみ保持
                    video_url = urllib.parse.urlunparse(
                        urllib.parse.urlparse(link_lx.text)._replace(query=None)
                    )

                pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
                video_id = re.findall(pattern, video_url)[0]

                pubDate_lx = item.find("pubDate")
                uploaded = datetime.strptime(pubDate_lx.text, src_df).strftime(dst_df)

                return (video_id, title, uploaded, video_url)

            expect = GetItemInfo(item_lx)
            actual = GetMyListInfoFromRss.GetItemInfo(item_lx)
            self.assertEqual(expect, actual)

            # 異常系
            # title取得失敗
            item_lx = MakeItemLx(url, "title")
            with self.assertRaises(AttributeError):
                actual = GetMyListInfoFromRss.GetItemInfo(item_lx)

            # link取得失敗
            item_lx = MakeItemLx(url, "link")
            with self.assertRaises(AttributeError):
                actual = GetMyListInfoFromRss.GetItemInfo(item_lx)

            # pubDate取得失敗
            item_lx = MakeItemLx(url, "pubDate")
            with self.assertRaises(AttributeError):
                actual = GetMyListInfoFromRss.GetItemInfo(item_lx)

    def test_AnalysisSoup(self):
        """AnalysisSoup のテスト
        """
        with ExitStack() as stack:
            mockaup = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.AnalysisUploadedPage"))
            mockamp = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.AnalysisMylistPage"))

            mockaup.return_value = "AnalysisUploadedPage result"
            mockamp.return_value = "AnalysisMylistPage result"

            # 正常系
            # 投稿動画ページ
            url = self.__GetURLSet()[0]
            xml = self.__GetXMLFromRSS(url)
            soup = BeautifulSoup(xml, "lxml-xml")

            url_type = "uploaded"
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisSoup(url_type, url, soup))
            expect = "AnalysisUploadedPage result"
            self.assertEqual(expect, actual)
            mockaup.assert_called_once_with(url, soup)
            mockaup.reset_mock()
            mockamp.assert_not_called()
            mockamp.reset_mock()

            # マイリストページ
            url = self.__GetURLSet()[3]
            xml = self.__GetXMLFromRSS(url)
            soup = BeautifulSoup(xml, "lxml-xml")
            url_type = "mylist"
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisSoup(url_type, url, soup))
            expect = "AnalysisMylistPage result"
            self.assertEqual(expect, actual)
            mockaup.assert_not_called()
            mockaup.reset_mock()
            mockamp.assert_called_once_with(url, soup)
            mockamp.reset_mock()

            # 異常系
            # 不正なurlタイプ
            with self.assertRaises(ValueError):
                url_type = "invalid url type"
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisSoup(url_type, "", None))

    def test_AnalysisUploadedPage(self):
        """AnalysisUploadedPage のテスト
        """
        with ExitStack() as stack:
            # 正常系
            mylist_url = self.__GetMylistURLSet()[0]
            mylist_title, _, mylist_username = self.__GetMylistInfoSet(mylist_url)
            video_info = self.__GetVideoInfoSet(mylist_url)
            video_info.reverse()
            pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/video"
            userid = re.findall(pattern, mylist_url)[0]
            myshowname = "投稿動画"
            showname = f"{mylist_username}さんの投稿動画"

            video_id_list = [v["video_id"] for v in video_info]
            title_list = [v["title"] for v in video_info]
            registered_at_list = [v["registered_at"] for v in video_info]
            video_url_list = [v["video_url"] for v in video_info]

            expect = {
                "userid": userid,
                "mylistid": "",
                "showname": showname,
                "myshowname": myshowname,
                "video_id_list": video_id_list,
                "title_list": title_list,
                "registered_at_list": registered_at_list,
                "video_url_list": video_url_list,
            }

            def MakeSoup(url, error_target=""):
                xml = self.__GetXMLFromRSS(url)
                if error_target != "":
                    xml = xml.replace(error_target, "invalid")
                return BeautifulSoup(xml, "lxml-xml")

            soup = MakeSoup(mylist_url)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisUploadedPage(mylist_url, soup))
            self.assertEqual(expect, actual)

            # 異常系
            # 動画名収集失敗
            with self.assertRaises(IndexError):
                soup = MakeSoup(mylist_url, "title")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisUploadedPage(mylist_url, soup))

            # 登録日時収集失敗
            with self.assertRaises(AttributeError):
                soup = MakeSoup(mylist_url, "pubDate")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisUploadedPage(mylist_url, soup))

            # TODO::登録日時収集は成功するが解釈に失敗

            # 動画URL収集失敗
            with self.assertRaises(AttributeError):
                soup = MakeSoup(mylist_url, "link")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisUploadedPage(mylist_url, soup))

    def test_AnalysisMylistPage(self):
        """AnalysisMylistPage のテスト
        """
        with ExitStack() as stack:
            # 正常系
            url = self.__GetURLSet()[3]
            mylist_url = url

            # マイリストのURLならRSSが取得できるURLに加工
            pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
            if re.search(pattern, mylist_url):
                mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除
            mylist_title, _, mylist_username = self.__GetMylistInfoSet(mylist_url)
            video_info = self.__GetVideoInfoSet(mylist_url)
            video_info.reverse()
            pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)"
            userid, mylistid = re.findall(pattern, url)[0]
            pattern = "^マイリスト (.*)‐ニコニコ動画$"
            myshowname = re.findall(pattern, mylist_title)[0]
            showname = f"「{myshowname}」-{mylist_username}さんのマイリスト"

            video_id_list = [v["video_id"] for v in video_info]
            title_list = [v["title"] for v in video_info]
            registered_at_list = [v["registered_at"] for v in video_info]
            video_url_list = [v["video_url"] for v in video_info]

            expect = {
                "userid": userid,
                "mylistid": mylistid,
                "showname": showname,
                "myshowname": myshowname,
                "video_id_list": video_id_list,
                "title_list": title_list,
                "registered_at_list": registered_at_list,
                "video_url_list": video_url_list,
            }

            def MakeSoup(url, error_target=""):
                xml = self.__GetXMLFromRSS(url)
                if error_target != "":
                    xml = xml.replace(error_target, "invalid")
                return BeautifulSoup(xml, "lxml-xml")

            soup = MakeSoup(mylist_url)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisMylistPage(url, soup))
            self.assertEqual(expect, actual)

            # 異常系
            # 動画名収集失敗
            with self.assertRaises(IndexError):
                soup = MakeSoup(mylist_url, "title")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisMylistPage(url, soup))

            # 登録日時収集失敗
            with self.assertRaises(AttributeError):
                soup = MakeSoup(mylist_url, "pubDate")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisMylistPage(url, soup))

            # TODO::登録日時収集は成功するが解釈に失敗

            # 動画URL収集失敗
            with self.assertRaises(AttributeError):
                soup = MakeSoup(mylist_url, "link")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisMylistPage(url, soup))

    def test_GetUsernameFromApi(self):
        """GetUsernameFromApi のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.logger.error"))
            mockslp = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.asyncio.sleep"))
            mocksg = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.AsyncHTMLSession"))

            # 正常系
            mocksg = self.__MakeAPISessionResponseMock(mocksg, 200)

            expect = {}
            mylist_url = self.__GetURLSet()[3]
            video_info_list = self.__GetVideoInfoSet(mylist_url)
            video_id_list = [video_info["video_id"] for video_info in video_info_list]
            title_list = [video_info["title"] for video_info in video_info_list]
            uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
            video_url_list = [video_info["video_url"] for video_info in video_info_list]
            username_list = [video_info["username"] for video_info in video_info_list]

            expect = {
                "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
                "title_list": title_list,               # 動画タイトルリスト [テスト動画]
                "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                "username_list": username_list,         # 投稿者リスト [投稿者1]
            }

            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetUsernameFromApi(video_id_list))
            self.assertEqual(expect, actual)

            # 異常系
            # session.get に失敗
            mocksg = self.__MakeAPISessionResponseMock(mocksg, 503)

            loop = asyncio.new_event_loop()
            with self.assertRaises(ValueError):
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetUsernameFromApi(video_id_list))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
