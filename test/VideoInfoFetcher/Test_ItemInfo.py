# coding: utf-8
"""ItemInfo のテスト

ItemInfo の各種機能をテストする
"""
import sys
import unittest

from NNMM.VideoInfoFetcher.ItemInfo import ItemInfo


class TestItemInfo(unittest.TestCase):
    def _get_url_set(self) -> list[str]:
        """urlセットを返す
        """
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012?ref=pc_mypage_nicorepo",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def _make_iteminfo(self, error_target="", error_value="") -> list[dict]:
        """iteminfo を表す辞書のセットを返す
        """
        NUM = 5
        res = []
        for i in range(NUM):
            video_id = f"sm1000000{i}"
            title = f"動画タイトル_{i}"
            registered_at = f"2022-05-08 00:01:0{i}"
            video_url = "https://www.nicovideo.jp/watch/" + video_id

            r = {
                "video_id": video_id,
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
            self.assertEqual(item.get("video_id"), r.video_id)
            self.assertEqual(item.get("title"), r.title)
            self.assertEqual(item.get("registered_at"), r.registered_at)
            self.assertEqual(item.get("video_url"), r.video_url)

    def test_is_valid(self):
        """_is_valid のテスト
        """
        # 正常系
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)
        self.assertEqual(True, r._is_valid())

        # 異常系
        # video_id が文字列でない
        with self.assertRaises(TypeError):
            item = self._make_iteminfo("video_id", -1)[0]
            r = ItemInfo(**item)

        # video_id が空文字列
        with self.assertRaises(ValueError):
            item = self._make_iteminfo("video_id", "")[0]
            r = ItemInfo(**item)

        # video_id が不正な文字列
        with self.assertRaises(ValueError):
            item = self._make_iteminfo("video_id", "不正な動画ID")[0]
            r = ItemInfo(**item)

        # registered_at が不正な文字列
        with self.assertRaises(ValueError):
            item = self._make_iteminfo("registered_at", "不正な登録日時")[0]
            r = ItemInfo(**item)

        # video_url が不正な文字列
        with self.assertRaises(ValueError):
            item = self._make_iteminfo("video_url", "不正な動画URL")[0]
            r = ItemInfo(**item)

    def test_to_dict(self):
        """to_dict のテスト
        """
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)
        self.assertEqual(item, r.to_dict())

    def test_result(self):
        """result のテスト
        """
        item = self._make_iteminfo()[0]
        r = ItemInfo(**item)
        self.assertEqual(item, r.result)

        self.assertEqual(r.result, r.to_dict())


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
