# coding: utf-8
"""Showname のテスト

Showname の各種機能をテストする
"""
import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.VideoInfoFetcher.ValueObjects.Myshowname import Myshowname
from NNMM.VideoInfoFetcher.ValueObjects.Showname import Showname
from NNMM.VideoInfoFetcher.ValueObjects.Username import Username


class TestShowname(unittest.TestCase):
    def test_ShownameInit(self):
        """Showname の初期化後の状態をテストする
        """
        # 正常系
        EXPECT_UPLOADED_PATTERN = "^(.*)さんの投稿動画$"
        EXPECT_MYLIST_PATTERN = "^「(.*)」-(.*)さんのマイリスト$"

        # 投稿動画のマイリスト表示名パターン
        showname_str = "投稿者1さんの投稿動画"
        showname = Showname(showname_str)
        self.assertEqual(showname_str, showname._name)
        self.assertEqual(EXPECT_UPLOADED_PATTERN, Showname.UPLOADED_PATTERN)

        # マイリストのマイリスト表示名パターン
        showname_str = "「テスト用マイリスト1」-投稿者1さんのマイリスト"
        showname = Showname(showname_str)
        self.assertEqual(showname_str, showname._name)
        self.assertEqual(EXPECT_MYLIST_PATTERN, Showname.MYLIST_PATTERN)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            showname = Showname("投稿者1さんの投稿動画")
            showname._name = "投稿者2さんの投稿動画"

        # パターンでない文字列
        with self.assertRaises(ValueError):
            showname = Showname("不正な文字列")

        # 引数が文字列でない
        with self.assertRaises(TypeError):
            showname = Showname(-1)

    def test_name(self):
        """_name のテスト
        """
        showname_str = "投稿者1さんの投稿動画"
        showname = Showname(showname_str)
        self.assertEqual(showname_str, showname._name)
        self.assertEqual(showname._name, showname.name)

    def test_create(self):
        """create のテスト
        """
        # 正常系
        # 投稿動画のマイリスト表示名
        username = Username("投稿者1")
        myshowname = Myshowname("テスト用マイリスト1")

        expect_showname = "投稿者1さんの投稿動画"
        showname = Showname.create(username, None)
        self.assertEqual(expect_showname, showname.name)

        # マイリストのマイリスト表示名
        expect_showname = "「テスト用マイリスト1」-投稿者1さんのマイリスト"
        showname = Showname.create(username, myshowname)
        self.assertEqual(expect_showname, showname.name)

        # 異常系
        # 入力がどちらもNone
        with self.assertRaises(AttributeError):
            showname = Showname.create(None, None)

        # usernameのみNone
        with self.assertRaises(AttributeError):
            showname = Showname.create(None, myshowname)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
