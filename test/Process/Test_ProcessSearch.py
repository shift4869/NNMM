# coding: utf-8
"""ProcessSearch のテスト
"""
import re
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch

from NNMM.Process import ProcessSearch


class TestProcessSearch(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def MakeMylistShownameList(self):
        """表示マイリストデータセット
        """
        NUM = 5
        res = [f"投稿者{i+1}" for i in range(NUM)]
        return res

    def MakeMylistDB(self):
        """mylist_db.select()で取得されるマイリストデータセット
        """
        NUM = 5
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i+1}", "投稿動画", "uploaded", f"投稿者{i+1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i+1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", True if i % 2 == 0 else False] for i in range(NUM)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def MakeMylistInfoDB(self, mylist_url):
        """mylist_info_db.select_from_mylist_url(mylist_url)で取得されるマイリストデータセット
        """
        NUM = 5
        res = []

        m = -1
        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        if re.search(pattern, mylist_url):
            m = int(re.search(pattern, mylist_url)[1])
        if m == -1:
            return []

        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded", "video_url", "mylist_url"]
        table_rows = [[i, f"sm{m}000000{i+1}", f"動画タイトル{m}_{i+1}", f"投稿者{m}", "",
                       "2022-02-01 02:30:00",
                       f"https://www.nicovideo.jp/watch/sm{m}000000{i+1}",
                       f"https://www.nicovideo.jp/user/1000000{m}/video"] for i in range(NUM)]

        for rows in table_rows:
            d = {}
            for r, c in zip(rows, table_cols):
                d[c] = r
            res.append(d)
        return res

    def MakeTableRecords(self, mylist_url):
        """表示中の動画テーブルから取得されるレコードセット
        """
        NUM = 5
        m = -1
        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        if re.search(pattern, mylist_url):
            m = int(re.search(pattern, mylist_url)[1])
        if m == -1:
            return []

        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL"]
        records = [[i, f"sm{m}000000{i+1}", f"動画タイトル{m}_{i+1}", f"投稿者{m}", "未視聴", "2022-01-28 22:00:00",
                    f"https://www.nicovideo.jp/watch/sm{m}000000{i+1}", mylist_url] for i in range(NUM)]
        return records

    def test_PMSrun(self):
        """ProcessMylistSearchのrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.error"))
            mocksgpgt = stack.enter_context(patch("NNMM.Process.ProcessSearch.popup_get_text"))

            pms = ProcessSearch.ProcessMylistSearch()

            # 正常系
            def ReturnMW():
                def ReturnWindowList():
                    r_wl = MagicMock()
                    r_wl.get_indexes.return_value = [1]
                    r_wl.Values = self.MakeMylistShownameList()
                    return r_wl

                expect_window_dict = {
                    "-LIST-": ReturnWindowList(),
                    "-INPUT2-": MagicMock()
                }

                r = MagicMock()
                mockwindow = MagicMock()
                mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
                mockwindow.__iter__.side_effect = expect_window_dict.__iter__
                mockwindow.__contains__.side_effect = expect_window_dict.__contains__
                type(r).window = mockwindow

                r.mylist_db.select.return_value = self.MakeMylistDB()
                return r

            mockmw = ReturnMW()
            mocksgpgt.return_value = "投稿者1"
            actual = pms.run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                index = 1
                pattern = mocksgpgt.return_value
                NEW_MARK = "*:"
                m_list = self.MakeMylistDB()
                include_new_index_list = []
                match_index_list = []
                for i, m in enumerate(m_list):
                    if m["is_include_new"]:
                        m["showname"] = NEW_MARK + m["showname"]
                        include_new_index_list.append(i)
                    if re.search(pattern, m["showname"]):
                        match_index_list.append(i)
                        index = i  # 更新後にスクロールするインデックスを更新
                list_data = [m["showname"] for m in m_list]

                mc = mockmw.window["-LIST-"].mock_calls
                self.assertEqual(3 + len(include_new_index_list) + len(match_index_list) + 2, len(mc))
                self.assertEqual(call.get_indexes(), mc[0])
                self.assertEqual(call.get_indexes(), mc[1])
                self.assertEqual(call.update(values=list_data), mc[2])
                for c, i in enumerate(include_new_index_list):
                    self.assertEqual(call.Widget.itemconfig(i, fg="black", bg="light pink"), mc[3 + c])
                for c, i in enumerate(match_index_list):
                    self.assertEqual(call.Widget.itemconfig(i, fg="black", bg="light goldenrod"), mc[3 + len(include_new_index_list) + c])
                self.assertEqual(call.Widget.see(index), mc[-2])
                self.assertEqual(call.update(set_to_index=index), mc[-1])
                mockmw.window["-LIST-"].reset_mock()

                mc = mockmw.window["-INPUT2-"].mock_calls
                self.assertEqual(1, len(mc))
                if len(match_index_list) > 0:
                    self.assertEqual(call.update(value=f"{len(match_index_list)}件ヒット！"), mc[0])
                else:
                    self.assertEqual(call.update(value="該当なし"), mc[0])
                mockmw.window["-INPUT2-"].reset_mock()

                mocksgpgt.assert_called_once_with("マイリスト名検索（正規表現可）")
                mocksgpgt.reset_mock()

                mc = mockmw.mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual(call.mylist_db.select(), mc[0])
                mockmw.reset_mock()

            assertMockCall()

            # 複数ヒット
            mockmw = ReturnMW()
            mocksgpgt.return_value = "投稿者"
            actual = pms.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 1件もヒットしなかった
            mockmw = ReturnMW()
            mocksgpgt.return_value = "ヒットしない検索条件"
            actual = pms.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 検索条件が空白
            mockmw = ReturnMW()
            mocksgpgt.return_value = ""
            actual = pms.run(mockmw)
            self.assertEqual(1, actual)

            # 異常系
            # 引数エラー
            mockmw = ReturnMW()
            del mockmw.window
            del type(mockmw).window
            actual = pms.run(mockmw)
            self.assertEqual(-1, actual)

    def test_PMSFVrun(self):
        """ProcessMylistSearchFromVideoのrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.error"))
            mocksgpgt = stack.enter_context(patch("NNMM.Process.ProcessSearch.popup_get_text"))

            pmsfv = ProcessSearch.ProcessMylistSearchFromVideo()

            # 正常系
            def ReturnMW():
                def ReturnWindowList():
                    r_wl = MagicMock()
                    r_wl.get_indexes.return_value = [1]
                    r_wl.Values = self.MakeMylistShownameList()
                    return r_wl

                expect_window_dict = {
                    "-LIST-": ReturnWindowList(),
                    "-INPUT2-": MagicMock()
                }

                r = MagicMock()
                mockwindow = MagicMock()
                mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
                mockwindow.__iter__.side_effect = expect_window_dict.__iter__
                mockwindow.__contains__.side_effect = expect_window_dict.__contains__
                type(r).window = mockwindow

                r.mylist_db.select.return_value = self.MakeMylistDB()
                r.mylist_info_db.select_from_mylist_url = self.MakeMylistInfoDB
                return r

            mockmw = ReturnMW()
            mocksgpgt.return_value = "動画タイトル1_1"
            actual = pmsfv.run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                index = 1
                pattern = mocksgpgt.return_value
                NEW_MARK = "*:"
                m_list = self.MakeMylistDB()
                include_new_index_list = []
                match_index_list = []
                for i, m in enumerate(m_list):
                    if m["is_include_new"]:
                        m["showname"] = NEW_MARK + m["showname"]
                        include_new_index_list.append(i)
                    mylist_url = m["url"]
                    records = self.MakeMylistInfoDB(mylist_url)
                    for r in records:
                        if re.search(pattern, r["title"]):
                            match_index_list.append(i)
                            index = i  # 更新後にスクロールするインデックスを更新
                list_data = [m["showname"] for m in m_list]

                mc = mockmw.window["-LIST-"].mock_calls
                self.assertEqual(3 + len(include_new_index_list) + len(match_index_list) + 2, len(mc))
                self.assertEqual(call.get_indexes(), mc[0])
                self.assertEqual(call.get_indexes(), mc[1])
                self.assertEqual(call.update(values=list_data), mc[2])
                for c, i in enumerate(include_new_index_list):
                    self.assertEqual(call.Widget.itemconfig(i, fg="black", bg="light pink"), mc[3 + c])
                for c, i in enumerate(match_index_list):
                    self.assertEqual(call.Widget.itemconfig(i, fg="black", bg="light goldenrod"), mc[3 + len(include_new_index_list) + c])
                self.assertEqual(call.Widget.see(index), mc[-2])
                self.assertEqual(call.update(set_to_index=index), mc[-1])
                mockmw.window["-LIST-"].reset_mock()

                mc = mockmw.window["-INPUT2-"].mock_calls
                self.assertEqual(1, len(mc))
                if len(match_index_list) > 0:
                    self.assertEqual(call.update(value=f"{len(match_index_list)}件ヒット！"), mc[0])
                else:
                    self.assertEqual(call.update(value="該当なし"), mc[0])
                mockmw.window["-INPUT2-"].reset_mock()

                mocksgpgt.assert_called_once_with("動画名検索（正規表現可）")
                mocksgpgt.reset_mock()

                mc = mockmw.mock_calls
                self.assertEqual(1, len(mc))
                self.assertEqual(call.mylist_db.select(), mc[0])
                mockmw.reset_mock()

            assertMockCall()

            # 複数ヒット
            mockmw = ReturnMW()
            mocksgpgt.return_value = "動画タイトル1_"
            actual = pmsfv.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 1件もヒットしなかった
            mockmw = ReturnMW()
            mocksgpgt.return_value = "ヒットしない検索条件"
            actual = pmsfv.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 検索条件が空白
            mockmw = ReturnMW()
            mocksgpgt.return_value = ""
            actual = pmsfv.run(mockmw)
            self.assertEqual(1, actual)

            # 異常系
            # 引数エラー
            mockmw = ReturnMW()
            del mockmw.window
            del type(mockmw).window
            actual = pmsfv.run(mockmw)
            self.assertEqual(-1, actual)

    def test_PVSrun(self):
        """ProcessVideoSearchのrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.error"))
            mocksgpgt = stack.enter_context(patch("NNMM.Process.ProcessSearch.popup_get_text"))

            pvs = ProcessSearch.ProcessVideoSearch()

            # 正常系
            mylist_url_s = self.MakeMylistDB()[0]["url"]
            selected_num_s = [0]

            def ReturnMW():
                r_wt = MagicMock()
                r_wt.Values = self.MakeTableRecords(mylist_url_s)
                expect_window_dict = {
                    "-TABLE-": r_wt,
                    "-INPUT2-": MagicMock()
                }

                expect_values_dict = {
                    "-TABLE-": selected_num_s
                }

                r = MagicMock()
                mockwindow = MagicMock()
                mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
                mockwindow.__iter__.side_effect = expect_window_dict.__iter__
                mockwindow.__contains__.side_effect = expect_window_dict.__contains__
                type(r).window = mockwindow
                mockvalue = MagicMock()
                mockvalue.__getitem__.side_effect = expect_values_dict.__getitem__
                mockvalue.__iter__.side_effect = expect_values_dict.__iter__
                mockvalue.__contains__.side_effect = expect_values_dict.__contains__
                type(r).values = mockvalue

                return r

            mockmw = ReturnMW()
            mocksgpgt.return_value = "動画タイトル1_1"
            actual = pvs.run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                index = min([int(v) for v in selected_num_s])
                pattern = mocksgpgt.return_value
                records = self.MakeTableRecords(mylist_url_s)

                match_index_list = []
                for i, r in enumerate(records):
                    if re.search(pattern, r[2]):
                        match_index_list.append(i)
                        index = i  # 更新後にスクロールするインデックスを更新

                mc = mockmw.window["-TABLE-"].mock_calls
                self.assertEqual(3, len(mc))
                self.assertEqual(call.update(row_colors=[(i, "black", "light goldenrod") for i in match_index_list]), mc[0])
                self.assertEqual(call.Widget.see(index + 1), mc[1])
                if match_index_list:
                    self.assertEqual(call.update(select_rows=match_index_list), mc[2])
                else:
                    self.assertEqual(call.update(select_rows=[index]), mc[2])
                mockmw.window["-TABLE-"].reset_mock()

                mc = mockmw.window["-INPUT2-"].mock_calls
                self.assertEqual(1, len(mc))
                if len(match_index_list) > 0:
                    self.assertEqual(call.update(value=f"{len(match_index_list)}件ヒット！"), mc[0])
                else:
                    self.assertEqual(call.update(value="該当なし"), mc[0])
                mockmw.window["-INPUT2-"].reset_mock()

                mc = mockmw.values.mock_calls
                self.assertEqual(2, len(mc))
                self.assertEqual(call.__getitem__("-TABLE-"), mc[0])
                self.assertEqual(call.__getitem__("-TABLE-"), mc[1])
                mockmw.values.reset_mock()

                mocksgpgt.assert_called_once_with("動画名検索（正規表現可）")
                mocksgpgt.reset_mock()

                mockmw.reset_mock()

            assertMockCall()

            # 複数ヒット
            mockmw = ReturnMW()
            mocksgpgt.return_value = "動画タイトル1_"
            actual = pvs.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 1件もヒットしなかった
            mockmw = ReturnMW()
            mocksgpgt.return_value = "ヒットしない検索条件"
            actual = pvs.run(mockmw)
            self.assertEqual(0, actual)
            assertMockCall()

            # 検索条件が空白
            mockmw = ReturnMW()
            mocksgpgt.return_value = ""
            actual = pvs.run(mockmw)
            self.assertEqual(1, actual)

            # 異常系
            # 引数エラー
            mockmw = ReturnMW()
            del mockmw.window
            del type(mockmw).window
            actual = pvs.run(mockmw)
            self.assertEqual(-1, actual)

    def test_PMSCrun(self):
        """ProcessMylistSearchClearのrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.error"))
            mockums = stack.enter_context(patch("NNMM.Process.ProcessSearch.update_mylist_pane"))

            pmsc = ProcessSearch.ProcessMylistSearchClear()

            # 正常系
            mockmw = MagicMock()
            actual = pmsc.run(mockmw)
            self.assertEqual(0, actual)
            mockums.assert_called_once_with(mockmw.window, mockmw.mylist_db)
            mockums.reset_mock()

            # 異常系
            # 引数エラー
            mockmw = MagicMock()
            del mockmw.window
            actual = pmsc.run(mockmw)
            self.assertEqual(-1, actual)

    def test_PVSCrun(self):
        """ProcessVideoSearchClearのrunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessSearch.logger.error"))
            mockuts = stack.enter_context(patch("NNMM.Process.ProcessSearch.update_table_pane"))

            pvsc = ProcessSearch.ProcessVideoSearchClear()

            # 正常系
            # mylist_urlが右上のテキストボックスに存在するとき
            mylist_url_s = self.MakeMylistDB()[0]["url"]

            def ReturnMW():
                r_wt = MagicMock()
                r_wt.get = lambda: mylist_url_s
                expect_window_dict = {
                    "-INPUT1-": r_wt
                }

                r = MagicMock()
                mockwindow = MagicMock()
                mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
                mockwindow.__iter__.side_effect = expect_window_dict.__iter__
                mockwindow.__contains__.side_effect = expect_window_dict.__contains__
                type(r).window = mockwindow
                return r

            mockmw = ReturnMW()
            actual = pvsc.run(mockmw)
            self.assertEqual(0, actual)
            mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db, mylist_url_s)
            mockuts.reset_mock()

            # 右上のテキストボックス空のとき
            mylist_url_s = ""
            mockmw = ReturnMW()
            actual = pvsc.run(mockmw)
            self.assertEqual(0, actual)
            mockuts.assert_called_once_with(mockmw.window, mockmw.mylist_db, mockmw.mylist_info_db, mylist_url_s)
            mockuts.reset_mock()

            # 異常系
            # 引数エラー
            mockmw = MagicMock()
            del mockmw.window
            actual = pvsc.run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
