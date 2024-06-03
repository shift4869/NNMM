import sys
import unittest
from collections import namedtuple
from dataclasses import FrozenInstanceError

from mock import MagicMock

from nnmm.process.update_mylist.value_objects.mylist_with_video import MylistWithVideo
from nnmm.process.update_mylist.value_objects.payload import Payload
from nnmm.util import Result
from nnmm.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


class TestPayload(unittest.TestCase):
    def test_init(self):
        mylist_with_video = MagicMock(spec=MylistWithVideo)
        fetched_info = MagicMock(spec=FetchedVideoInfo)

        instance = Payload(mylist_with_video, fetched_info)
        self.assertEqual(mylist_with_video, instance._mylist_with_video)
        self.assertEqual(fetched_info, instance._fetched_info)

        instance = Payload(mylist_with_video, Result.failed)
        self.assertEqual(mylist_with_video, instance._mylist_with_video)
        self.assertEqual(Result.failed, instance._fetched_info)

        Params = namedtuple("Params", ["mylist_with_video", "fetched_info"])
        params_list = [
            Params(mylist_with_video, Result.success),
            Params(mylist_with_video, "invalid"),
            Params("invalid", fetched_info),
        ]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = Payload(params.mylist_with_video, params.fetched_info)

        with self.assertRaises(FrozenInstanceError):
            instance = Payload(mylist_with_video, fetched_info)
            instance._fetched_info = Result.failed

    def test_property(self):
        mylist_with_video = MagicMock(spec=MylistWithVideo)
        fetched_info = MagicMock(spec=FetchedVideoInfo)
        instance = Payload(mylist_with_video, fetched_info)

        self.assertEqual(mylist_with_video, instance.mylist_with_video)
        self.assertEqual(mylist_with_video.mylist, instance.mylist)
        self.assertEqual(mylist_with_video.video_list, instance.video_list)
        self.assertEqual(fetched_info, instance.fetched_info)

    def test_create(self):
        mylist_with_video = MagicMock(spec=MylistWithVideo)
        fetched_info = MagicMock(spec=FetchedVideoInfo)
        actual = Payload.create(mylist_with_video, fetched_info)
        expect = Payload(mylist_with_video, fetched_info)
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
