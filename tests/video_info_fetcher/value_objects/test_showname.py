import sys
import unittest
from collections import namedtuple
from dataclasses import FrozenInstanceError

from NNMM.util import MylistType
from NNMM.video_info_fetcher.value_objects.myshowname import Myshowname
from NNMM.video_info_fetcher.value_objects.showname import Showname
from NNMM.video_info_fetcher.value_objects.username import Username


class TestShowname(unittest.TestCase):
    def test_init(self):
        EXPECT_UPLOADED_PATTERN = "^(.*)さんの投稿動画$"
        EXPECT_MYLIST_PATTERN = "^「(.*)」-(.*)さんのマイリスト$"
        EXPECT_SERIES_PATTERN = "^「(.*)」-(.*)さんのシリーズ$"

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

        # シリーズのマイリスト表示名パターン
        showname_str = "「テスト用シリーズ1」-投稿者1さんのシリーズ"
        showname = Showname(showname_str)
        self.assertEqual(showname_str, showname._name)
        self.assertEqual(EXPECT_SERIES_PATTERN, Showname.SERIES_PATTERN)

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
        showname_str = "投稿者1さんの投稿動画"
        showname = Showname(showname_str)
        self.assertEqual(showname_str, showname._name)
        self.assertEqual(showname._name, showname.name)

    def test_create(self):
        username = Username("投稿者1")
        myshowname = Myshowname("テスト用マイリスト1")

        Params = namedtuple("Params", ["mylist_type", "username", "myshowname", "result"])
        params_list: list[Params] = [
            Params(MylistType.uploaded, username, None, "投稿者1さんの投稿動画"),
            Params(MylistType.mylist, username, myshowname, "「テスト用マイリスト1」-投稿者1さんのマイリスト"),
            Params(
                MylistType.series,
                username,
                Myshowname("テスト用シリーズ1"),
                "「テスト用シリーズ1」-投稿者1さんのシリーズ",
            ),
            Params(MylistType.none, username, myshowname, None),
            Params(MylistType.mylist, username, None, None),
            Params(MylistType.mylist, username, -1, None),
            Params(MylistType.uploaded, None, None, None),
            Params(None, username, myshowname, None),
        ]

        for params in params_list:
            if expect := params.result:
                actual = Showname.create(
                    params.mylist_type,
                    params.username,
                    params.myshowname if params.myshowname else None,
                )
                self.assertEqual(expect, actual.name)
            else:
                with self.assertRaises(ValueError):
                    actual = Showname.create(
                        params.mylist_type,
                        params.username,
                        params.myshowname if params.myshowname else None,
                    )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
