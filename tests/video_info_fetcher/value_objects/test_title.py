"""Title のテスト

Title の各種機能をテストする
"""

import sys
import unittest
from dataclasses import FrozenInstanceError

from nnmm.video_info_fetcher.value_objects.title import Title


class TestTitle(unittest.TestCase):
    def test_TitleInit(self):
        """Title の初期化後の状態をテストする"""
        # 正常系
        title_str = "動画タイトル1"
        title = Title(title_str)
        self.assertEqual(title_str, title._name)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            title = Title("動画タイトル1")
            title._name = "動画タイトル2"

        # 空文字列
        with self.assertRaises(ValueError):
            title = Title("")

        # 引数が文字列でない
        with self.assertRaises(TypeError):
            title = Title(-1)

    def test_name(self):
        """_name のテスト"""
        title_str = "動画タイトル1"
        title = Title(title_str)
        self.assertEqual(title_str, title._name)
        self.assertEqual(title._name, title.name)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
