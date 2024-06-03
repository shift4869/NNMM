import sys
import unittest
from dataclasses import FrozenInstanceError

from nnmm.process.update_mylist.value_objects.updated_at import UpdatedAt


class TestUpdatedAt(unittest.TestCase):
    def test_init(self):
        # 正常系
        # 通常の投稿日時
        expect_destination_datetime_format = "%Y-%m-%d %H:%M:%S"
        dt_str = "2022-05-14 00:01:00"
        uploaded_at = UpdatedAt(dt_str)
        self.assertEqual(dt_str, uploaded_at._datetime)
        self.assertEqual(expect_destination_datetime_format, UpdatedAt.DESTINATION_DATETIME_FORMAT)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        dt_str = "2022-05-14 00:01:00"
        with self.assertRaises(FrozenInstanceError):
            uploaded_at = UpdatedAt(dt_str)
            uploaded_at._datetime = "2022-05-14 23:59:59"

        # UpdatedAt.DESTINATION_DATETIME_FORMAT 形式でない文字列
        dt_str = "2022/05/14 00:01:00"
        with self.assertRaises(ValueError):
            uploaded_at = UpdatedAt(dt_str)

        # 空白
        dt_str = ""
        with self.assertRaises(ValueError):
            uploaded_at = UpdatedAt(dt_str)

        # 引数が文字列でない
        dt_str = -1
        with self.assertRaises(TypeError):
            uploaded_at = UpdatedAt(dt_str)

    def test_dt_str(self):
        """dt_str のテスト"""
        dt_str = "2022-05-14 00:01:00"
        uploaded_at = UpdatedAt(dt_str)
        self.assertEqual(dt_str, uploaded_at.dt_str)
        self.assertEqual(uploaded_at.dt_str, uploaded_at._datetime)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
