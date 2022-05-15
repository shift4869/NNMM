# coding: utf-8
"""ProcessUpdatePartialMylistInfo のテスト
"""
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from mock import MagicMock, patch, call

import freezegun

from NNMM.GuiFunction import IntervalTranslation
from NNMM.Process import ProcessUpdatePartialMylistInfo


class TestProcessUpdatePartialMylistInfo(unittest.TestCase):

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
        checked_at = ["2022-02-01 02:30:00", "2022-02-01 02:15:00"]  # [更新対象でない時刻, 更新対象となる時刻]
        rows = [[i, f"投稿者{i+1}", "投稿動画", "uploaded", f"投稿者{i+1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i+1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", checked_at[i % 2],
                 "15分", False] for i in range(num)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def MakeMylistInfoDB(self, mylist_url, num: int = 5) -> list[dict]:
        """mylist_info_db.SelectFromMylistURL()で取得される動画情報データセット
        """
        res = []
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded_at", "video_url", "mylist_url"]
        n = 0
        for k in range(num):
            table_rows = [[n + i, f"sm{k+1}000000{i+1}", f"動画タイトル{k+1}_{i+1}", f"投稿者{k+1}",
                           "未視聴" if i % 2 == 0 else "",
                           f"2022-02-01 0{k+1}:00:0{i+1}",
                           f"https://www.nicovideo.jp/watch/sm{k+1}000000{i+1}",
                           f"https://www.nicovideo.jp/user/1000000{k+1}/video"] for i in range(num)]
            n = n + 1 + num

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return [r for r in res if r["mylist_url"] == mylist_url]

    def test_PUPMIInit(self):
        """ProcessUpdatePartialMylistInfo の初期状態をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdatePartialMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdatePartialMylistInfo.logger.error"))

            pupmi = ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfo()

            self.assertEqual("Partial mylist", pupmi.L_KIND)
            self.assertEqual("-PARTIAL_UPDATE_THREAD_DONE-", pupmi.E_DONE)

    def test_PUPMIGetTargetMylist(self):
        """GetTargetMylist をテストする
        """
        with ExitStack() as stack:
            stack.enter_context(freezegun.freeze_time("2022-02-01 02:30:00"))
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdatePartialMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdatePartialMylistInfo.logger.error"))

            pupmi = ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfo()

            # 正常系
            m_list = self.MakeMylistDB()
            mylist_url = m_list[0].get("url")

            mockmw = MagicMock()
            mockmdb = MagicMock()
            mockmdb.Select.side_effect = lambda: m_list
            mockmw.mylist_db = mockmdb

            pupmi.mylist_db = mockmw.mylist_db
            actual = pupmi.GetTargetMylist()

            def ReturnExpect():
                result = []

                src_df = "%Y/%m/%d %H:%M"
                dst_df = "%Y-%m-%d %H:%M:%S"
                now_dst = datetime.now()
                try:
                    for m in m_list:
                        checked_dst = datetime.strptime(m["checked_at"], dst_df)
                        interval_str = str(m["check_interval"])
                        dt = IntervalTranslation(interval_str) - 1
                        if dt < -1:
                            continue
                        predict_dst = checked_dst + timedelta(minutes=dt)
                        if predict_dst < now_dst:
                            result.append(m)
                except KeyError:
                    return []
                return result

            expect = ReturnExpect()
            self.assertEqual(expect, actual)

            # 実行後呼び出し確認
            mc = mockmw.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.mylist_db.Select(), mc[0])
            mockmw.reset_mock()

            # インターバル文字列不正のレコードが含まれている
            m_list[1]["check_interval"] = "不正なインターバル文字列"
            actual = pupmi.GetTargetMylist()
            expect = ReturnExpect()
            self.assertEqual(expect, actual)

            # 異常系
            # 日時取得エラー
            m_list[0]["checked_at"] = "不正な日時"
            actual = pupmi.GetTargetMylist()
            self.assertEqual([], actual)

            # 引数エラー
            del pupmi.mylist_db
            actual = pupmi.GetTargetMylist()
            self.assertEqual([], actual)

    def test_PUPMITDInit(self):
        """ProcessUpdatePartialMylistInfoThreadDone の初期状態をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessUpdatePartialMylistInfo.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessUpdatePartialMylistInfo.logger.error"))

            pupmitd = ProcessUpdatePartialMylistInfo.ProcessUpdatePartialMylistInfoThreadDone()
            self.assertEqual("Partial mylist", pupmitd.L_KIND)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
