import sys
import unittest
from contextlib import ExitStack
from typing import Iterator

from mock import MagicMock, patch

from NNMM.process.value_objects.mylist_row import MylistRow
from NNMM.process.value_objects.mylist_row_list import MylistRowList


class TestMylistRowList(unittest.TestCase):
    def _get_mylist_row(self) -> MylistRow:
        return MylistRow.create("投稿者1さんの投稿動画")

    def test_init(self):
        mylist_row = MagicMock(spec=MylistRow)
        instance = MylistRowList([mylist_row])
        self.assertEqual([mylist_row], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = MylistRowList(params)

    def test_magic_method(self):
        mylist_row = MagicMock(spec=MylistRow)
        instance = MylistRowList([mylist_row])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], mylist_row)

        mylist_row_2 = MagicMock(spec=MylistRow)
        instance[0] = mylist_row_2
        self.assertEqual(instance[0], mylist_row_2)

    def test_to_name_list(self):
        mylist_row = self._get_mylist_row()
        instance = MylistRowList([mylist_row])
        actual = instance.to_name_list()
        expect = [mylist_row.name]
        self.assertEqual(expect, actual)

    def test_create(self):
        with ExitStack() as stack:
            mock_mylist_row = stack.enter_context(
                patch("NNMM.process.value_objects.mylist_row_list.MylistRow.create")
            )
            mylist_row = MagicMock(spec=MylistRow)
            mock_mylist_row.side_effect = lambda m: mylist_row

            actual = MylistRowList.create([mylist_row])
            self.assertEqual(MylistRowList([mylist_row]), actual)
            mock_mylist_row.assert_called_once_with(mylist_row)

            with self.assertRaises(ValueError):
                actual = MylistRowList.create("invalid")


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
