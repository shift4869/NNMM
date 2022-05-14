# coding: utf-8
"""RegisteredAt のテスト

RegisteredAt の各種機能をテストする
"""
import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.VideoInfoFetcher.RegisteredAt import RegisteredAt


class TestRegisteredAt(unittest.TestCase):
    def test_RegisteredAtInit(self):
        """RegisteredAt の初期化後の状態をテストする
        """
        # 正常系
        # 通常の登録日時
        expect_destination_datetime_format = "%Y-%m-%d %H:%M:%S"
        dt_str = "2022-05-14 00:01:00"
        registered_at = RegisteredAt(dt_str)
        self.assertEqual(dt_str, registered_at._datetime)
        self.assertEqual(expect_destination_datetime_format, RegisteredAt.DESTINATION_DATETIME_FORMAT)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        dt_str = "2022-05-14 00:01:00"
        with self.assertRaises(FrozenInstanceError):
            registered_at = RegisteredAt(dt_str)
            registered_at._datetime = "2022-05-14 23:59:59"

        # RegisteredAt.DESTINATION_DATETIME_FORMAT 形式でない文字列
        dt_str = "2022/05/14 00:01:00"
        with self.assertRaises(ValueError):
            registered_at = RegisteredAt(dt_str)

        # 空白
        dt_str = ""
        with self.assertRaises(ValueError):
            registered_at = RegisteredAt(dt_str)

        # 引数が文字列でない
        dt_str = -1
        with self.assertRaises(TypeError):
            registered_at = RegisteredAt(dt_str)

    def test_dt_str(self):
        """dt_str のテスト
        """
        dt_str = "2022-05-14 00:01:00"
        registered_at = RegisteredAt(dt_str)
        self.assertEqual(dt_str, registered_at.dt_str)
        self.assertEqual(registered_at.dt_str, registered_at._datetime)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
