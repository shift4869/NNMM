import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack
from copy import deepcopy

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row import Status
from nnmm.process.value_objects.table_row_list import TableRowList
from nnmm.process.value_objects.textbox_upper import UpperTextbox
from nnmm.process.watched_all_mylist import WatchedAllMylist
from nnmm.util import Result


class TestWatchedAllMylist(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_db(self, num: int = 5) -> list[dict]:
        res = []
        col = [
            "id",
            "username",
            "mylistname",
            "type",
            "showname",
            "url",
            "created_at",
            "updated_at",
            "checked_at",
            "check_interval",
            "is_include_new",
        ]
        rows = [
            [
                i,
                f"投稿者{i + 1}",
                "投稿動画",
                "uploaded",
                f"投稿者{i + 1}さんの投稿動画",
                f"https://www.nicovideo.jp/user/1000000{i + 1}/video",
                "2022-02-01 02:30:00",
                "2022-02-01 02:30:00",
                "2022-02-01 02:30:00",
                "15分",
                i % 2 == 0,
            ]
            for i in range(num)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_table_data(self, mylist_url) -> list[str]:
        """self.window["-TABLE-"].Valuesで取得されるテーブル情報動画データセット"""
        NUM = 5
        res = []
        table_cols_name = [
            "No.",
            "動画ID",
            "動画名",
            "投稿者",
            "状況",
            "投稿日時",
            "登録日時",
            "動画URL",
            "所属マイリストURL",
            "マイリスト表示名",
            "マイリスト名",
            "作成日時",
        ]
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
                ]
                res.append(table_rows)
        return res

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mockli = self.enterContext(patch("nnmm.process.watched_all_mylist.logger.info"))
            mock_update_mylist_pane = self.enterContext(
                patch("nnmm.process.watched_all_mylist.ProcessBase.update_mylist_pane")
            )
            mock_update_table_pane = self.enterContext(
                patch("nnmm.process.watched_all_mylist.ProcessBase.update_table_pane")
            )
            mock_upper_textbox = self.enterContext(
                patch("nnmm.process.watched_all_mylist.ProcessBase.get_upper_textbox")
            )
            mock_all_table_row = self.enterContext(
                patch("nnmm.process.watched_all_mylist.ProcessBase.get_all_table_row")
            )

            instance = WatchedAllMylist(self.process_info)

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            def_data = self._make_table_data(mylist_url)

            def pre_run(is_mylist_url_empty):
                s_def_data = deepcopy(def_data)

                instance.mylist_db.reset_mock()
                instance.mylist_db.select.side_effect = self._make_mylist_db

                instance.mylist_info_db.reset_mock()
                instance.window.reset_mock()

                mock_upper_textbox.reset_mock()
                if is_mylist_url_empty:

                    def f():
                        return UpperTextbox.create("")

                    mock_upper_textbox.side_effect = f
                else:

                    def f():
                        return UpperTextbox.create(mylist_url)

                    mock_upper_textbox.side_effect = f

                mock_all_table_row.reset_mock()
                s_def_data = [[i + 1] + r[1:-1] for i, r in enumerate(s_def_data)]

                def f():
                    return TableRowList.create(s_def_data)

                mock_all_table_row.side_effect = f

                mock_update_mylist_pane.reset_mock()
                mock_update_table_pane.reset_mock()

            def post_run(is_mylist_url_empty):
                records = [m for m in m_list if m["is_include_new"]]
                mylist_url_list = [r["url"] for r in records]
                expect_mylist_db_calls = [call.select()]
                expect_mylist_db_calls.extend([
                    call.update_include_flag(s_mylist_url, False) for s_mylist_url in mylist_url_list
                ])
                self.assertEqual(expect_mylist_db_calls, instance.mylist_db.mock_calls)

                self.assertEqual(
                    [call.update_status_in_mylist(s_mylist_url, "") for s_mylist_url in mylist_url_list],
                    instance.mylist_info_db.mock_calls,
                )

                expect_window_calls = []
                s_mylist_url = mylist_url
                if is_mylist_url_empty:
                    s_mylist_url = ""
                    s_def_data = deepcopy(def_data)
                    s_def_data = [[i + 1] + r[1:-1] for i, r in enumerate(s_def_data)]
                    s_def_data = TableRowList.create(s_def_data)
                    for i, _ in enumerate(s_def_data):
                        s_def_data[i] = s_def_data[i].replace_from_typed_value(status=Status.watched)
                    expect_window_calls.extend([
                        call.__getitem__("-TABLE-"),
                        call.__getitem__().update(values=s_def_data.to_table_data()),
                    ])
                self.assertEqual(expect_window_calls, instance.window.mock_calls)

                mock_update_mylist_pane.assert_called_once_with()
                mock_update_table_pane.assert_called_once_with(s_mylist_url)

            Params = namedtuple("Params", ["is_mylist_url_empty", "result"])
            params_list = [
                Params(True, Result.success),
                Params(False, Result.success),
            ]
            for params in params_list:
                pre_run(params.is_mylist_url_empty)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.is_mylist_url_empty)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
