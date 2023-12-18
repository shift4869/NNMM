import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack
from copy import deepcopy

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.process.value_objects.table_row import Status
from NNMM.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from NNMM.process.value_objects.table_row_list import TableRowList
from NNMM.process.value_objects.textbox_upper import UpperTextbox
from NNMM.process.watched import Watched
from NNMM.util import Result


class TestWatched(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_db(self, num: int = 5) -> list[dict]:
        """mylist_db.select()で取得されるマイリストデータセット
        """
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i + 1}", "投稿動画", "uploaded", f"投稿者{i + 1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i + 1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", False] for i in range(num)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_table_data(self, mylist_url) -> list[str]:
        """self.window["-TABLE-"].Valuesで取得されるテーブル情報動画データセット
        """
        NUM = 5
        res = []
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名", "作成日時"]
        for k in range(NUM):
            for i in range(NUM):
                # MylistInfo + showname系
                number = i + (k * NUM)
                video_id = f"sm{k + 1}000000{i + 1}"
                title = f"動画タイトル{k + 1}_{i + 1}"
                username = f"投稿者{k + 1}"
                status = "未視聴"
                uploaded_at = f"2022-02-02 0{k + 1}:00:0{i + 1}"
                registered_at = f"2022-02-03 0{k + 1}:00:0{i + 1}"
                video_url = f"https://www.nicovideo.jp/watch/sm{k + 1}000000{i + 1}"
                created_at = f"2022-02-01 0{k + 1}:00:0{i + 1}"
                showname = f"showname_{mylist_url}"
                mylistname = f"mylistname_{mylist_url}"
                table_rows = [
                    number,
                    video_id,
                    title,
                    username,
                    status,
                    uploaded_at,
                    registered_at,
                    video_url,
                    mylist_url,
                    created_at,
                ]
                res.append(table_rows)
        return res

    def _get_mylist_info_from_mylist_url(self, table_row_list, mylist_url) -> list[dict]:
        for table_row in table_row_list:
            if table_row.mylist_url.non_query_url == mylist_url:
                return [table_row]
        return []

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.watched.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.watched.logger.error"))
            mock_selected_table_row_index_list = stack.enter_context(patch("NNMM.process.watched.ProcessBase.get_selected_table_row_index_list"))
            mock_all_table_row = stack.enter_context(patch("NNMM.process.watched.ProcessBase.get_all_table_row"))
            mock_include_new_video = stack.enter_context(patch("NNMM.process.watched.is_mylist_include_new_video"))
            mock_upper_textbox = stack.enter_context(patch("NNMM.process.watched.ProcessBase.get_upper_textbox"))
            mock_update_table_pane = stack.enter_context(patch("NNMM.process.watched.ProcessBase.update_table_pane"))
            mock_update_mylist_pane = stack.enter_context(patch("NNMM.process.watched.ProcessBase.update_mylist_pane"))

            instance = Watched(self.process_info)

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            def_data = self._make_table_data(mylist_url)
            def pre_run(s_value, s_status, is_include_new):
                mock_selected_table_row_index_list.reset_mock()
                if s_value == -1:
                    mock_selected_table_row_index_list.side_effect = lambda: []
                else:
                    def f(): return SelectedTableRowIndexList.create([s_value])
                    mock_selected_table_row_index_list.side_effect = f

                s_def_data = deepcopy(def_data)
                s_def_data = [[i + 1] + r[1:-1] for i, r in enumerate(s_def_data)]
                s_def_data = TableRowList.create(s_def_data)
                mock_all_table_row.reset_mock()
                mock_all_table_row.side_effect = lambda: s_def_data

                instance.mylist_db.reset_mock()
                instance.mylist_info_db.reset_mock()
                def f(mylist_url): return self._get_mylist_info_from_mylist_url(s_def_data, mylist_url)
                instance.mylist_info_db.select_from_mylist_url.side_effect = f
                def f(video_id, mylist_url, status): return s_status
                instance.mylist_info_db.update_status.side_effect = f

                mock_include_new_video.reset_mock()
                mock_include_new_video.side_effect = lambda table_list: is_include_new

                mock_upper_textbox.reset_mock()
                def f(): return UpperTextbox.create(mylist_url)
                mock_upper_textbox.side_effect = f

                instance.window.reset_mock()
                mock_update_table_pane.reset_mock()
                mock_update_mylist_pane.reset_mock()

            def post_run(s_value, s_status, is_include_new):
                self.assertEqual([
                    call(),
                ], mock_selected_table_row_index_list.mock_calls)
                if s_value == -1:
                    mock_all_table_row.assert_not_called()
                    instance.mylist_info_db.assert_not_called()
                    instance.mylist_db.assert_not_called()
                    mock_include_new_video.assert_not_called()
                    mock_upper_textbox.assert_not_called()
                    mock_update_table_pane.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    return

                s_def_data = deepcopy(def_data)
                s_def_data = [[i + 1] + r[1:-1] for i, r in enumerate(s_def_data)]
                s_def_data = TableRowList.create(s_def_data)
                selected = s_def_data[s_value]
                s_video_id = selected.video_id.id
                s_mylist_url = selected.mylist_url.non_query_url
                self.assertEqual([
                    call.update_status(s_video_id, s_mylist_url, ""),
                    call.select_from_mylist_url(s_mylist_url),
                ], instance.mylist_info_db.mock_calls)

                updated_row = selected.replace_from_typed_value(status=Status.watched)
                s_def_data[s_value] = updated_row

                m_list = self._get_mylist_info_from_mylist_url(s_def_data, s_mylist_url)
                m_list = [list(m.values()) for m in m_list]
                self.assertEqual([
                    call(m_list),
                ], mock_include_new_video.mock_calls)

                if not is_include_new:
                    self.assertEqual([
                        call.update_include_flag(s_mylist_url, False)
                    ], instance.mylist_db.mock_calls)
                else:
                    instance.mylist_db.assert_not_called()

                self.assertEqual([
                    call.__getitem__("-TABLE-"),
                    call.__getitem__().update(values=s_def_data.to_table_data()),
                    call.__getitem__("-TABLE-"),
                    call.__getitem__().update(select_rows=[s_value])
                ], instance.window.mock_calls)

                self.assertEqual([
                    call()
                ], mock_upper_textbox.mock_calls)

                mock_update_table_pane.assert_called_once_with(s_mylist_url)
                mock_update_mylist_pane.assert_called_once_with()

            Params = namedtuple("Params", ["s_value", "s_status", "is_include_new", "result"])
            params_list = [
                Params(0, 0, False, Result.success),
                Params(0, 0, True, Result.success),
                Params(0, 1, False, Result.success),
                Params(0, 1, True, Result.success),
                Params(-1, 0, False, Result.failed),
            ]
            for params in params_list:
                pre_run(*params[:-1])
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(*params[:-1])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
