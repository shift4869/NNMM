import sys
import unittest
from dataclasses import FrozenInstanceError
from typing import Iterator

from mock import MagicMock

from nnmm.process.update_mylist.value_objects.typed_mylist import TypedMylist
from nnmm.process.update_mylist.value_objects.typed_mylist_list import TypedMylistList


class TestTypedMylistList(unittest.TestCase):
    def test_init(self):
        typed_mylist = MagicMock(spec=TypedMylist)
        instance = TypedMylistList([typed_mylist])
        self.assertEqual([typed_mylist], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = TypedMylistList(params)

        with self.assertRaises(FrozenInstanceError):
            instance = TypedMylistList([typed_mylist])
            instance._list = []

    def test_magic_method(self):
        typed_mylist = MagicMock(spec=TypedMylist)
        instance = TypedMylistList([typed_mylist])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], typed_mylist)

    def test_create(self):
        typed_mylist = MagicMock(spec=TypedMylist)
        actual = TypedMylistList.create([typed_mylist])
        expect = TypedMylistList([typed_mylist])
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
