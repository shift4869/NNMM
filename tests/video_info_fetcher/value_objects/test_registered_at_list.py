"""RegisteredAtList のテスト

RegisteredAtList の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from nnmm.video_info_fetcher.value_objects.registered_at import RegisteredAt
from nnmm.video_info_fetcher.value_objects.registered_at_list import RegisteredAtList


class TestRegisteredAtList(unittest.TestCase):
    def _get_dt_strs(self):
        NUM = 5
        base_dt_str = "2022-05-12 00:01:0{}"
        return [base_dt_str.format(i) for i in range(1, NUM + 1)]

    def _get_registered_ats(self):
        registered_at_strs = self._get_dt_strs()
        return [RegisteredAt(r) for r in registered_at_strs]

    def test_RegisteredAtListInit(self):
        """RegisteredAtList の初期化後の状態をテストする"""
        base_dt_str = "2022-05-12 00:01:0{}"
        registered_at_strs = self._get_dt_strs()
        registered_ats = self._get_registered_ats()

        # 正常系
        # 登録日時のリスト
        expect_destination_datetime_format = "%Y-%m-%d %H:%M:%S"
        registered_at_list = RegisteredAtList(registered_ats)
        self.assertEqual(registered_ats, registered_at_list._list)
        self.assertEqual(expect_destination_datetime_format, RegisteredAtList.DESTINATION_DATETIME_FORMAT)

        # 空リスト
        registered_at_list = RegisteredAtList([])
        self.assertEqual([], registered_at_list._list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            registered_at_list = RegisteredAtList(registered_ats)
            registered_at_list._list = [RegisteredAt("2022-05-14 23:59:59")]

        # 引数がlistでない
        with self.assertRaises(TypeError):
            registered_at_list = RegisteredAtList(base_dt_str.format(1))

        # 引数がlist[RegisteredAt]でない
        with self.assertRaises(ValueError):
            registered_at_list = RegisteredAtList(registered_at_strs)

        # 引数のlistの要素のうち、一部がRegisteredAtでない
        num = len(registered_ats)
        registered_ats[num // 2] = base_dt_str.format(num // 2)
        with self.assertRaises(ValueError):
            registered_at_list = RegisteredAtList(registered_ats)

    def test_iter_len(self):
        """iter と len のテスト"""
        registered_ats = self._get_registered_ats()
        registered_at_list = RegisteredAtList(registered_ats)
        self.assertEqual(len(registered_ats), len(registered_at_list))
        for expect, actual in zip(registered_ats, registered_at_list):
            self.assertEqual(expect, actual)

    def test_create(self):
        """create のテスト"""
        registered_at_str = "2022-05-12 00:01:01"
        registered_at_strs = self._get_dt_strs()
        registered_ats = self._get_registered_ats()

        # 正常系
        # 空リスト
        registered_at_list = RegisteredAtList.create([])
        self.assertEqual([], registered_at_list._list)

        # 登録日時のリスト
        registered_at_list = RegisteredAtList.create(registered_ats)
        self.assertEqual(registered_ats, registered_at_list._list)

        # 登録日時を表す文字列のリスト
        registered_at_list = RegisteredAtList.create(registered_at_strs)
        self.assertEqual(registered_ats, registered_at_list._list)

        # 異常系
        # リストでない（str）
        with self.assertRaises(TypeError):
            registered_at_list = RegisteredAtList.create(registered_at_str)

        # リストでない（int）
        with self.assertRaises(TypeError):
            registered_at_list = RegisteredAtList.create(-1)

        # リストだが要素が登録日時でも文字列でもない
        with self.assertRaises(ValueError):
            registered_at_list = RegisteredAtList.create([-1])

        # 文字列のリストだが登録日時を表していない
        # RegisteredAt のエラーが送出される
        with self.assertRaises(ValueError):
            registered_at_list = RegisteredAtList.create(["不正な文字列"])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
