# coding: utf-8
"""ItemInfo のテスト

ItemInfo の各種機能をテストする
"""
import sys
import unittest

from NNMM.VideoInfoFetcher.ItemInfo import ItemInfo
from NNMM.VideoInfoFetcher.VideoURL import VideoURL


class TestItemInfo(unittest.TestCase):
    def _make_iteminfo(self, error_target="", error_value="") -> list[dict]:
        """iteminfo を表す辞書のセットを返す
        """
        NUM = 5
        res = []
        for i in range(NUM):
            video_id = f"sm1000000{i}"
            title = f"動画タイトル_{i}"
            registered_at = f"2022-05-08 00:01:0{i}"
            video_url = VideoURL.factory("https://www.nicovideo.jp/watch/" + video_id)

            r = {
                "title": title,
                "registered_at": registered_at,
                "_video_url": video_url,
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
            self.assertEqual(item.get("_video_url"), r._video_url)

    def test_is_valid(self):
        """_is_valid のテスト
        """
        # 正常系
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)
        self.assertEqual(True, r._is_valid())

        # 異常系
        # title が空リスト
        with self.assertRaises(TypeError):
            item = self._make_iteminfo("title", [])[0]
            r = ItemInfo(**item)

        # registered_at が不正な文字列
        with self.assertRaises(ValueError):
            item = self._make_iteminfo("registered_at", "不正な登録日時")[0]
            r = ItemInfo(**item)

    def test_to_dict(self):
        """to_dict のテスト
        """
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)

        item["video_url"] = item["_video_url"].video_url
        item["video_id"] = item["_video_url"].video_id
        del item["_video_url"]
        self.assertEqual(item, r.to_dict())

    def test_result(self):
        """result のテスト
        """
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)

        item["video_url"] = item["_video_url"].video_url
        item["video_id"] = item["_video_url"].video_id
        del item["_video_url"]
        self.assertEqual(item, r.result)

        self.assertEqual(r.result, r.to_dict())


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
