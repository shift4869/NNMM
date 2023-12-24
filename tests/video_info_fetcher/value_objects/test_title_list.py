"""TitleList のテスト

TitleList の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.video_info_fetcher.value_objects.title import Title
from NNMM.video_info_fetcher.value_objects.title_list import TitleList


class TestTitleList(unittest.TestCase):
    def _get_title_strs(self):
        NUM = 5
        base_title = "動画タイトル{}"
        return [base_title.format(i) for i in range(1, NUM + 1)]

    def _get_titles(self):
        title_strs = self._get_title_strs()
        return [Title(r) for r in title_strs]

    def test_TitleListInit(self):
        """TitleList の初期化後の状態をテストする"""
        base_title = "動画タイトル{}"
        title_strs = self._get_title_strs()
        titles = self._get_titles()

        # 正常系
        # タイトルのリスト
        title_list = TitleList(titles)
        self.assertEqual(titles, title_list._list)

        # 空リスト
        title_list = TitleList([])
        self.assertEqual([], title_list._list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            title_list = TitleList(titles)
            title_list._list = [Title(base_title.format(1))]

        # 引数がlistでない
        with self.assertRaises(TypeError):
            title_list = TitleList(base_title.format(1))

        # 引数がlist[Title]でない
        with self.assertRaises(ValueError):
            title_list = TitleList(title_strs)

        # 引数のlistの要素のうち、一部がTitleでない
        num = len(titles)
        titles[num // 2] = base_title.format(num // 2)
        with self.assertRaises(ValueError):
            title_list = TitleList(titles)

    def test_iter_len(self):
        """iter と len のテスト"""
        titles = self._get_titles()
        title_list = TitleList(titles)
        self.assertEqual(len(titles), len(title_list))
        for expect, actual in zip(titles, title_list):
            self.assertEqual(expect, actual)

    def test_create(self):
        """create のテスト"""
        base_title = "動画タイトル{}"
        title_strs = self._get_title_strs()
        titles = self._get_titles()

        # 正常系
        # 空リスト
        title_list = TitleList.create([])
        self.assertEqual([], title_list._list)

        # タイトルのリスト
        title_list = TitleList.create(titles)
        self.assertEqual(titles, title_list._list)

        # タイトルを表す文字列のリスト
        title_list = TitleList.create(title_strs)
        self.assertEqual(titles, title_list._list)

        # 異常系
        # リストでない（str）
        with self.assertRaises(TypeError):
            title_list = TitleList.create(base_title.format(1))

        # リストでない（int）
        with self.assertRaises(TypeError):
            title_list = TitleList.create(-1)

        # リストだが要素がタイトルでも文字列でもない
        with self.assertRaises(ValueError):
            title_list = TitleList.create([-1])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
