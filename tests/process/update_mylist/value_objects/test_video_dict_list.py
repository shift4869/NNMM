import sys
import unittest
from contextlib import ExitStack
from typing import Iterator

from mock import MagicMock, patch

from nnmm.process.update_mylist.value_objects.video_dict import VideoDict
from nnmm.process.update_mylist.value_objects.video_dict_list import VideoDictList


class TestVideoDictList(unittest.TestCase):
    def test_init(self):
        video_dict = MagicMock(spec=VideoDict)
        instance = VideoDictList([video_dict])
        self.assertEqual([video_dict], instance._list)

        params_list = [["invalid"], "invalid"]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = VideoDictList(params)

    def test_magic_method(self):
        video_dict = MagicMock(spec=VideoDict)
        instance = VideoDictList([video_dict])
        self.assertIsInstance(iter(instance), Iterator)
        self.assertEqual(len(instance), 1)
        self.assertEqual(instance[0], video_dict)

    def test_to_typed_video_list(self):
        with ExitStack() as stack:
            mock_typed_video_list = stack.enter_context(
                patch("nnmm.process.update_mylist.value_objects.video_dict_list.TypedVideoList.create")
            )
            mock_typed_video_list.side_effect = lambda m: "TypedVideoList.create()"
            video_dict = MagicMock(spec=VideoDict)
            video_dict.to_typed_video.side_effect = lambda: "to_typed_video()"

            instance = VideoDictList([video_dict])
            actual = instance.to_typed_video_list()
            self.assertEqual("TypedVideoList.create()", actual)
            mock_typed_video_list.assert_called_once_with(["to_typed_video()"])

    def test_create(self):
        with ExitStack() as stack:
            mock_video_dict = stack.enter_context(
                patch("nnmm.process.update_mylist.value_objects.video_dict_list.VideoDict.create")
            )
            video_dict = MagicMock(spec=VideoDict)
            mock_video_dict.side_effect = lambda m: video_dict

            actual = VideoDictList.create([video_dict])
            self.assertEqual(VideoDictList([video_dict]), actual)
            mock_video_dict.assert_called_once_with(video_dict)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
