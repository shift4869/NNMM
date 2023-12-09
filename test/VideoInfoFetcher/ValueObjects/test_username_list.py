"""UsernameList のテスト

UsernameList の各種機能をテストする
"""
import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.VideoInfoFetcher.ValueObjects.username import Username
from NNMM.VideoInfoFetcher.ValueObjects.username_list import UsernameList


class TestUsernameList(unittest.TestCase):
    def _get_dt_strs(self):
        NUM = 5
        base_name = "作成者{}"
        return [base_name.format(i) for i in range(1, NUM + 1)]

    def _get_usernames(self):
        username_strs = self._get_dt_strs()
        return [Username(r) for r in username_strs]

    def test_UsernameListInit(self):
        """UsernameList の初期化後の状態をテストする
        """
        base_name = "作成者{}"
        username_strs = self._get_dt_strs()
        usernames = self._get_usernames()

        # 正常系
        # Username のリスト
        username_list = UsernameList(usernames)
        self.assertEqual(usernames, username_list._list)

        # 空リスト
        username_list = UsernameList([])
        self.assertEqual([], username_list._list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            username_list = UsernameList(usernames)
            username_list._list = [Username(base_name.format(1))]

        # 引数がlistでない
        with self.assertRaises(TypeError):
            username_list = UsernameList(base_name.format(1))

        # 引数がlist[Username]でない
        with self.assertRaises(ValueError):
            username_list = UsernameList(username_strs)

        # 引数のlistの要素のうち、一部がUsernameでない
        num = len(usernames)
        usernames[num // 2] = base_name.format(num // 2)
        with self.assertRaises(ValueError):
            username_list = UsernameList(usernames)

    def test_iter_len(self):
        """iter と len のテスト
        """
        usernames = self._get_usernames()
        username_list = UsernameList(usernames)
        self.assertEqual(len(usernames), len(username_list))
        for expect, actual in zip(usernames, username_list):
            self.assertEqual(expect, actual)

    def test_create(self):
        """create のテスト
        """
        base_name = "作成者{}"
        username_strs = self._get_dt_strs()
        usernames = self._get_usernames()

        # 正常系
        # 空リスト
        username_list = UsernameList.create([])
        self.assertEqual([], username_list._list)

        # ユーザー名のリスト
        username_list = UsernameList.create(usernames)
        self.assertEqual(usernames, username_list._list)

        # ユーザー名を表す文字列のリスト
        username_list = UsernameList.create(username_strs)
        self.assertEqual(usernames, username_list._list)

        # 異常系
        # リストでない（str）
        with self.assertRaises(TypeError):
            username_list = UsernameList.create(base_name.format(1))

        # リストでない（int）
        with self.assertRaises(TypeError):
            username_list = UsernameList.create(-1)

        # リストだが要素がユーザー名でも文字列でもない
        with self.assertRaises(ValueError):
            username_list = UsernameList.create([-1])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
