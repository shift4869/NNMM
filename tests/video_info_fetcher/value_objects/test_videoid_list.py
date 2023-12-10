"""VideoidList のテスト

VideoidList の各種機能をテストする
"""
import sys
import unittest
from dataclasses import FrozenInstanceError

from NNMM.video_info_fetcher.value_objects.videoid import Videoid
from NNMM.video_info_fetcher.value_objects.videoid_list import VideoidList


class TestVideoidList(unittest.TestCase):
    def _get_id_strs(self):
        NUM = 5
        base_id_str = "sm1000000{}"
        return [base_id_str.format(i) for i in range(1, NUM + 1)]

    def _get_video_ids(self):
        video_id_strs = self._get_id_strs()
        return [Videoid(r) for r in video_id_strs]

    def test_VideoidListInit(self):
        """VideoidList の初期化後の状態をテストする
        """
        base_id_str = "sm1000000{}"
        video_id_strs = self._get_id_strs()
        video_ids = self._get_video_ids()

        # 正常系
        # Videoid のリスト
        video_id_list = VideoidList(video_ids)
        self.assertEqual(video_ids, video_id_list._list)

        # 空リスト
        video_id_list = VideoidList([])
        self.assertEqual([], video_id_list._list)

        # 異常系
        # インスタンス変数を後から変えようとする -> frozen違反
        with self.assertRaises(FrozenInstanceError):
            video_id_list = VideoidList(video_ids)
            video_id_list._list = [Videoid(base_id_str.format(1))]

        # 引数がlistでない
        with self.assertRaises(TypeError):
            video_id_list = VideoidList(base_id_str.format(1))

        # 引数がlist[Videoid]でない
        with self.assertRaises(ValueError):
            video_id_list = VideoidList(video_id_strs)

        # 引数のlistの要素のうち、一部がVideoidでない
        num = len(video_ids)
        video_ids[num // 2] = base_id_str.format(num // 2)
        with self.assertRaises(ValueError):
            video_id_list = VideoidList(video_ids)

    def test_iter_len(self):
        """iter と len のテスト
        """
        video_ids = self._get_video_ids()
        video_id_list = VideoidList(video_ids)
        self.assertEqual(len(video_ids), len(video_id_list))
        for expect, actual in zip(video_ids, video_id_list):
            self.assertEqual(expect, actual)

    def test_create(self):
        """create のテスト
        """
        base_id_str = "sm1000000{}"
        video_id_strs = self._get_id_strs()
        video_ids = self._get_video_ids()

        # 正常系
        # 空リスト
        video_id_list = VideoidList.create([])
        self.assertEqual([], video_id_list._list)

        # 動画IDのリスト
        video_id_list = VideoidList.create(video_ids)
        self.assertEqual(video_ids, video_id_list._list)

        # 動画IDを表す文字列のリスト
        video_id_list = VideoidList.create(video_id_strs)
        self.assertEqual(video_ids, video_id_list._list)

        # 異常系
        # リストでない（str）
        with self.assertRaises(TypeError):
            video_id_list = VideoidList.create(base_id_str.format(1))

        # リストでない（int）
        with self.assertRaises(TypeError):
            video_id_list = VideoidList.create(-1)

        # リストだが要素が動画IDでも文字列でもない
        with self.assertRaises(ValueError):
            video_id_list = VideoidList.create([-1])

        # 文字列のリストだが動画IDを表していない
        # Videoid のエラーが送出される
        with self.assertRaises(ValueError):
            video_id_list = VideoidList.create(["不正な文字列"])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
