"""Videoid のテスト

Videoid の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.video_info_fetcher.value_objects.videoid import Videoid


class TestVideoid(unittest.TestCase):
    def test_VideoidInit(self):
        """Videoid の初期化後の状態をテストする"""
        # 正常系
        # 通常の動画ID
        id = "sm12345678"
        videoid = Videoid(id)
        self.assertEqual(id, videoid._id)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        id = "sm12345678"
        with self.assertRaises(FrozenInstanceError):
            videoid = Videoid(id)
            videoid._id = "sm23456789"

        # 空白
        id = ""
        with self.assertRaises(ValueError):
            videoid = Videoid(id)

        # パターン以外の文字列
        id = "-1"
        with self.assertRaises(ValueError):
            videoid = Videoid(id)

        # 引数が文字列でない
        id = -1
        with self.assertRaises(TypeError):
            videoid = Videoid(id)

    def test_id(self):
        """id のテスト"""
        id = "sm12345678"
        videoid = Videoid(id)
        self.assertEqual(id, videoid.id)
        self.assertEqual(videoid.id, videoid._id)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
