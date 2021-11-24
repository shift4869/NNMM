# coding: utf-8
"""ProcessCreateMylist のテスト
"""

import asyncio
import re
import random
import sys
import unittest
import urllib.parse
from contextlib import ExitStack
from datetime import datetime
from logging import INFO, getLogger
from mock import MagicMock, patch, AsyncMock

from NNMM.Process import *
from NNMM import GetMyListInfo


class TestProcessCreateMylist(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
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
            mylist_url_info[0]: ("投稿者1さんの投稿動画‐ニコニコ動画", "投稿動画", "投稿者1"),
            mylist_url_info[1]: ("投稿者2さんの投稿動画‐ニコニコ動画", "投稿動画", "投稿者2"),
            mylist_url_info[2]: ("「マイリスト1」-投稿者1さんのマイリスト", "マイリスト1", "投稿者1"),
            mylist_url_info[3]: ("「マイリスト2」-投稿者1さんのマイリスト", "マイリスト2", "投稿者1"),
            mylist_url_info[4]: ("「マイリスト3」-投稿者3さんのマイリスト", "マイリスト3", "投稿者3"),
        }
        res = mylist_info.get(mylist_url, ("", "", ""))
        return res

    def __GetNowDatetime(self) -> str:
        """タイムスタンプを返す

        Returns:
            str: 現在日時 "%Y-%m-%d %H:%M:%S" 形式
        """
        dts_format = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now().strftime(dts_format)
        return dst

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

    def __MakeUsername(self, mylist_url: str) -> list[str]:
        """session.get 後の html.lxml.find_class の返り値を生成する

        Notes:
            html.lxml.find_class が "UserDetailsHeader-nickname" で
            呼び出されたときの返り値を生成する

        Args:
            mylist_url (str): マイリストURL

        Returns:
            list[str]: 投稿者のリスト(要素数は1)
        """
        res = []

        # マイリスト情報取得
        mylist_info = self.__GetMylistInfoSet(mylist_url)

        res = [mylist_info[2]]
        return res

    def __MakeMyshowname(self, mylist_url: str) -> list[str]:
        """session.get 後の html.lxml.find_class の返り値を生成する

        Notes:
            html.lxml.find_class が "MylistHeader-name" で
            呼び出されたときの返り値を生成する

        Args:
            mylist_url (str): マイリストURL

        Returns:
            list[str]: マイリスト名のリスト(要素数は1)
        """
        res = []

        # マイリスト情報取得
        mylist_info = self.__GetMylistInfoSet(mylist_url)

        res = [mylist_info[1]]
        return res

    def __MakeReturnHtml(self, url: str, error_target: str) -> AsyncMock:
        """html以下のプロパティ,メソッドを模倣するモックを返す

        Notes:
            以下のプロパティ,メソッドを模倣するモックを返す
            html
                aync arender()
                lxml
                    find_class()
                        [text]
        Args:
            url (str): 対象URL
            error_target (str): html.lxml.find_class においてエラーとするid

        Returns:
            AsyncMock: html を模倣するモック
        """
        r_html = AsyncMock()

        async def ReturnARender(s):
            return None
        type(r_html).arender = ReturnARender

        # クエリ除去
        mylist_url = urllib.parse.urlunparse(
            urllib.parse.urlparse(url)._replace(query=None)
        )

        # マイリストのURLならRSSが取得できるURLに加工
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, mylist_url):
            mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除

        def ReturnLxml():
            r_lxml = MagicMock()

            def ReturnFindClass(s, id):
                r_finds = []
                value_list = []

                # エラーとする指定があるなら空リストを返す
                if error_target != "":
                    if id in error_target and "ValueError" in error_target:
                        raise ValueError
                    if id == error_target:
                        return []

                # 呼び出し時のパラメータで分岐
                if id == "UserDetailsHeader-nickname":
                    # username
                    value_list = self.__MakeUsername(mylist_url)
                elif id == "MylistHeader-name":
                    # myshowname
                    value_list = self.__MakeMyshowname(mylist_url)

                # textプロパティで取り出せるようにパッキング
                for v in value_list:
                    r_p = MagicMock()
                    type(r_p).text = v
                    r_finds.append(r_p)
                return r_finds

            type(r_lxml).find_class = ReturnFindClass
            return r_lxml

        type(r_html).lxml = ReturnLxml()
        return r_html

    def __MakeSessionMock(self, return_status: int = 200, error_target: str = "") -> AsyncMock:
        """session を模倣するモック

        Notes:
            以下のプロパティ,メソッドを模倣するモックを返す
            session
                aync get()
                    html: __MakeReturnHtml()を参照
                aync close()

        Args:
            return_status (str): 想定リクエストステータス
            error_target (str): html.lxml.find_class においてエラーとするid

        Returns:
            AsyncMock: 以下のモックを返却する
                        return_statusが200のとき,session を模倣するモック
                            error_target が空文字列ならば正常なモック
                            error_target が空文字列でないならばhtml.lxml.find_class に失敗するモック
                        return_statusが200でないとき, session.getに失敗するモック
        """
        r_response = AsyncMock()

        async def ReturnGet(s, url):
            r_get = MagicMock()
            type(r_get).html = self.__MakeReturnHtml(url, error_target)
            return r_get
        type(r_response).get = ReturnGet if return_status == 200 else None

        async def ReturnClose(s):
            return None
        type(r_response).close = ReturnClose

        return r_response

    async def __MakePyppeteerMock(self, argv: dict) -> None:
        """pyppeteer.launch にパッチして、無効化するためのモック
        """
        return None

    def __MakeExpectResult(self, url: str) -> dict:
        """RSSまたはHTMLページスクレイピングで取得される動画情報の予測値を生成する

        Notes:
            table_colsをキーとする辞書リストを返す

        Args:
            url (str): リスクエト先URL

        Returns:
            dict: table_colsをキーとする動画情報辞書のリスト
        """
        expect = {}
        table_cols = ["username", "mylist_url", "showname", "mylistname"]

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

        username = mylist_info[2]

        # マイリスト名収集
        showname = ""
        myshowname = ""
        if type == "uploaded":
            # 投稿動画の場合はマイリスト名がないのでユーザー名と合わせて便宜上の名前に設定
            myshowname = "投稿動画"
            showname = f"{username}さんの投稿動画"
        elif type == "mylist":
            # マイリストの場合はタイトルから取得
            myshowname = mylist_info[1]
            showname = f"「{myshowname}」-{username}さんのマイリスト"

        value_list = [username, url, showname, myshowname]
        expect = dict(zip(table_cols, value_list))
        return expect

    def test_PCMAsyncGetMyListInfo(self):
        """ProcessCreateMylistのAsyncGetMyListInfoをテストする
        """
        with ExitStack() as stack:
            mockslp = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.sleep"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.logger.error"))
            mocklw = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.logger.warning"))
            mockses = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.AsyncHTMLSession", lambda: self.__MakeSessionMock(200)))
            mockpyp = stack.enter_context(patch("pyppeteer.launch", self.__MakePyppeteerMock))

            pcm = ProcessCreateMylist.ProcessCreateMylist()

            # 正常系
            urls = self.__GetURLSet()
            for url in urls:
                loop = asyncio.new_event_loop()
                actual = loop.run_until_complete(pcm.AsyncGetMyListInfo(url))
                expect = self.__MakeExpectResult(url)
                self.assertEqual(expect, actual)

            # 異常系
            # 入力URLが不正
            url = "https://不正なURL/user/11111111/video"
            actual = loop.run_until_complete(pcm.AsyncGetMyListInfo(url))
            self.assertEqual({}, actual)
 
            # session.getが常に失敗
            with patch("NNMM.Process.ProcessCreateMylist.AsyncHTMLSession", lambda: self.__MakeSessionMock(503)):
                url = urls[0]
                actual = loop.run_until_complete(pcm.AsyncGetMyListInfo(url))
                self.assertEqual({}, actual)

            # 動画が不正なマイリストを指定
            with patch("NNMM.GuiFunction.GetURLType", lambda x: "mylist"):
                url = "https://www.nicovideo.jp/user/99999999/mylist/99999999"
                actual = loop.run_until_complete(pcm.AsyncGetMyListInfo(url))
                self.assertEqual({}, actual)

            # 投稿者収集に失敗(AttributeError)
            url = urls[0]
            error_target = "UserDetailsHeader-nickname"
            with patch("NNMM.Process.ProcessCreateMylist.AsyncHTMLSession", lambda: self.__MakeSessionMock(200, error_target)):
                actual = loop.run_until_complete(pcm.AsyncGetMyListInfo(url))
                self.assertEqual({}, actual)

            # マイリスト名収集に失敗(AttributeError)
            url = urls[2]
            error_target = "MylistHeader-name"
            with patch("NNMM.Process.ProcessCreateMylist.AsyncHTMLSession", lambda: self.__MakeSessionMock(200, error_target)):
                actual = loop.run_until_complete(pcm.AsyncGetMyListInfo(url))
                self.assertEqual({}, actual)
        pass

    def test_PCMRun(self):
        """ProcessCreateMylistのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.logger.error"))
            mockcpg = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig"))
            mockgut = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.GetURLType"))
            mockgndt = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.GetNowDatetime"))
            mockpgt = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.sg.popup_get_text"))
            mockpu = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.sg.popup"))
            mockpu = stack.enter_context(patch("NNMM.Process.ProcessCreateMylist.sg.popup"))
            mocknel = stack.enter_context(patch("asyncio.new_event_loop"))

            pcm = ProcessCreateMylist.ProcessCreateMylist()

            # サンプル値選定
            url = random.choice(self.__GetURLSet())
            mylist_url = url
            # マイリストのURLならRSSが取得できるURLに加工
            pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
            if re.search(pattern, mylist_url):
                mylist_url = re.sub("/user/[0-9]+", "", mylist_url)  # /user/{userid} 部分を削除
            m_list = self.__GetMylistInfoSet(mylist_url)
            username = m_list[2]
            showname = m_list[0]
            mylistname = m_list[1]

            mockcpg.side_effect = lambda: {"general": {"auto_reload": "15分毎"}}
            mockgut.side_effect = self.__GetURLType
            mockgndt.side_effect = self.__GetNowDatetime
            mockpgt.side_effect = lambda msg, title: url

            mockrucs = MagicMock()
            mockruc = MagicMock()
            expect_v_record = {
                "video_id": "sm11111111",
                "title": "動画タイトル1",
                "username": username,
                "status": "",
                "uploaded": "Wed, 19 Oct 2021 01:00:00 +0900",
                "video_url": "https://www.nicovideo.jp/watch/sm11111111",
                "mylist_url": url,
                "created_at": "Wed, 19 Oct 2021 02:00:00 +0900",
                "showname": showname,
                "mylistname": mylistname,
            }
            expect_m_record = {
                "username": username,
                "mylist_url": url,
                "showname": showname,
                "mylistname": mylistname,
            }
            mockrucs.side_effect = [
                [expect_v_record],
                [],
                expect_m_record,
            ]
            type(mockruc).run_until_complete = mockrucs
            mocknel.side_effect = lambda: mockruc

            def updatemock(value):
                r = MagicMock()
                type(r).update = lambda s, value: value
                return r

            expect_values_dict = {
                "-INPUT1-": "",
                "-INPUT2-": "",
            }
            expect_window_dict = {
                "-INPUT2-": "",
            }
            for k, v in expect_window_dict.items():
                expect_window_dict[k] = updatemock(v)

            mockwm = MagicMock()
            mockwin = MagicMock()
            type(mockwin).write_event_value = lambda s, k, v: f"{k}_{v}"
            type(mockwin).refresh = lambda s: 0
            mockwin.__getitem__.side_effect = expect_window_dict.__getitem__
            mockwin.__iter__.side_effect = expect_window_dict.__iter__
            mockwin.__contains__.side_effect = expect_window_dict.__contains__
            type(mockwm).window = mockwin
            type(mockwm).values = expect_values_dict

            def Upsert_mock(s, id: int, username: str, mylistname: str, type: str, showname: str, url: str,
                            created_at: str, updated_at: str, checked_at: str, check_interval: str, is_include_new: bool) -> int:
                return 0
            mockmb = MagicMock()
            type(mockmb).SelectFromURL = lambda s, url: []
            type(mockmb).Select = lambda s: [{"id": 0}]
            type(mockmb).Upsert = Upsert_mock
            type(mockwm).mylist_db = mockmb

            mockmib = MagicMock()
            type(mockmib).UpsertFromList = lambda s, records: 0
            type(mockwm).mylist_info_db = mockmib

            actual = pcm.Run(mockwm)
        pass

    def test_PCMTDRun(self):
        """ProcessCreateMylistThreadDoneのRunをテストする
        """
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
