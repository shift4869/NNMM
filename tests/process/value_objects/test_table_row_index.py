import sys
import unittest
from collections import namedtuple

from nnmm.process.value_objects.table_row_index import TableRowIndex


class TestTableRowIndex(unittest.TestCase):
    def test_init(self):
        Params = namedtuple("Params", ["index", "result"])
        params_list = [
            Params(0, 0),
            Params(1, 1),
            Params(5, 5),
            Params(-1, "invalid"),
            Params("1", "invalid"),
        ]
        for params in params_list:
            if params.result == "invalid":
                with self.assertRaises(ValueError):
                    instance = TableRowIndex(params.index)
            else:
                instance = TableRowIndex(params.index)
                self.assertEqual(params.result, instance._index)

    def test_int(self):
        instance = TableRowIndex(0)
        self.assertEqual(0, int(instance))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
