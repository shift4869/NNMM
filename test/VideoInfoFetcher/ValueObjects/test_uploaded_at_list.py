"""UploadedAtList のテスト

UploadedAtList の各種機能をテストする
"""
import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.VideoInfoFetcher.ValueObjects.uploaded_at import UploadedAt
from NNMM.VideoInfoFetcher.ValueObjects.uploaded_at_list import UploadedAtList


class TestUploadedAtList(unittest.TestCase):
    def _get_dt_strs(self):
        NUM = 5
        base_dt_str = "2022-05-12 00:01:0{}"
        return [base_dt_str.format(i) for i in range(1, NUM + 1)]

    def _get_uploaded_ats(self):
        uploaded_at_strs = self._get_dt_strs()
        return [UploadedAt(r) for r in uploaded_at_strs]

    def test_UploadedAtListInit(self):
        """UploadedAtList の初期化後の状態をテストする
        """
        base_dt_str = "2022-05-12 00:01:0{}"
        uploaded_at_strs = self._get_dt_strs()
        uploaded_ats = self._get_uploaded_ats()

        # 正常系
        # 登録日時のリスト
        expect_destination_datetime_format = "%Y-%m-%d %H:%M:%S"
        uploaded_at_list = UploadedAtList(uploaded_ats)
        self.assertEqual(uploaded_ats, uploaded_at_list._list)
        self.assertEqual(expect_destination_datetime_format, UploadedAtList.DESTINATION_DATETIME_FORMAT)

        # 空リスト
        uploaded_at_list = UploadedAtList([])
        self.assertEqual([], uploaded_at_list._list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            uploaded_at_list = UploadedAtList(uploaded_ats)
            uploaded_at_list._list = [UploadedAt("2022-05-14 23:59:59")]

        # 引数がlistでない
        with self.assertRaises(TypeError):
            uploaded_at_list = UploadedAtList(base_dt_str.format(1))

        # 引数がlist[UploadedAt]でない
        with self.assertRaises(ValueError):
            uploaded_at_list = UploadedAtList(uploaded_at_strs)

        # 引数のlistの要素のうち、一部がUploadedAtでない
        num = len(uploaded_ats)
        uploaded_ats[num // 2] = base_dt_str.format(num // 2)
        with self.assertRaises(ValueError):
            uploaded_at_list = UploadedAtList(uploaded_ats)

    def test_iter_len(self):
        """iter と len のテスト
        """
        uploaded_ats = self._get_uploaded_ats()
        uploaded_at_list = UploadedAtList(uploaded_ats)
        self.assertEqual(len(uploaded_ats), len(uploaded_at_list))
        for expect, actual in zip(uploaded_ats, uploaded_at_list):
            self.assertEqual(expect, actual)

    def test_create(self):
        """create のテスト
        """
        uploaded_at_str = "2022-05-12 00:01:01"
        uploaded_at_strs = self._get_dt_strs()
        uploaded_ats = self._get_uploaded_ats()

        # 正常系
        # 空リスト
        uploaded_at_list = UploadedAtList.create([])
        self.assertEqual([], uploaded_at_list._list)

        # 登録日時のリスト
        uploaded_at_list = UploadedAtList.create(uploaded_ats)
        self.assertEqual(uploaded_ats, uploaded_at_list._list)

        # 登録日時を表す文字列のリスト
        uploaded_at_list = UploadedAtList.create(uploaded_at_strs)
        self.assertEqual(uploaded_ats, uploaded_at_list._list)

        # 異常系
        # リストでない（str）
        with self.assertRaises(TypeError):
            uploaded_at_list = UploadedAtList.create(uploaded_at_str)

        # リストでない（int）
        with self.assertRaises(TypeError):
            uploaded_at_list = UploadedAtList.create(-1)

        # リストだが要素が登録日時でも文字列でもない
        with self.assertRaises(ValueError):
            uploaded_at_list = UploadedAtList.create([-1])

        # 文字列のリストだが登録日時を表していない
        # UploadedAt のエラーが送出される
        with self.assertRaises(ValueError):
            uploaded_at_list = UploadedAtList.create(["不正な文字列"])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
