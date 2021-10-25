# coding: utf-8
"""GuiFunction のテスト

GuiFunction の各種機能をテストする
Guiの処理部分はモックで動作確認する(実際にGUIは表示されない)
"""

import re
import random
import sys
import unittest
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from mock import MagicMock, patch, AsyncMock
from pathlib import Path

import freezegun
from NNMM import GuiFunction


class TestGetMyListInfo(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

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


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
