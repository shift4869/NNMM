# coding: utf-8
"""GuiFunction のテスト

GuiFunction の各種機能をテストする
Guiの処理部分はモックで動作確認する(実際にGUIは表示されない)
"""

import random
import re
import sys
import unittest
from contextlib import ExitStack
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path

import freezegun
from mock import AsyncMock, MagicMock, PropertyMock, patch
from sqlalchemy import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM import GuiFunction
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *

TEST_DB_PATH = "./test/test.db"


class TestGetMyListInfo(unittest.TestCase):

    def setUp(self):
        Path(TEST_DB_PATH).unlink(missing_ok=True)
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

    def __LoadToMylistTable(self, records) -> list[dict]:
        """テスト用のMylist初期レコードを格納したテーブルを用意する

        Args:
            records (list[Mylist]): 格納するレコードの配列
        """
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

    def __GetVideoInfoSet(self) -> list[tuple]:
        """動画情報セットを返す（mylist_url以外）
        """
        video_info = [
            ("sm11111111", "動画タイトル1", "投稿者1", "未視聴", "2021-05-29 22:00:11", "2021-05-29 22:01:11", "https://www.nicovideo.jp/watch/sm11111111", "2021-10-16 00:00:11"),
            ("sm22222222", "動画タイトル2", "投稿者1", "未視聴", "2021-05-29 22:00:22", "2021-05-29 22:02:22", "https://www.nicovideo.jp/watch/sm22222222", "2021-10-16 00:00:22"),
            ("sm33333333", "動画タイトル3", "投稿者1", "未視聴", "2021-05-29 22:00:33", "2021-05-29 22:03:33", "https://www.nicovideo.jp/watch/sm33333333", "2021-10-16 00:00:33"),
            ("sm44444444", "動画タイトル4", "投稿者2", "未視聴", "2021-05-29 22:00:44", "2021-05-29 22:04:44", "https://www.nicovideo.jp/watch/sm44444444", "2021-10-16 00:00:44"),
            ("sm55555555", "動画タイトル5", "投稿者2", "未視聴", "2021-05-29 22:00:55", "2021-05-29 22:05:55", "https://www.nicovideo.jp/watch/sm55555555", "2021-10-16 00:00:55"),
        ]
        return video_info

    def __MakeMylistInfoSample(self, id: int, mylist_id: int) -> MylistInfo:
        """MylistInfoオブジェクトを作成する

        Note:
            動画情報セット
                video_id (str): 動画ID(smxxxxxxxx)
                title (str): 動画タイトル
                username (str): 投稿者名
                status (str): 視聴状況({"未視聴", ""})
                uploaded_at (str): 投稿日時
                registered_at (str): 登録日時
                video_url (str): 動画URL
                created_at (str): 作成日時
            マイリスト情報セット
                mylist_url (str): 所属マイリストURL

        Args:
            id (int): 動画情報セットのid
            mylist_id (int): マイリスト情報セットのid

        Returns:
            MylistInfo: MylistInfoオブジェクト
        """
        v = self.__GetVideoInfoSet()[id]
        mylist_url = self.__GetURLInfoSet()[mylist_id]
        r = MylistInfo(v[0], v[1], v[2], v[3], v[4], v[5], v[6], mylist_url, v[7])
        return r

    def __LoadToMylistInfoTable(self) -> list[dict]:
        """テスト用の初期レコードを格納したテーブルを用意する
        """

        dbname = TEST_DB_PATH
        engine = create_engine(f"sqlite:///{dbname}", echo=False, pool_recycle=5, connect_args={"timeout": 30})
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine, autoflush=False)
        session = Session()

        MAX_VIDEO_INFO_NUM = 5
        MAX_URL_INFO_NUM = 5
        for i in range(0, MAX_URL_INFO_NUM):
            for j in range(0, MAX_VIDEO_INFO_NUM):
                r = self.__MakeMylistInfoSample(j, i)
                session.add(r)

        session.commit()
        session.close()
        return 0

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
        src_df = "%Y/%m/%d %H:%M"
        dst_df = "%Y-%m-%d %H:%M:%S"
        f_now = "2021-10-22 01:00:00"
        with freezegun.freeze_time(f_now):
            # 正常系
            actual = GuiFunction.GetNowDatetime()
            expect = f_now
            self.assertEqual(expect, actual)

            # 異常系
            actual = GuiFunction.GetNowDatetime()
            expect = datetime.strptime(f_now, dst_df) + timedelta(minutes=1)
            expect = expect.strftime(dst_df)
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
        """マイリストペインの表示を更新する機能のテスト
        """
        MAX_RECORD_NUM = 5
        records = []
        for i in range(0, MAX_RECORD_NUM):
            r = self.__MakeMylistSample(i)
            records.append(r)

        t_id = random.sample(range(0, len(records) - 1), 2)
        for i in t_id:
            records[i].is_include_new = True
        self.__LoadToMylistTable(records)

        m_cont = MylistDBController(TEST_DB_PATH)

        # mock作成
        e_index = random.randint(0, len(records) - 1)
        r_response = MagicMock()
        type(r_response).get_indexes = lambda s: [e_index]
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

        # 実行
        actual = GuiFunction.UpdateMylistShow(mockwin, m_cont)
        self.assertEqual(0, actual)

        # mock呼び出し確認
        NEW_MARK = "*:"
        m_list = m_cont.select()
        e_include_new_index_list = []
        expect = []
        for i, m in enumerate(m_list):
            if m["is_include_new"]:
                m["showname"] = NEW_MARK + m["showname"]
                e_include_new_index_list.append(i)
        expect = [m["showname"] for m in m_list]

        # ucal[{n回目の呼び出し}][kwargs=1]
        ucal = r_update.call_args_list
        self.assertEqual(len(ucal), 2)
        self.assertEqual({"values": expect}, ucal[0][1])
        self.assertEqual({"set_to_index": e_index}, ucal[1][1])

        # ical[{n回目の呼び出し}][args=0]
        # ical[{n回目の呼び出し}][kwargs=1]
        ical = r_itemconfig.call_args_list
        self.assertEqual(len(ical), len(e_include_new_index_list))
        for c, i in zip(ical, e_include_new_index_list):
            self.assertEqual((i, ), c[0])
            self.assertEqual({"fg": "black", "bg": "light pink"}, c[1])

        # scal[{n回目の呼び出し}][args=0]
        scal = r_see.call_args_list
        self.assertEqual(len(scal), 1)
        self.assertEqual((e_index, ), scal[0][0])

    def test_UpdateTableShow(self):
        """テーブルリストペインの表示を更新する機能のテスト
        """
        MAX_RECORD_NUM = 5
        records = []
        for i in range(0, MAX_RECORD_NUM):
            r = self.__MakeMylistSample(i)
            records.append(r)
        self.__LoadToMylistTable(records)
        self.__LoadToMylistInfoTable()

        m_cont = MylistDBController(TEST_DB_PATH)
        mb_cont = MylistInfoDBController(TEST_DB_PATH)

        # mock作成
        e_index = random.randint(0, len(records) - 1)
        mylist_url = self.__GetURLInfoSet()[e_index]
        r_list = MagicMock()
        r_listWidget = MagicMock()
        r_listsee = MagicMock()
        type(r_listWidget).see = r_listsee
        type(r_list).Widget = r_listWidget
        type(r_list).get_indexes = lambda s: [e_index]

        r_input = MagicMock()
        r_inputget = MagicMock()
        r_inputget.side_effect = [mylist_url, ""]  # 1回目は正常、2回目は空
        type(r_input).get = lambda s: r_inputget(s)

        r_table = MagicMock()
        r_tableupdate = MagicMock()
        type(r_table).update = r_tableupdate
        r_values = PropertyMock()
        r_values.return_value = ["values"]
        type(r_table).Values = r_values

        mockwin = {
            "-INPUT1-": r_input,
            "-LIST-": r_list,
            "-TABLE-": r_table,
        }

        # 1回目の実行
        actual = GuiFunction.UpdateTableShow(mockwin, m_cont, mb_cont)
        self.assertEqual(0, actual)

        # mock呼び出し確認
        expect = []
        records = mb_cont.select_from_mylist_url(mylist_url)
        for i, m in enumerate(records):
            a = [i + 1, m["video_id"], m["title"], m["username"], m["status"], m["uploaded_at"], m["registered_at"], m["video_url"], m["mylist_url"]]
            expect.append(a)

        # window["-INPUT1-"].get()の呼び出し確認
        self.assertEqual(r_inputget.call_count, 1)
        r_inputget.reset_mock()

        # lucal[{n回目の呼び出し}][args=0]
        lucal = r_listsee.call_args_list
        self.assertEqual(len(lucal), 1)
        self.assertEqual((e_index, ), lucal[0][0])
        r_listsee.reset_mock()

        # tucal[{n回目の呼び出し}][kwargs=1]
        tucal = r_tableupdate.call_args_list
        self.assertEqual(len(tucal), 3)
        self.assertEqual({"values": expect}, tucal[0][1])
        self.assertEqual({"select_rows": [0]}, tucal[1][1])
        self.assertEqual({"row_colors": [(0, "", "")]}, tucal[2][1])
        r_tableupdate.reset_mock()

        # 2回目の実行
        actual = GuiFunction.UpdateTableShow(mockwin, m_cont, mb_cont)
        self.assertEqual(0, actual)

        # window["-INPUT1-"].get()が呼び出されていることを確認
        self.assertEqual(r_inputget.call_count, 1)
        r_inputget.reset_mock()

        # window["-TABLE-"].Valuesが呼び出されていることを確認
        self.assertEqual(r_values.call_count, 1)
        r_values.reset_mock()

        # lical[{n回目の呼び出し}][kwargs=1]
        lucal = r_listsee.call_args_list
        self.assertEqual(len(lucal), 1)
        self.assertEqual((e_index, ), lucal[0][0])
        r_listsee.reset_mock()

        # tucal[{n回目の呼び出し}][kwargs=1]
        tucal = r_tableupdate.call_args_list
        self.assertEqual(len(tucal), 3)
        self.assertEqual({"values": ["values"]}, tucal[0][1])
        self.assertEqual({"select_rows": [0]}, tucal[1][1])
        self.assertEqual({"row_colors": [(0, "", "")]}, tucal[2][1])
        r_tableupdate.reset_mock()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
