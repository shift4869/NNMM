import sys
import unittest
from contextlib import ExitStack
from typing import Iterator

from mock import MagicMock, patch

from nnmm.process.value_objects.table_row import TableRow
from nnmm.process.value_objects.table_row_list import SelectedTableRowList, TableRowList


class TestTableRowList(unittest.TestCase):
    def _get_table_row(self) -> TableRow:
        return TableRow.create("投稿者1さんの投稿動画")

    def test_init(self):
        table_row = MagicMock(spec=TableRow)
        instance = TableRowList([table_row])
        self.assertEqual([table_row], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = TableRowList(params)

        table_row = MagicMock(spec=TableRow)
        instance = SelectedTableRowList([table_row])
        self.assertEqual([table_row], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = SelectedTableRowList(params)

    def test_magic_method(self):
        table_row = MagicMock(spec=TableRow)
        instance = TableRowList([table_row])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], table_row)

        table_row_2 = MagicMock(spec=TableRow)
        instance[0] = table_row_2
        self.assertEqual(instance[0], table_row_2)

    def test_to_table_data(self):
        table_row = MagicMock(spec=TableRow)
        table_row.to_row = lambda: "table_row.to_row()"
        instance = TableRowList([table_row])
        actual = instance.to_table_data()
        expect = ["table_row.to_row()"]
        self.assertEqual(expect, actual)

    def test_to_table_row_list(self):
        table_row = MagicMock(spec=TableRow)
        table_row.to_namedtuple = lambda: "table_row.to_namedtuple()"
        instance = TableRowList([table_row])
        actual = instance.to_table_row_list()
        expect = ["table_row.to_namedtuple()"]
        self.assertEqual(expect, actual)

    def test_create(self):
        with ExitStack() as stack:
            mock_table_row = stack.enter_context(patch("nnmm.process.value_objects.table_row_list.TableRow.create"))
            table_row = MagicMock(spec=TableRow)
            mock_table_row.side_effect = lambda m: table_row

            actual = TableRowList.create([table_row])
            self.assertEqual(TableRowList([table_row]), actual)
            mock_table_row.assert_called_once_with(table_row)

            with self.assertRaises(ValueError):
                actual = TableRowList.create("invalid")


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
