# coding: utf-8
"""GuiFunction のテスト

GuiFunction の各種機能をテストする
Guiの処理部分はモックで動作確認する(実際にGUIは表示されない)
"""

import re
import random
import sys
import unittest
from contextlib import ExitStack
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from mock import MagicMock, patch, AsyncMock
from pathlib import Path

import freezegun
from sqlalchemy import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM import GuiFunction
from NNMM.MylistDBController import *

TEST_DB_PATH = "./test/test.db"


class TestGetMyListInfo(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        Path(TEST_DB_PATH).unlink(missing_ok=True)
        pass

    def __GetMylistInfoSet(self) -> list[tuple]:
        """Mylistオブジェクトの情報セットを返す（mylist_url以外）
        """
        mylist_info = [
            (1, "投稿者1", "投稿動画", "uploaded", "投稿者1さんの投稿動画", "2021-05-29 00:00:11", "2021-10-16 00:00:11", "2021-10-17 00:00:11", "15分", False),
            (2, "投稿者2", "投稿動画", "uploaded", "投稿者2さんの投稿動画", "2021-05-29 00:00:22", "2021-10-16 00:00:22", "2021-10-17 00:00:22", "15分", False),
            (3, "投稿者1", "マイリスト1", "mylist", "「マイリスト1」-投稿者1さんのマイリスト", "2021-05-29 00:11:11", "2021-10-16 00:11:11", "2021-10-17 00:11:11", "15分", False),
            (4, "投稿者1", "マイリスト2", "mylist", "「マイリスト2」-投稿者1さんのマイリスト", "2021-05-29 00:22:11", "2021-10-16 00:22:11", "2021-10-17 00:22:11", "15分", False),
            (5, "投稿者3", "マイリスト3", "mylist", "「マイリスト3」-投稿者3さんのマイリスト", "2021-05-29 00:11:33", "2021-10-16 00:11:33", "2021-10-17 00:11:33", "15分", False),
        ]
        return mylist_info

    def __GetURLInfoSet(self) -> list[str]:
        """mylist_urlの情報セットを返す
        """
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def __MakeMylistSample(self, id: str) -> Mylist:
        """Mylistオブジェクトを作成する

        Note:
            マイリスト情報セット
                id (int): ID
                username (str): 投稿者名
                mylistname (str): マイリスト名
                type (str): マイリストのタイプ({"uploaded", "mylist"})
                showname (str): マイリストの一意名({username}_{type})
                                typeが"uploaded"の場合："{username}さんの投稿動画"
                                typeが"mylist"の場合："「{mylistname}」-{username}さんのマイリスト"
                url (str): マイリストURL
                created_at (str): 作成日時
                updated_at (str): 更新日時
                checked_at (str): 更新確認日時
                check_interval (str): 最低更新間隔
                is_include_new (boolean): 未視聴動画を含むかどうか

        Args:
            id (int): マイリストとURL情報セットのid

        Returns:
            Mylist: Mylistオブジェクト
        """
        ml = self.__GetMylistInfoSet()[id]
        mylist_url = self.__GetURLInfoSet()[id]
        r = Mylist(ml[0], ml[1], ml[2], ml[3], ml[4], mylist_url, ml[5], ml[6], ml[7], ml[8], ml[9])
        return r

    def __LoadToTable(self, records) -> list[dict]:
        """テスト用の初期レコードを格納したテーブルを用意する

        Args:
            records (list[Mylist]): 格納するレコードの配列
        """
        Path(TEST_DB_PATH).unlink(missing_ok=True)

        dbname = TEST_DB_PATH
        engine = create_engine(f"sqlite:///{dbname}", echo=False, pool_recycle=5, connect_args={"timeout": 30})
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine, autoflush=False)
        session = Session()

        for r in records:
            session.add(r)

        session.commit()
        session.close()
        return 0

    def __MakeWindowMock(self):
        r_response = MagicMock()

        type(r_response).get_indexes = lambda s: [1, 2, 3]

        return {"-LIST-": r_response}

    def test_GetURLType(self):
        """マイリストのタイプを返す機能のテスト
        """
        # 正常系
        # 投稿動画ページのURL
        url = "https://www.nicovideo.jp/user/11111111/video"
        actual = GuiFunction.GetURLType(url)
        expect = "uploaded"
        self.assertEqual(expect, actual)

        # マイリストURL
        url = "https://www.nicovideo.jp/user/11111111/mylist/00000011"
        actual = GuiFunction.GetURLType(url)
        expect = "mylist"
        self.assertEqual(expect, actual)

        # 異常系
        # マイリストのURLだがリダイレクト元のURL
        url = "https://www.nicovideo.jp/mylist/00000011"
        actual = GuiFunction.GetURLType(url)
        self.assertEqual("", actual)

        # 全く関係ないURL
        url = "https://www.google.co.jp/"
        actual = GuiFunction.GetURLType(url)
        self.assertEqual("", actual)

        # ニコニコの別サービスのURL
        url = "https://seiga.nicovideo.jp/seiga/im11111111"
        actual = GuiFunction.GetURLType(url)
        self.assertEqual("", actual)

    def test_GetNowDatetime(self):
        """タイムスタンプを返す機能のテスト
        """
        td_format = "%Y/%m/%d %H:%M"
        dts_format = "%Y-%m-%d %H:%M:%S"
        f_now = "2021-10-22 01:00:00"
        with freezegun.freeze_time(f_now):
            # 正常系
            actual = GuiFunction.GetNowDatetime()
            expect = f_now
            self.assertEqual(expect, actual)

            # 異常系
            actual = GuiFunction.GetNowDatetime()
            expect = datetime.strptime(f_now, dts_format) + timedelta(minutes=1)
            expect = expect.strftime(dts_format)
            self.assertNotEqual(expect, actual)

    def test_IsMylistIncludeNewVideo(self):
        """テーブルリスト内を走査する機能のテスト
        """
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        STATUS_INDEX = 4
        video_id_t = "sm100000{:02}"
        video_name_t = "動画タイトル_{:02}"
        video_url_t = "https://www.nicovideo.jp/watch/sm100000{:02}"
        mylist_url = "https://www.nicovideo.jp/user/11111111/mylist/10000011"
        username = "投稿者1"
        uploaded_t = "21-10-23 01:00:{:02}"
        myshowname = "投稿者1のマイリスト1"
        showname = f"「{myshowname}」-{username}さんのマイリスト"

        def TableListFactory():
            # 実際はタプルのリストだが値を修正してテストするためにリストのリストとする
            t = [
                [i, video_id_t.format(i), video_name_t.format(i), username, "", uploaded_t.format(i),
                 video_url_t.format(i), mylist_url, myshowname, showname] for i in range(1, 10)
            ]
            return t

        # 正常系
        # 全て視聴済
        table_list = TableListFactory()
        actual = GuiFunction.IsMylistIncludeNewVideo(table_list)
        self.assertEqual(False, actual)

        # 未視聴を含む
        table_list = TableListFactory()
        t_id = random.sample(range(0, len(table_list) - 1), 2)
        for i in t_id:
            table_list[i][STATUS_INDEX] = "未視聴"
        actual = GuiFunction.IsMylistIncludeNewVideo(table_list)
        self.assertEqual(True, actual)

        # 空リストはFalse
        actual = GuiFunction.IsMylistIncludeNewVideo([])
        self.assertEqual(False, actual)

        # 異常系
        # 要素数が少ない
        with self.assertRaises(KeyError):
            table_list = TableListFactory()
            table_list = [t[:STATUS_INDEX] for t in table_list]
            actual = GuiFunction.IsMylistIncludeNewVideo(table_list)
            self.assertEqual(False, actual)

        # 状況ステータスの位置が異なる
        with self.assertRaises(KeyError):
            table_list = TableListFactory()
            table_list = [[t[-1]] + t[:-1] for t in table_list]
            actual = GuiFunction.IsMylistIncludeNewVideo(table_list)
            self.assertEqual(False, actual)
        pass

    def test_IntervalTranslation(self):
        """インターバルを解釈する関数のテスト
        """
        # 正常系
        # 分
        e_val = random.randint(1, 59)
        interval_str = f"{e_val}分"
        actual = GuiFunction.IntervalTranslation(interval_str)
        expect = e_val
        self.assertEqual(expect, actual)

        # 時間
        e_val = random.randint(1, 23)
        interval_str = f"{e_val}時間"
        actual = GuiFunction.IntervalTranslation(interval_str)
        expect = e_val * 60
        self.assertEqual(expect, actual)

        # 日
        e_val = random.randint(1, 31)
        interval_str = f"{e_val}日"
        actual = GuiFunction.IntervalTranslation(interval_str)
        expect = e_val * 60 * 24
        self.assertEqual(expect, actual)

        # 週間
        e_val = random.randint(1, 5)
        interval_str = f"{e_val}週間"
        actual = GuiFunction.IntervalTranslation(interval_str)
        expect = e_val * 60 * 24 * 7
        self.assertEqual(expect, actual)

        # 月
        e_val = random.randint(1, 12)
        interval_str = f"{e_val}ヶ月"
        actual = GuiFunction.IntervalTranslation(interval_str)
        expect = e_val * 60 * 24 * 31
        self.assertEqual(expect, actual)

        # 異常系
        interval_str = "不正なinterval_str"
        actual = GuiFunction.IntervalTranslation(interval_str)
        expect = -1
        self.assertEqual(expect, actual)
        pass

    def test_UpdateMylistShow(self):
        """マイリストペインを更新する機能のテスト
        """
        with ExitStack() as stack:
            # mockcpb = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig", self.__MakeWindowMock))

            MAX_RECORD_NUM = 5
            records = []
            id_num = 1
            for i in range(0, MAX_RECORD_NUM):
                r = self.__MakeMylistSample(i)
                records.append(r)

            t_id = random.sample(range(0, len(records) - 1), 2)
            for i in t_id:
                records[i].is_include_new = True
            self.__LoadToTable(records)

            m_cont = MylistDBController(TEST_DB_PATH)

            # mock作成
            r_response = MagicMock()
            type(r_response).get_indexes = lambda s: [random.randint(0, len(records) - 1)]
            type(r_response).Values = []

            r_update = MagicMock()
            type(r_response).update = r_update

            r_widget = MagicMock()
            r_itemconfig = MagicMock()
            r_see = MagicMock()
            type(r_widget).itemconfig = r_itemconfig
            type(r_widget).see = r_see

            type(r_response).Widget = r_widget
            mockwin = {"-LIST-": r_response}
            actual = GuiFunction.UpdateMylistShow(mockwin, m_cont)
            self.assertEqual(0, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
