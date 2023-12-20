from contextlib import ExitStack
import sys
import unittest
from typing import Iterator

from mock import MagicMock, patch

from NNMM.process.update_mylist.value_objects.mylist_dict import MylistDict
from NNMM.process.update_mylist.value_objects.mylist_dict_list import MylistDictList


class TestMylistDictList(unittest.TestCase):
    def test_init(self):
        mylist_dict = MagicMock(spec=MylistDict)
        instance = MylistDictList([mylist_dict])
        self.assertEqual([mylist_dict], instance._list)

        params_list = [
            ["invalid"],
            "invalid"
        ]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = MylistDictList(params)

    def test_magic_method(self):
        mylist_dict = MagicMock(spec=MylistDict)
        instance = MylistDictList([mylist_dict])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], mylist_dict)

    def test_typed_mylist_list(self):
        with ExitStack() as stack:
            mock_typed_mylist_list = stack.enter_context(patch("NNMM.process.update_mylist.value_objects.mylist_dict_list.TypedMylistList.create"))
            mock_typed_mylist_list.side_effect = lambda m: "TypedMylistList.create()"
            mylist_dict = MagicMock(spec=MylistDict)
            mylist_dict.to_typed_mylist.side_effect = lambda: "to_typed_mylist()"

            instance = MylistDictList([mylist_dict])
            actual = instance.to_typed_mylist_list()
            self.assertEqual("TypedMylistList.create()", actual)
            mock_typed_mylist_list.assert_called_once_with(["to_typed_mylist()"])

    def test_create(self):
        with ExitStack() as stack:
            mock_mylist_dict = stack.enter_context(patch("NNMM.process.update_mylist.value_objects.mylist_dict_list.MylistDict.create"))
            mylist_dict = MagicMock(spec=MylistDict)
            mock_mylist_dict.side_effect = lambda m: mylist_dict

            actual = MylistDictList.create([mylist_dict])
            self.assertEqual(MylistDictList([mylist_dict]), actual)
            mock_mylist_dict.assert_called_once_with(mylist_dict)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
