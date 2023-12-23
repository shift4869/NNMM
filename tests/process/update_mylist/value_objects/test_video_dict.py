import sys
import unittest
from contextlib import ExitStack

from mock import patch

from NNMM.process.update_mylist.value_objects.video_dict import VideoDict


class TestVideoDict(unittest.TestCase):
    def _make_video_dict(self, index: int = 1) -> dict[str, str]:
        uploaded_url = f"https://www.nicovideo.jp/user/1000000{index}/video"
        mylist_url = f"https://www.nicovideo.jp/user/1000000{index}/mylist/{index:08}"
        return {
            "id": str(index),
            "video_id": f"sm1234567{index}",
            "title": f"title_{index}",
            "username": f"username_{index}",
            "status": f"未視聴" if index == 1 else "",
            "uploaded_at": f"2023-12-22 12:34:5{index}",
            "registered_at": f"2023-12-22 12:34:5{index}",
            "video_url": f"https://www.nicovideo.jp/watch/sm1234567{index}",
            "mylist_url": uploaded_url if index == 1 else mylist_url,
            "created_at": f"2023-12-22 12:34:5{index}",
        }

    def test_init(self):
        video_dict = self._make_video_dict()
        instance = VideoDict(video_dict)
        self.assertEqual(video_dict, instance._dict)
        with self.assertRaises(ValueError):
            instance = VideoDict("invalid_arg")

    def test_is_valid(self):
        video_dict = self._make_video_dict()
        instance = VideoDict(video_dict)
        self.assertTrue(instance.is_valid())

        del video_dict["video_url"]
        object.__setattr__(instance, "_dict", video_dict)
        with self.assertRaises(ValueError):
            _ = instance.is_valid()
        with self.assertRaises(ValueError):
            instance = VideoDict({"invalid_key": "invalid_value"})

    def test_getitem(self):
        video_dict = self._make_video_dict()
        instance = VideoDict(video_dict)
        self.assertTrue(video_dict["video_url"], instance["video_url"])

    def test_to_typed_video(self):
        with ExitStack() as stack:
            mock_typed_video = stack.enter_context(
                patch("NNMM.process.update_mylist.value_objects.video_dict.TypedVideo.create")
            )
            mock_typed_video.side_effect = lambda m: "TypedVideo.create()"

            video_dict = self._make_video_dict()
            instance = VideoDict(video_dict)
            actual = instance.to_typed_video()
            self.assertEqual("TypedVideo.create()", actual)
            mock_typed_video.assert_called_once_with(video_dict)

    def test_create(self):
        video_dict = self._make_video_dict()
        actual = VideoDict.create(video_dict)
        expect = VideoDict(video_dict)
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
