"""Userid のテスト

Userid の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.video_info_fetcher.value_objects.userid import Userid


class TestUserid(unittest.TestCase):
    def test_UseridInit(self):
        """Userid の初期化後の状態をテストする"""
        # 正常系
        # 通常のユーザーID
        id = "12345678"
        userid = Userid(id)
        self.assertEqual(id, userid._id)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        id = "12345678"
        with self.assertRaises(FrozenInstanceError):
            userid = Userid(id)
            userid._id = "2345678"

        # 空白 -> ユーザーIDでは空白は許容されない
        id = ""
        with self.assertRaises(ValueError):
            userid = Userid(id)
            self.assertEqual(id, userid._id)

        # 数字以外の文字が含まれる文字列
        id = "-1"
        with self.assertRaises(ValueError):
            userid = Userid(id)

        # 引数が文字列でない
        id = -1
        with self.assertRaises(TypeError):
            userid = Userid(id)

    def test_id(self):
        """id のテスト"""
        id = "12345678"
        userid = Userid(id)
        self.assertEqual(id, userid.id)
        self.assertEqual(userid.id, userid._id)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
