import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.process.update_mylist.value_objects.myshowname import Myshowname


class TestMyshowname(unittest.TestCase):
    def test_init(self):
        """Myshowname の初期化後の状態をテストする
        """
        # 正常系
        myshowname_str = "テスト用マイリスト1"
        myshowname = Myshowname(myshowname_str)
        self.assertEqual(myshowname_str, myshowname._name)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            myshowname = Myshowname("テスト用マイリスト1")
            myshowname._name = "テスト用マイリスト2"

        # 空文字列
        with self.assertRaises(ValueError):
            myshowname = Myshowname("")

        # 引数が文字列でない
        with self.assertRaises(TypeError):
            myshowname = Myshowname(-1)

    def test_name(self):
        """_name のテスト
        """
        myshowname_str = "テスト用マイリスト1"
        myshowname = Myshowname(myshowname_str)
        self.assertEqual(myshowname_str, myshowname._name)
        self.assertEqual(myshowname._name, myshowname.name)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
