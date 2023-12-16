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
                status = ""
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
                    showname,
                    mylistname,
                ]
                res.append(table_rows)
        return res

    def _convert_table_data_to_dict(self, table_data: list[list[str]]) -> list[dict]:
        table_cols_name = [
            "id",
            "video_id",
            "title",
            "username",
            "status",
            "uploaded_at",
            "registered_at",
            "video_url",
            "mylist_url",
            "created_at",
            "showname",
            "mylistname",
        ]
        res = []
        for table_rows in table_data:
            res.append(dict(zip(table_cols_name, table_rows)))
        return res

    def _get_mylist_info_from_mylist_url(self, table_data, mylist_url) -> list[dict]:
        table_dict_list = self._convert_table_data_to_dict(table_data)
        for table_dict in table_dict_list:
            if table_dict.get("mylist_url") == mylist_url:
                return [table_dict]
        return []

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.watched.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.watched.logger.error"))
            mock_update_table_pane = stack.enter_context(patch("NNMM.process.watched.update_table_pane"))
            mock_update_mylist_pane = stack.enter_context(patch("NNMM.process.watched.update_mylist_pane"))
            mock_include_new_video = stack.enter_context(patch("NNMM.process.watched.is_mylist_include_new_video"))
            mock_window = MagicMock()

            instance = Watched(self.process_info)

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            def_data = self._make_table_data(mylist_url)
            def pre_run(s_value, s_status, is_include_new):
                s_def_data = deepcopy(def_data)
                mock_window.reset_mock()
                instance.window.reset_mock()
                mock_window.Values = s_def_data
                instance.window.__getitem__.side_effect = lambda key: mock_window

                instance.values.reset_mock()
                if s_value == -1:
                    instance.values.__getitem__.side_effect = lambda key: []
                else:
                    values_dict = {
                        "-TABLE-": [s_value],
                        "-INPUT1-": s_def_data[0][8],
                    }
                    instance.values.__getitem__.side_effect = lambda key: values_dict[key]

                instance.mylist_db.reset_mock()
                instance.mylist_info_db.reset_mock()
                def f(mylist_url): return self._get_mylist_info_from_mylist_url(s_def_data, mylist_url)
                instance.mylist_info_db.select_from_mylist_url.side_effect = f
                def f(video_id, mylist_url, status): return s_status
                instance.mylist_info_db.update_status.side_effect = f

                mock_include_new_video.reset_mock()
                mock_include_new_video.side_effect = lambda table_list: is_include_new

                mock_update_table_pane.reset_mock()
                mock_update_mylist_pane.reset_mock()

            def post_run(s_value, s_status, is_include_new):
                if s_value == -1:
                    self.assertEqual([
                        call.__getitem__("-TABLE-"),
                    ], instance.values.mock_calls)
                    self.assertEqual([
                        call.__getitem__("-TABLE-"),
                    ], instance.window.mock_calls)
                    instance.mylist_info_db.assert_not_called()
                    instance.mylist_db.assert_not_called()
                    mock_include_new_video.assert_not_called()
                    mock_update_table_pane.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    return
                else:
                    self.assertEqual([
                        call.__getitem__("-TABLE-"),
                        call.__getitem__("-TABLE-"),
                        call.__getitem__("-TABLE-"),
                        call.__getitem__("-INPUT1-")
                    ], instance.values.mock_calls)

                selected = def_data[s_value]
                s_mylist_url = selected[8]
                self.assertEqual([
                    call.update_status(selected[1], s_mylist_url, ""),
                    call.select_from_mylist_url(s_mylist_url),
                ], instance.mylist_info_db.mock_calls)

                s_def_data = deepcopy(def_data)
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
                    call.__getitem__("-TABLE-"),
                    call.__getitem__("-TABLE-")
                ], instance.window.mock_calls)

                mock_update_table_pane.assert_called_once_with(
                    instance.window, instance.mylist_db, instance.mylist_info_db, s_mylist_url
                )

                mock_update_mylist_pane.assert_called_once_with(
                    instance.window, instance.mylist_db
                )

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
