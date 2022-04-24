# coding: utf-8
"""GetMyListInfoFromRssのテスト

GetMyListInfoFromRssの各種機能をテストする
"""

import asyncio
import shutil
import sys
import unittest
import urllib.parse
import warnings
from contextlib import ExitStack
from mock import MagicMock, patch, AsyncMock
from pathlib import Path
from re import findall
from urllib.error import HTTPError

from bs4 import BeautifulSoup

from NNMM.MylistDBController import *
from NNMM import GetMyListInfoFromRss

RSS_PATH = "./test/rss/"


class TestGetMyListInfoFromRss(unittest.TestCase):

    def setUp(self):
        # requestsのResourceWarning抑制
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
        title_t = "動画タイトル{}_{:02}"
        video_url_t = "https://www.nicovideo.jp/watch/sm{}00000{:02}"
        uploaded_t = "Wed, 19 Oct 2021 0{}:{:02}:00 +0900"
        video_info = {
            mylist_url_info[0]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(1, 10)],
            mylist_url_info[1]: [(title_t.format(2, i), video_url_t.format(2, i), uploaded_t.format(2, i)) for i in range(1, 10)],
            mylist_url_info[2]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(1, 5)],
            mylist_url_info[3]: [(title_t.format(1, i), video_url_t.format(1, i), uploaded_t.format(1, i)) for i in range(5, 10)],
            mylist_url_info[4]: [(title_t.format(3, i), video_url_t.format(3, i), uploaded_t.format(3, i)) for i in range(1, 10)],
        }
        res = video_info.get(mylist_url, [("", "", "")])
        return res

    def __GetURLType(self, url: str) -> str:
        """URLタイプを返す

        Args:
            url (str): 対象URL

        Returns:
            str: マッチ時 URLタイプ{"uploaded", "mylist"}
                 マッチしなかった場合 空文字列
        """
        # 投稿動画
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
        if re.search(pattern, url):
            return "uploaded"

        # マイリスト
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, url):
            return "mylist"

        return ""

    def __MakeXML(self, mylist_url: str) -> str:
        """RSS取得時に返されるxmlを作成する

        Args:
            mylist_url (str): 対象マイリストURL

        Returns:
            str: 成功時 生成したxml, 失敗時 空文字列
        """
        xml = ""

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
        video_info = self.__GetVideoInfoSet(mylist_url)
        for item in reversed(video_info):
            title, video_url, uploaded = item
            xml = xml + f"""
                <item>
                    <title>{title}</title>
                    <link>{video_url}?ref=rss_mylist_rss2</link>
                    <pubDate>{uploaded}</pubDate>
                    <description><![CDATA[<p></p>]]></description>
                </item>
            """

        xml = xml + "</channel></rss>"
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
                    r.text = self.__MakeXML(request_url)
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

    def __MakeAsyncHTMLSession(self) -> AsyncMock:
        """AsyncHTMLSession にパッチするモックを作成する
        """
        r_response = AsyncMock()

        async def ReturnGet(s, url):
            r = MagicMock()

            def ReturnText(val):
                r_text = MagicMock()
                r_text.text = val
                return r_text

            base_url = "https://ext.nicovideo.jp/api/getthumbinfo/"
            pattern = f"^{base_url}(sm[0-9]+)$"
            video_id = re.findall(pattern, url)[0]

            def ReturnFindall(name):
                urls = self.__GetMylistURLSet()
                for mylist_url in urls:
                    mylist_info = self.__GetMylistInfoSet(mylist_url)
                    video_info_list = self.__GetVideoInfoSet(mylist_url)
                    for video_info in video_info_list:
                        if video_id in video_info[1]:
                            return [ReturnText(mylist_info[2])]
                return []

            r.html.lxml.findall = ReturnFindall
            return r
        type(r_response).get = ReturnGet
        return r_response

    def __MakeAsyncHTMLSessionAPI(self) -> AsyncMock:
        """AsyncHTMLSession にパッチするモックを作成する（動画情報API用）
        """
        r_response = AsyncMock()

        async def ReturnGet(s, url):
            r = MagicMock()

            def ReturnText(val):
                r_text = MagicMock()
                r_text.text = val
                return r_text

            base_url = "https://ext.nicovideo.jp/api/getthumbinfo/"
            pattern = f"^{base_url}(sm[0-9]+)$"
            video_id = re.findall(pattern, url)[0]

            def ReturnFindall(name):
                urls = self.__GetMylistURLSet()
                if name == "thumb/user_nickname":
                    for mylist_url in urls:
                        mylist_info = self.__GetMylistInfoSet(mylist_url)
                        video_info_list = self.__GetVideoInfoSet(mylist_url)
                        for video_info in video_info_list:
                            if video_id in video_info[1]:
                                return [ReturnText(mylist_info[2])]
                return []

            r.html.lxml.findall = ReturnFindall
            return r
        type(r_response).get = ReturnGet
        return r_response

    def __MakeConfigMock(self) -> dict:
        """Configから取得できるRSS書き出し先のパスを返すモックを作成する

        Returns:
            dict: Configアクセスを模倣する辞書
        """
        return {"general": {"rss_save_path": RSS_PATH}}

    def __MakeExpectResult(self, url: str) -> list[dict]:
        """RSSまたはHTMLページスクレイピングで取得される動画情報の予測値を生成する

        Notes:
            table_colsをキーとする辞書リストを返す

        Args:
            url (str): リスクエト先URL

        Returns:
            list[dict]: table_colsをキーとする動画情報辞書のリスト
        """
        expect = []
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]

        # クエリ除去
        url = urllib.parse.urlunparse(
            urllib.parse.urlparse(url)._replace(query=None)
        )

        # url_type判定
        type = self.__GetURLType(url)

        mylist_url = url
        # マイリストのURLならRSSが取得できるURLに加工
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        # マイリスト情報と動画情報を取得
        mylist_info = self.__GetMylistInfoSet(mylist_url)
        video_info = self.__GetVideoInfoSet(mylist_url)

        username = mylist_info[2]

        for i, item in enumerate(reversed(video_info)):
            # マイリスト名収集
            showname = ""
            myshowname = ""
            if type == "uploaded":
                # 投稿動画の場合はマイリスト名がないのでユーザー名と合わせて便宜上の名前に設定
                myshowname = "投稿動画"
                showname = f"{username}さんの投稿動画"
            elif type == "mylist":
                # マイリストの場合はタイトルから取得
                pattern = "^マイリスト (.*)‐ニコニコ動画$"
                myshowname = re.findall(pattern, mylist_info[0])[0]
                showname = f"「{myshowname}」-{username}さんのマイリスト"

            title = item[0]

            video_url = item[1]
            pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+"
            if re.findall(pattern, video_url):
                # クエリ除去してURL部分のみ保持
                video_url = urllib.parse.urlunparse(
                    urllib.parse.urlparse(video_url)._replace(query=None)
                )

            pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
            video_id = re.findall(pattern, item[1])[0]

            td_format = "%a, %d %b %Y %H:%M:%S %z"
            dts_format = "%Y-%m-%d %H:%M:%S"
            uploaded = datetime.strptime(item[2], td_format).strftime(dts_format)

            value_list = [i + 1, video_id, title, username, "",
                          uploaded, video_url, url, showname, myshowname]
            expect.append(dict(zip(table_cols, value_list)))
        return expect

    def test_GetMyListInfoFromRss(self):
        """GetMyListInfoFromRss のテスト
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.logger.warning"))
            mockslp = stack.enter_context(patch("asyncio.sleep"))
            mockgel = stack.enter_context(patch("asyncio.get_event_loop"))
            mockcpb = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig", self.__MakeConfigMock))
            mocksg = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.AsyncHTMLSession", self.__MakeAsyncHTMLSession))

            # 正常系
            mockgel.return_value = self.__MakeEventLoopMock()
            urls = self.__GetURLSet()
            for url in urls:
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
            with patch("NNMM.GetMyListInfoFromRss.BeautifulSoup", lambda t, p: None):
                url = urls[0]
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                self.assertEqual([], actual)

            # 投稿者名取得に失敗
            pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
            with patch("re.findall", lambda p, t: findall(p, t) if p != pattern else None):
                url = urls[0]
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                self.assertEqual([], actual)

            # マイリスト名取得に失敗
            pattern = "^マイリスト (.*)‐ニコニコ動画$"
            with patch("re.findall", lambda p, t: findall(p, t) if p != pattern else None):
                url = urls[2]
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                self.assertEqual([], actual)

            # config取得に失敗
            # 二重にパッチを当てても想定どおりの挙動をしてくれる
            # withの間だけconfigを返す関数を無効化する
            with patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig", lambda: None):
                url = urls[0]
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                self.assertEqual([], actual)

            # RSS保存に失敗
            # RSS保存は失敗しても返り値は正常となる
            with patch("pathlib.Path.open", lambda: None):
                url = urls[0]
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                expect = self.__MakeExpectResult(url)
                self.assertEqual(expect, actual)

            # エントリ保存に失敗(TypeError)
            # エントリのvideo_idの切り出しに失敗
            pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
            with patch("re.findall", lambda p, t: findall(p, t) if p != pattern else None):
                url = urls[0]
                actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
                self.assertEqual([], actual)

            # エントリ保存に失敗(ValueError)
            # エントリのuploadedの切り出しに失敗
            # datetime.strptimeはビルトイン関数のためモックを当てるのが面倒
            # BeautifulSoupのfindメソッドを置き換える
            # real_func = bs4.element.Tag.find

            # def mock_func(s, t):
            #     r = real_func(s, t)
            #     type(r).text = r.text + "不正なpubDate"
            #     return r

            # with patch("bs4.element.Tag.find", lambda s, t: real_func(s, t) if t != "pubDate" else mock_func(s, t)):
            #     url = urls[0]
            #     actual = loop.run_until_complete(GetMyListInfoFromRss.GetMyListInfoFromRss(url))
            #     self.assertEqual([], actual)

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
            expect = self.__MakeXML(url)
            self.assertEqual(expect, actual[1].text)

            # リトライあり、取得成功
            mockgel.return_value = self.__MakeEventLoopMock(MAX_RETRY_NUM - 1, False)
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetSoupInstance(url, suffix))
            expect = self.__MakeXML(url)
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

    def test_GetSoupInstance(self):
        """GetSoupInstance のテスト
        """
        with ExitStack() as stack:
            # 正常系
            url = self.__GetURLSet()[0]

            def MakeItemLx(url, error_target=""):
                xml = self.__MakeXML(url)
                if error_target != "":
                    xml = xml.replace(error_target, "invalid")
                soup = BeautifulSoup(xml, "lxml-xml")
                items_lx = soup.find_all("item")
                return items_lx[0]

            item_lx = MakeItemLx(url)

            def GetItemInfo(item):
                td_format = "%a, %d %b %Y %H:%M:%S %z"
                dts_format = "%Y-%m-%d %H:%M:%S"

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
                uploaded = datetime.strptime(pubDate_lx.text, td_format).strftime(dts_format)

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
            xml = self.__MakeXML(url)
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
            xml = self.__MakeXML(url)
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
            title, uploaded, username = self.__GetMylistInfoSet(mylist_url)
            video_info = self.__GetVideoInfoSet(mylist_url)
            video_info.reverse()
            pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/video"
            userid = re.findall(pattern, mylist_url)[0]
            myshowname = "投稿動画"
            showname = f"{username}さんの投稿動画"
            
            title_list = [v[0] for v in video_info]
            video_url_list = [v[1] for v in video_info]
            pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
            video_id_list = [re.findall(pattern, v)[0] for v in video_url_list]

            td_format = "%a, %d %b %Y %H:%M:%S %z"
            dts_format = "%Y-%m-%d %H:%M:%S"
            uploaded_list = [datetime.strptime(v[2], td_format).strftime(dts_format) for v in video_info]

            num = len(video_id_list)
            username_list = [username for _ in range(num)]

            expect = {
                "userid": userid,
                "mylistid": "",
                "showname": showname,
                "myshowname": myshowname,
                "video_id_list": video_id_list,
                "title_list": title_list,
                "uploaded_list": uploaded_list,
                "video_url_list": video_url_list,
                "username_list": username_list,
            }

            def MakeSoup(url, error_target=""):
                xml = self.__MakeXML(url)
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

            # 投稿日時収集失敗
            with self.assertRaises(AttributeError):
                soup = MakeSoup(mylist_url, "pubDate")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisUploadedPage(mylist_url, soup))

            # TODO::投稿日時収集は成功するが解釈に失敗

            # 動画URL収集失敗
            with self.assertRaises(AttributeError):
                soup = MakeSoup(mylist_url, "link")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisUploadedPage(mylist_url, soup))

    def test_AnalysisMylistPage(self):
        """AnalysisMylistPage のテスト
        """
        with ExitStack() as stack:
            mockguf = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.GetUsernameFromApi"))

            # 正常系
            url = self.__GetURLSet()[3]
            mylist_url = url
            # マイリストのURLならRSSが取得できるURLに加工
            pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
            if re.search(pattern, mylist_url):
                mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除
            title, uploaded, username = self.__GetMylistInfoSet(mylist_url)
            video_info = self.__GetVideoInfoSet(mylist_url)
            video_info.reverse()
            pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)"
            userid, mylistid = re.findall(pattern, url)[0]
            pattern = "^マイリスト (.*)‐ニコニコ動画$"
            myshowname = re.findall(pattern, title)[0]
            showname = f"「{myshowname}」-{username}さんのマイリスト"

            title_list = [v[0] for v in video_info]
            video_url_list = [v[1] for v in video_info]
            pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
            video_id_list = [re.findall(pattern, v)[0] for v in video_url_list]

            td_format = "%a, %d %b %Y %H:%M:%S %z"
            dts_format = "%Y-%m-%d %H:%M:%S"
            uploaded_list = [datetime.strptime(v[2], td_format).strftime(dts_format) for v in video_info]

            # 投稿者名は実際には動画情報APIに問い合わせているがここでは検証しない
            num = len(video_id_list)
            username_list = [username for _ in range(num)]
            mockguf.return_value = username_list

            expect = {
                "userid": userid,
                "mylistid": mylistid,
                "showname": showname,
                "myshowname": myshowname,
                "video_id_list": video_id_list,
                "title_list": title_list,
                "uploaded_list": uploaded_list,
                "video_url_list": video_url_list,
                "username_list": username_list,
            }

            def MakeSoup(url, error_target=""):
                xml = self.__MakeXML(url)
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

            # 投稿日時収集失敗
            with self.assertRaises(AttributeError):
                soup = MakeSoup(mylist_url, "pubDate")
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(GetMyListInfoFromRss.AnalysisMylistPage(url, soup))

            # TODO::投稿日時収集は成功するが解釈に失敗

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
            mockslp = stack.enter_context(patch("asyncio.sleep"))
            mockgel = stack.enter_context(patch("asyncio.get_event_loop"))
            mocksg = stack.enter_context(patch("NNMM.GetMyListInfoFromRss.AsyncHTMLSession", self.__MakeAsyncHTMLSessionAPI))

            # 正常系
            default_name = "<NULL>"
            url = self.__GetURLSet()[3]
            mylist_url = url
            # マイリストのURLならRSSが取得できるURLに加工
            pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
            if re.search(pattern, mylist_url):
                mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除
            title, uploaded, username = self.__GetMylistInfoSet(mylist_url)
            video_info = self.__GetVideoInfoSet(mylist_url)
            video_info.reverse()

            video_url_list = [v[1] for v in video_info]
            pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
            video_id_list = [re.findall(pattern, v)[0] for v in video_url_list]

            num = len(video_id_list)
            expect = [username for _ in range(num)]

            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetUsernameFromApi(video_id_list))
            self.assertEqual(expect, actual)

            # 異常系
            video_id_list = ["sm99999999", "sm99999998", "sm99999997"]
            num = len(video_id_list)
            expect = [default_name for _ in range(num)]
            loop = asyncio.new_event_loop()
            actual = loop.run_until_complete(GetMyListInfoFromRss.GetUsernameFromApi(video_id_list))
            self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
