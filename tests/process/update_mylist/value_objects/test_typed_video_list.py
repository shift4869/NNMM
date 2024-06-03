import sys
import unittest
from dataclasses import FrozenInstanceError
from typing import Iterator

from mock import MagicMock

from nnmm.process.update_mylist.value_objects.typed_video import TypedVideo
from nnmm.process.update_mylist.value_objects.typed_video_list import TypedVideoList


class TestTypedVideoList(unittest.TestCase):
    def test_init(self):
        typed_video = MagicMock(spec=TypedVideo)
        instance = TypedVideoList([typed_video])
        self.assertEqual([typed_video], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = TypedVideoList(params)

        with self.assertRaises(FrozenInstanceError):
            instance = TypedVideoList([typed_video])
            instance._list = []

    def test_magic_method(self):
        typed_video = MagicMock(spec=TypedVideo)
        instance = TypedVideoList([typed_video])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], typed_video)

        typed_video_2 = MagicMock(spec=TypedVideo)
        instance[0] = typed_video_2
        self.assertEqual(instance[0], typed_video_2)

    def test_create(self):
        typed_video = MagicMock(spec=TypedVideo)
        actual = TypedVideoList.create([typed_video])
        expect = TypedVideoList([typed_video])
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
