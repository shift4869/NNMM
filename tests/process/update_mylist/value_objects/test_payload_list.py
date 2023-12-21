import sys
import unittest
from contextlib import ExitStack
from dataclasses import FrozenInstanceError
from typing import Iterator

from mock import MagicMock, patch

from NNMM.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from NNMM.process.update_mylist.value_objects.payload import Payload
from NNMM.process.update_mylist.value_objects.payload_list import PayloadList
from NNMM.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


class TestPayloadList(unittest.TestCase):
    def test_init(self):
        payload = MagicMock(spec=Payload)
        instance = PayloadList([payload])
        self.assertEqual([payload], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = PayloadList(params)

        with self.assertRaises(FrozenInstanceError):
            instance = PayloadList([payload])
            instance._list = []

    def test_magic_method(self):
        payload = MagicMock(spec=Payload)
        instance = PayloadList([payload])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], payload)

    def test_create(self):
        with ExitStack() as stack:
            mock_create = stack.enter_context(
                patch("NNMM.process.update_mylist.value_objects.payload_list.Payload.create")
            )
            payload = MagicMock(spec=Payload)
            mock_create.side_effect = lambda mylist_with_videolist, fetched_info: payload

            mylist_with_video_list = MagicMock(spec=MylistWithVideoList)
            fetched_video_info = MagicMock(spec=FetchedVideoInfo)
            payload_tuple_list = [(mylist_with_video_list, fetched_video_info)]
            actual = PayloadList.create(payload_tuple_list)
            expect = PayloadList([payload])
            self.assertEqual(expect, actual)

            mylist_with_video_list = MagicMock(spec=MylistWithVideoList)
            payload_tuple_list = [(mylist_with_video_list, None)]
            actual = PayloadList.create(payload_tuple_list)
            expect = PayloadList([payload])
            self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
