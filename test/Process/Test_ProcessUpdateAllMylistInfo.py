# coding: utf-8
"""ProcessUpdateAllMylistInfo のテスト
"""
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, patch

from NNMM.Process import ProcessUpdateAllMylistInfo


class TestProcessUpdateAllMylistInfo(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def MakeMylistDB(self, num: int = 5) -> list[dict]:
        """mylist_db.Select()で取得されるマイリストデータセット
        """
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i+1}", "投稿動画", "uploaded", f"投稿者{i+1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i+1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", True if i % 2 == 0 else False] for i in range(num)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def MakeMylistInfoDB(self, num: int = 5) -> list[dict]:
        """mylist_info_db.Select()で取得される動画情報データセット
        """
        res = []
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded_at", "video_url", "mylist_url"]
        n = 0
        for k in range(num):
            table_rows = [[n, f"sm{k+1}000000{i+1}", f"動画タイトル{k+1}_{i+1}", f"投稿者{k+1}", "",
                           f"2022-02-01 0{k+1}:00:0{i+1}",
                           f"https://www.nicovideo.jp/watch/sm{k+1}000000{i+1}",
                           f"https://www.nicovideo.jp/user/1000000{k+1}/video"] for i in range(num)]
            n = n + 1

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return res

    def test_GetTargetMylist(self):
        """GetTargetMylistをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))

            puami = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfo()

            # 正常系
            expect = ["TargetMylist list"]
            r = MagicMock()
            r.Select = lambda: expect
            puami.mylist_db = r
            actual = puami.GetTargetMylist()
            self.assertEqual(expect, actual)

            # 異常系
            # 属性エラー
            del puami.mylist_db
            actual = puami.GetTargetMylist()
            self.assertEqual([], actual)

    def test_PUAMITDInit(self):
        """ProcessUpdateAllMylistInfoThreadDone の初期状態をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdateAllMylistInfo.logger.error"))

            puami_td = ProcessUpdateAllMylistInfo.ProcessUpdateAllMylistInfoThreadDone()
            self.assertEqual("All mylist", puami_td.L_KIND)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
