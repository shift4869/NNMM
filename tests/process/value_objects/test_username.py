import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.process.value_objects.username import Username


class TestUsername(unittest.TestCase):
    def test_init(self):
        # 正常系
        username_str = "作成者1"
        username = Username(username_str)
        self.assertEqual(username_str, username._name)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            username = Username("作成者1")
            username._name = "作成者2"

        # 空文字列
        with self.assertRaises(ValueError):
            username = Username("")

        # 引数が文字列でない
        with self.assertRaises(TypeError):
            username = Username(-1)

    def test_name(self):
        username_str = "作成者1"
        username = Username(username_str)
        self.assertEqual(username_str, username._name)
        self.assertEqual(username._name, username.name)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
