# coding: utf-8
"""ItemInfo のテスト

ItemInfo の各種機能をテストする
"""
import sys
import unittest

from NNMM.VideoInfoFetcher.ItemInfo import ItemInfo
from NNMM.VideoInfoFetcher.RegisteredAt import RegisteredAt
from NNMM.VideoInfoFetcher.Title import Title
from NNMM.VideoInfoFetcher.Videoid import Videoid
from NNMM.VideoInfoFetcher.VideoURL import VideoURL


class TestItemInfo(unittest.TestCase):
    def _make_iteminfo(self, error_target="", error_value="") -> list[dict]:
        """iteminfo を表す辞書のセットを返す
        """
        NUM = 5
        res = []
        for i in range(NUM):
            video_id = Videoid(f"sm1000000{i}")
            title = Title(f"動画タイトル_{i}")
            registered_at = RegisteredAt(f"2022-05-08 00:01:0{i}")
            video_url = VideoURL.create("https://www.nicovideo.jp/watch/" + video_id.id)

            r = {
                # "video_id": video_id,
                "title": title,
                "registered_at": registered_at,
                "video_url": video_url,
            }

            if error_target != "":
                r[error_target] = error_value

            res.append(r)
        return res

    def test_ItemInfoInit(self):
        """ItemInfo の初期化後の状態をテストする
        """
        # 正常系
        items = self._make_iteminfo()
        for item in items:
            r = ItemInfo(**item)
            self.assertEqual(item.get("title"), r.title)
            self.assertEqual(item.get("registered_at"), r.registered_at)
            self.assertEqual(item.get("video_url"), r.video_url)
            self.assertEqual(item.get("video_url").video_id, r.video_id)

    def test_is_valid(self):
        """_is_valid のテスト
        """
        # 正常系
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)
        self.assertEqual(True, r._is_valid())

    def test_to_dict(self):
        """to_dict のテスト
        """
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)

        item["video_id"] = item["video_url"].video_id
        self.assertEqual(item, r.to_dict())

    def test_result(self):
        """result のテスト
        """
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)

        item["video_id"] = item["video_url"].video_id
        self.assertEqual(item, r.result)

        self.assertEqual(r.result, r.to_dict())


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
