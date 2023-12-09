"""VideoInfoRssFetcher のテスト

VideoInfoRssFetcher の各種機能をテストする
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
from pathlib import Path

from bs4 import BeautifulSoup
from mock import AsyncMock, MagicMock, patch

from NNMM import GuiFunction
from NNMM.VideoInfoFetcher.rss_parser import RSSParser
from NNMM.VideoInfoFetcher.ValueObjects.fetched_api_video_info import FetchedAPIVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.fetched_page_video_info import FetchedPageVideoInfo
from NNMM.VideoInfoFetcher.ValueObjects.mylist_url import MylistURL
from NNMM.VideoInfoFetcher.ValueObjects.myshowname import Myshowname
from NNMM.VideoInfoFetcher.ValueObjects.registered_at_list import RegisteredAtList
from NNMM.VideoInfoFetcher.ValueObjects.showname import Showname
from NNMM.VideoInfoFetcher.ValueObjects.title_list import TitleList
from NNMM.VideoInfoFetcher.ValueObjects.uploaded_at_list import UploadedAtList
from NNMM.VideoInfoFetcher.ValueObjects.uploaded_url import UploadedURL
from NNMM.VideoInfoFetcher.ValueObjects.username import Username
from NNMM.VideoInfoFetcher.ValueObjects.username_list import UsernameList
from NNMM.VideoInfoFetcher.ValueObjects.video_url_list import VideoURLList
from NNMM.VideoInfoFetcher.ValueObjects.videoid_list import VideoidList
from NNMM.VideoInfoFetcher.video_info_fetcher_base import SourceType
from NNMM.VideoInfoFetcher.video_info_rss_fetcher import VideoInfoRssFetcher

RSS_PATH = "./test/rss/"


class TestVideoInfoRssFetcher(unittest.TestCase):

    def setUp(self):
        # requestsのResourceWarning抑制
        warnings.simplefilter("ignore", ResourceWarning)
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

    def _get_xml_from_rss(self, mylist_url: str) -> str:
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
        title, uploaded, username = self._get_mylist_info_set(mylist_url)
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
        video_info = self._get_video_info_set(mylist_url)
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

    def _make_event_loop_mock(self, retry_count=0, html_error=False) -> AsyncMock:
        """asyncio.get_event_loop にパッチするモックを作成する

        Notes:
            asyncのrun_in_executor の呼び出しを模倣する

        Returns:
            AsyncMock: run_in_executor が呼び出せるモック
        """
        r_response = AsyncMock()
        global count
        count = retry_count

        async def ReturnrunInExecutor(s, executor, func, args):
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
                    raise ValueError

                if html_error:
                    raise ValueError
            else:
                count = count - 1
                raise ValueError
            return r
        type(r_response).run_in_executor = ReturnrunInExecutor
        return r_response

    def _make_config_mock(self) -> dict:
        """Configから取得できるRSS書き出し先のパスを返すモックを作成する

        Returns:
            dict: Configアクセスを模倣する辞書
        """
        return {"general": {"rss_save_path": RSS_PATH}}

    def _make_response_mock(self, request_url, status_code: int = 200, error_target: str = ""):
        mock = MagicMock()
        mock.text = self._get_xml_from_rss(request_url)
        return mock

    def _make_session_response_mock(self, mock, status_code: int = 200, error_target: str = ""):
        async def return_session_response(request_url: str) -> MagicMock:
            if error_target == "ValueError":
                raise ValueError
            if status_code == 503:
                return None

            r_response = self._make_response_mock(request_url, status_code, error_target)
            return r_response
        mock.side_effect = return_session_response
        return mock

    def _make_analysis_rss_mock(self, mock, url: str = "", kind: str = ""):
        mylist_info = self._get_mylist_info_set(url)
        video_info_list = self._get_video_info_set(url)
        video_id_list = [video_info["video_id"] for video_info in video_info_list]
        title_list = [video_info["title"] for video_info in video_info_list]
        registered_at_list = [video_info["registered_at"] for video_info in video_info_list]
        video_url_list = [video_info["video_url"] for video_info in video_info_list]

        if UploadedURL.is_valid(url):
            mylist_url = UploadedURL.create(url)
            userid = mylist_url.userid
            mylistid = mylist_url.mylistid
            username = Username(mylist_info[2])
            myshowname = Myshowname("投稿動画")
            showname = Showname.create(username, None)
        elif MylistURL.is_valid(url):
            mylist_url = MylistURL.create(url)
            userid = mylist_url.userid
            mylistid = mylist_url.mylistid
            username = Username(mylist_info[2])
            myshowname = Myshowname(mylist_info[0].replace("‐ニコニコ動画", ""))
            showname = Showname.create(username, myshowname)

        video_id_list = VideoidList.create(video_id_list)
        title_list = TitleList.create(title_list)
        registered_at_list = RegisteredAtList.create(registered_at_list)
        video_url_list = VideoURLList.create(video_url_list)

        num = len(title_list)
        rss_result = {
            "no": range(1, num + 1),                    # No. [1, ..., len()-1]
            "userid": userid,                           # ユーザーID 1234567
            "mylistid": mylistid,                       # マイリストID 12345678
            "showname": showname,                       # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
            "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
            "mylist_url": mylist_url,                   # マイリストURL https://www.nicovideo.jp/user/1234567/mylist/12345678
            "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        }

        def return_rss(soup: BeautifulSoup):
            if kind == "ValueError":
                raise ValueError
            return FetchedPageVideoInfo(**rss_result)

        mock.side_effect = return_rss
        return mock

    def _make_get_videoinfo_from_api_mock(self, mock, url: str = "", kind: str = ""):
        mylist_url = url

        video_info_list = self._get_video_info_set(mylist_url)
        title_list = [video_info["title"] for video_info in video_info_list]
        uploaded_at_list = [video_info["uploaded_at"] for video_info in video_info_list]
        video_id_list = [video_info["video_id"] for video_info in video_info_list]
        video_url_list = [video_info["video_url"] for video_info in video_info_list]
        username_list = [video_info["username"] for video_info in video_info_list]

        title_list = TitleList.create(title_list)
        uploaded_at_list = UploadedAtList.create(uploaded_at_list)
        video_id_list = VideoidList.create(video_id_list)
        video_url_list = VideoURLList.create(video_url_list)
        username_list = UsernameList.create(username_list)

        num = len(video_id_list)
        api_result = {
            "no": list(range(1, num + 1)),          # No. [1, ..., len()-1]
            "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
            "title_list": title_list,               # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
            "username_list": username_list,         # 投稿者リスト [投稿者1]
        }

        if kind == "TitleError":
            api_result["title_list"] = TitleList([t.name + "_不正なタイトル名" for t in title_list])
        if kind == "VideoUrlError":
            api_result["video_url_list"] = VideoURLList([v.non_query_url + "_不正なタイトル名" for v in video_url_list])
        if kind == "UsernameError":
            api_result["username_list"] = UsernameList([])

        def return_api(v):
            if kind == "ValueError":
                raise ValueError
            return FetchedAPIVideoInfo(**api_result)

        mock.side_effect = return_api
        return mock

    def _make_expect_result(self, url):
        url_type = GuiFunction.get_mylist_type(url)
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
        """VideoInfoRssFetcher の初期化後の状態をテストする
        """
        source_type = SourceType.RSS
        urls = self._get_url_set()
        for url in urls:
            virf = VideoInfoRssFetcher(url)

            if UploadedURL.is_valid(url):
                expect_mylist_url = UploadedURL.create(url)
            elif MylistURL.is_valid(url):
                expect_mylist_url = MylistURL.create(url)

            self.assertEqual(expect_mylist_url, virf.mylist_url)
            self.assertEqual(source_type, virf.source_type)

    def test_analysis_rss(self):
        with ExitStack() as stack:
            # mockps = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoRssFetcher.RSSParser"))

            url = self._get_url_set()[0]
            xml = self._get_xml_from_rss(url).strip()
            parser: RSSParser = RSSParser(url, xml)

            virf = VideoInfoRssFetcher(url)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(virf._analysis_rss(xml))
            expect = loop.run_until_complete(parser.parse())
            self.assertEqual(expect, actual)

            with self.assertRaises(ValueError):
                virf = VideoInfoRssFetcher(url)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                actual = loop.run_until_complete(virf._analysis_rss("invalid_xml"))

    def test_fetch_videoinfo_from_rss(self):
        """_fetch_videoinfo_from_rss のテスト
        """
        with ExitStack() as stack:
            mockcpb = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.get_config", self._make_config_mock))
            mockses = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoRssFetcher.VideoInfoRssFetcher._get_session_response"))
            mocksoup = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoRssFetcher.VideoInfoRssFetcher._analysis_rss"))
            mockhapi = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoRssFetcher.VideoInfoRssFetcher._get_videoinfo_from_api"))

            # 正常系
            mockses = self._make_session_response_mock(mockses, 200)
            urls = self._get_url_set()
            for url in urls:
                mocksoup = self._make_analysis_rss_mock(mocksoup, url)
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url)

                virf = VideoInfoRssFetcher(url)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())
                expect = self._make_expect_result(url)
                self.assertEqual(expect, actual)

            # 異常系
            # session.getが常に失敗
            with self.assertRaises(ValueError):
                mockses = self._make_session_response_mock(mockses, 503)
                url = urls[0]
                virf = VideoInfoRssFetcher(url)
                actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())

            # session.getが例外送出
            with self.assertRaises(ValueError):
                mockses = self._make_session_response_mock(mockses, 503, "ValueError")
                url = urls[0]
                virf = VideoInfoRssFetcher(url)
                actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())

            # config取得に失敗
            # 二重にパッチを当てても想定どおりの挙動をしてくれる
            # withの間だけconfigを返す関数を無効化する
            with patch("NNMM.ConfigMain.ProcessConfigBase.get_config", lambda: None):
                with self.assertRaises(ValueError):
                    mockses = self._make_session_response_mock(mockses, 200)
                    url = urls[0]
                    virf = VideoInfoRssFetcher(url)
                    actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())

            # rssからの動画情報収集に失敗
            with self.assertRaises(ValueError):
                mocksoup = self._make_analysis_rss_mock(mocksoup, url, "ValueError")
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url)
                url = urls[0]
                virf = VideoInfoRssFetcher(url)
                actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())

            # apiからの動画情報収集に失敗
            with self.assertRaises(ValueError):
                mocksoup = self._make_analysis_rss_mock(mocksoup, url)
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url, "ValueError")
                url = urls[0]
                virf = VideoInfoRssFetcher(url)
                actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())

            # 取得したtitleの情報がrssとapiで異なる
            with self.assertRaises(ValueError):
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url, "TitleError")
                url = urls[0]
                virf = VideoInfoRssFetcher(url)
                actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())

            # 取得したvideo_urlの情報がrssとapiで異なる
            with self.assertRaises(ValueError):
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url, "VideoUrlError")
                url = urls[0]
                virf = VideoInfoRssFetcher(url)
                actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())

            # username_listの大きさが不正
            with self.assertRaises(ValueError):
                mockhapi = self._make_get_videoinfo_from_api_mock(mockhapi, url, "UsernameError")
                url = urls[0]
                virf = VideoInfoRssFetcher(url)
                actual = loop.run_until_complete(virf._fetch_videoinfo_from_rss())

            # TODO::結合時のエラーを模倣する

    def test_fetch_videoinfo(self):
        """_fetch_videoinfo のテスト
        """
        with ExitStack() as stack:
            mockfvft = stack.enter_context(patch("NNMM.VideoInfoFetcher.VideoInfoRssFetcher.VideoInfoRssFetcher._fetch_videoinfo_from_rss"))

            expect = "VideoInfoRssFetcher._fetch_videoinfo() called"
            mockfvft.side_effect = lambda: str(expect)

            url = self._get_url_set()[0]
            virf = VideoInfoRssFetcher(url)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(virf._fetch_videoinfo())
            self.assertEqual(expect, actual)
            mockfvft.assert_called_once()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
