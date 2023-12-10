"""FetchedAPIVideoInfo のテスト

FetchedAPIVideoInfo の各種機能をテストする
"""
import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.video_info_fetcher.value_objects.fetched_api_video_info import FetchedAPIVideoInfo
from NNMM.video_info_fetcher.value_objects.title_list import TitleList
from NNMM.video_info_fetcher.value_objects.uploaded_at_list import UploadedAtList
from NNMM.video_info_fetcher.value_objects.username_list import UsernameList
from NNMM.video_info_fetcher.value_objects.video_url_list import VideoURLList
from NNMM.video_info_fetcher.value_objects.videoid_list import VideoidList


class TestFetchedAPIVideoInfo(unittest.TestCase):
    def test_FetchedAPIVideoInfoInit(self):
        """FetchedAPIVideoInfo の初期化後の状態をテストする
        """
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
        fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, uploaded_at_list,
                                      video_url_list, username_list)
        self.assertEqual(no, fvi_api.no)
        self.assertEqual(video_id_list, fvi_api.video_id_list)
        self.assertEqual(title_list, fvi_api.title_list)
        self.assertEqual(uploaded_at_list, fvi_api.uploaded_at_list)
        self.assertEqual(video_url_list, fvi_api.video_url_list)
        self.assertEqual(username_list, fvi_api.username_list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, uploaded_at_list,
                                          video_url_list, username_list)
            fvi_api.username_list = UsernameList.create(["投稿者2"])

    def test_is_valid(self):
        """_is_valid のテスト
        """
        title_list = TitleList.create(["テスト動画1"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1"])
        no = list(range(1, len(video_id_list) + 1))

        # 正常系
        fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, uploaded_at_list,
                                      video_url_list, username_list)
        self.assertEqual(True, fvi_api._is_valid())

        # 異常系
        # VideoidList 指定が不正
        with self.assertRaises(TypeError):
            fvi_api = FetchedAPIVideoInfo(no, None, title_list, uploaded_at_list,
                                          video_url_list, username_list)
        # TitleList 指定が不正
        with self.assertRaises(TypeError):
            fvi_api = FetchedAPIVideoInfo(no, video_id_list, None, uploaded_at_list,
                                          video_url_list, username_list)
        # UploadedAtList 指定が不正
        with self.assertRaises(TypeError):
            fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, None,
                                          video_url_list, username_list)
        # VideoURLList 指定が不正
        with self.assertRaises(TypeError):
            fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, uploaded_at_list,
                                          None, username_list)
        # UsernameList 指定が不正
        with self.assertRaises(TypeError):
            fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, uploaded_at_list,
                                          video_url_list, None)
        # UsernameList 指定が不正
        with self.assertRaises(TypeError):
            fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, uploaded_at_list,
                                          video_url_list, None)
        # no 指定が不正
        with self.assertRaises(ValueError):
            fvi_api = FetchedAPIVideoInfo([], video_id_list, title_list, uploaded_at_list,
                                          video_url_list, username_list)
        # list の長さが同じでない
        title_list = TitleList.create(["テスト動画1", "テスト動画2"])
        with self.assertRaises(ValueError):
            fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, uploaded_at_list,
                                          video_url_list, username_list)

    def test_to_dict(self):
        """to_dict のテスト
        """
        title_list = TitleList.create(["テスト動画"])
        uploaded_at_list = UploadedAtList.create(["2022-05-06 00:00:01"])
        video_url_list = VideoURLList.create(["https://www.nicovideo.jp/watch/sm12345678"])
        video_id_list = VideoidList.create(video_url_list.video_id_list)
        username_list = UsernameList.create(["投稿者1"])
        no = list(range(1, len(video_id_list) + 1))

        fvi_api = FetchedAPIVideoInfo(no, video_id_list, title_list, uploaded_at_list,
                                      video_url_list, username_list)
        expect = {
            "no": no,
            "video_id_list": video_id_list,
            "title_list": title_list,
            "uploaded_at_list": uploaded_at_list,
            "video_url_list": video_url_list,
            "username_list": username_list,
        }
        actual = fvi_api.to_dict()
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
