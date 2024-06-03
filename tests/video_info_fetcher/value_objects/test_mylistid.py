"""Mylistid のテスト

Mylistid の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from nnmm.video_info_fetcher.value_objects.mylistid import Mylistid


class TestMylistid(unittest.TestCase):
    def test_MylistidInit(self):
        """Mylistid の初期化後の状態をテストする"""
        # 正常系
        # 通常のマイリストID
        id = "1234567"
        mylistid = Mylistid(id)
        self.assertEqual(id, mylistid._id)

        # 空白 -> マイリストIDでは空白は許容される
        id = ""
        mylistid = Mylistid(id)
        self.assertEqual(id, mylistid._id)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        id = "1234567"
        with self.assertRaises(FrozenInstanceError):
            mylistid = Mylistid(id)
            mylistid._id = "2345678"

        # 数字以外の文字が含まれる文字列
        id = "-1"
        with self.assertRaises(ValueError):
            mylistid = Mylistid(id)

        # 引数が文字列でない
        id = -1
        with self.assertRaises(TypeError):
            mylistid = Mylistid(id)

    def test_id(self):
        """id のテスト"""
        id = "1234567"
        mylistid = Mylistid(id)
        self.assertEqual(id, mylistid.id)
        self.assertEqual(mylistid.id, mylistid._id)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
