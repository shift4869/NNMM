import sys
import unittest
from typing import Iterator

from mock import MagicMock

from nnmm.process.value_objects.table_row_index import TableRowIndex
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList, TableRowIndexList


class TestTableRowIndexList(unittest.TestCase):
    def test_init(self):
        table_row = MagicMock(spec=TableRowIndex)
        instance = TableRowIndexList([table_row])
        self.assertEqual([table_row], instance._list)

        table_row = MagicMock(spec=TableRowIndex)
        instance = SelectedTableRowIndexList([table_row])
        self.assertEqual([table_row], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = TableRowIndexList(params)

        for params in params_list:
            with self.assertRaises(ValueError):
                instance = SelectedTableRowIndexList(params)

    def test_magic_method(self):
        table_row = MagicMock(spec=TableRowIndex)
        instance = TableRowIndexList([table_row])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], table_row)

        table_row_2 = MagicMock(spec=TableRowIndex)
        instance[0] = table_row_2
        self.assertEqual(instance[0], table_row_2)

    def test_to_int_list(self):
        table_row = TableRowIndex(1)
        instance = TableRowIndexList([table_row])
        actual = instance.to_int_list()
        expect = [1]
        self.assertEqual(expect, actual)

    def test_create(self):
        table_row = TableRowIndex(1)
        actual = TableRowIndexList.create([1])
        expect = TableRowIndexList([table_row])
        self.assertEqual(expect, actual)

        with self.assertRaises(ValueError):
            actual = TableRowIndexList.create("invalid")


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
