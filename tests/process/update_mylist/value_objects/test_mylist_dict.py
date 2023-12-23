import sys
import unittest
from contextlib import ExitStack

from mock import patch

from NNMM.process.update_mylist.value_objects.mylist_dict import MylistDict


class TestMylistDict(unittest.TestCase):
    def _get_mylist_dict(self, index: int = 1) -> dict:
        return {
            "id": index,
            "username": f"username_{index}",
            "mylistname": f"mylistname_{index}",
            "type": f"uploaded",
            "showname": f"showname_{index}",
            "url": f"url_{index}",
            "created_at": "2023-12-21 12:34:56",
            "updated_at": "2023-12-21 12:34:56",
            "checked_at": "2023-12-21 12:34:56",
            "check_interval": "15分",
            "is_include_new": False,
        }

    def test_init(self):
        mylist_dict = self._get_mylist_dict()
        instance = MylistDict(mylist_dict)
        self.assertEqual(mylist_dict, instance._dict)
        with self.assertRaises(ValueError):
            instance = MylistDict("invalid_arg")

    def test_is_valid(self):
        mylist_dict = self._get_mylist_dict()
        instance = MylistDict(mylist_dict)
        self.assertTrue(instance.is_valid())

        del mylist_dict["url"]
        object.__setattr__(instance, "_dict", mylist_dict)
        with self.assertRaises(ValueError):
            _ = instance.is_valid()
        with self.assertRaises(ValueError):
            instance = MylistDict({"invalid_key": "invalid_value"})

    def test_getitem(self):
        mylist_dict = self._get_mylist_dict()
        instance = MylistDict(mylist_dict)
        self.assertTrue(mylist_dict["url"], instance["url"])

    def test_typed_mylist(self):
        with ExitStack() as stack:
            mock_typed_mylist = stack.enter_context(patch("NNMM.process.update_mylist.value_objects.mylist_dict.TypedMylist.create"))
            mock_typed_mylist.side_effect = lambda m: "TypedMylist.create()"

            mylist_dict = self._get_mylist_dict()
            instance = MylistDict(mylist_dict)
            actual = instance.to_typed_mylist()
            self.assertEqual("TypedMylist.create()", actual)
            mock_typed_mylist.assert_called_once_with(mylist_dict)

    def test_create(self):
        mylist_dict = self._get_mylist_dict()
        actual = MylistDict.create(mylist_dict)
        expect = MylistDict(mylist_dict)
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
