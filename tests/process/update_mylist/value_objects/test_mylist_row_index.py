import sys
import unittest
from collections import namedtuple

from NNMM.process.update_mylist.value_objects.mylist_row_index import MylistRowIndex


class TestMylistRowIndex(unittest.TestCase):
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
                    instance = MylistRowIndex(params.index)
            else:
                instance = MylistRowIndex(params.index)
                self.assertEqual(params.result, instance._index)

    def test_int(self):
        instance = MylistRowIndex(0)
        self.assertEqual(0, int(instance))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
