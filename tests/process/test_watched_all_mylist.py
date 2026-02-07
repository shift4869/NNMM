import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row_list import TableRowList
from nnmm.process.watched_all_mylist import WatchedAllMylist
from nnmm.util import Result


class TestWatchedAllMylist(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.watched_all_mylist.logger.info"))
        self.enterContext(patch("nnmm.process.watched_all_mylist.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> WatchedAllMylist:
        instance = WatchedAllMylist(self.process_info)
        return instance

    def _make_mylist_db(self) -> list[dict]:
        NUM = 5
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
                "2026-02-07 02:30:00",
                "2026-02-07 02:30:00",
                "2026-02-07 02:30:00",
                "15分",
                True,
            ]
            for i in range(NUM)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_table_row_list(self, mylist_url) -> list[list[str]]:
        """テーブル情報動画データセット"""
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
        ]
        for k in range(NUM):
            for i in range(NUM):
                # MylistInfo + showname系
                number = i + (k * NUM) + 1
                video_id = f"sm{k + 1}000000{i + 1}"
                title = f"動画タイトル{k + 1}_{i + 1}"
                username = f"投稿者{k + 1}"
                status = "未視聴"
                uploaded_at = f"2026-02-02 0{k + 1}:00:0{i + 1}"
                registered_at = f"2026-02-03 0{k + 1}:00:0{i + 1}"
                video_url = f"https://www.nicovideo.jp/watch/sm{k + 1}000000{i + 1}"
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
                ]
                res.append(table_rows)
        return res

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)

    def test_component(self):
        instance = self._get_instance()
        actual = instance.create_component()
        self.assertIsNone(actual)

    def test_callback(self) -> Result:
        Params = namedtuple(
            "Params",
            [
                "kind_get_upper_textbox",
                "result",
            ],
        )

        def pre_run(params: Params) -> WatchedAllMylist:
            instance = self._get_instance()
            instance.get_upper_textbox = MagicMock()
            instance.update_mylist_pane = MagicMock()
            instance.update_table_pane = MagicMock()
            instance.get_all_table_row = MagicMock()
            instance.set_all_table_row = MagicMock()
            instance.mylist_db = MagicMock()
            instance.mylist_info_db = MagicMock()

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            if params.kind_get_upper_textbox == "valid":
                instance.get_upper_textbox.return_value.to_str.return_value = mylist_url
            else:  # "empty"
                instance.get_upper_textbox.return_value.to_str.return_value = ""
                r_list = self._make_table_row_list(mylist_url)
                instance.get_all_table_row.return_value = TableRowList.create(r_list)

            instance.mylist_db.select.return_value = m_list

            return instance

        def post_run(actual: Result, instance: WatchedAllMylist, params: Params) -> None:
            self.assertEqual(params.result, actual)
            instance.get_upper_textbox.return_value.to_str.assert_called_once_with()
            self.assertEqual(
                [
                    call.select(),
                    call.update_include_flag("https://www.nicovideo.jp/user/10000001/video", False),
                    call.update_include_flag("https://www.nicovideo.jp/user/10000002/video", False),
                    call.update_include_flag("https://www.nicovideo.jp/user/10000003/video", False),
                    call.update_include_flag("https://www.nicovideo.jp/user/10000004/video", False),
                    call.update_include_flag("https://www.nicovideo.jp/user/10000005/video", False),
                ],
                instance.mylist_db.mock_calls,
            )
            self.assertEqual(
                [
                    call.update_status_in_mylist("https://www.nicovideo.jp/user/10000001/video", ""),
                    call.update_status_in_mylist("https://www.nicovideo.jp/user/10000002/video", ""),
                    call.update_status_in_mylist("https://www.nicovideo.jp/user/10000003/video", ""),
                    call.update_status_in_mylist("https://www.nicovideo.jp/user/10000004/video", ""),
                    call.update_status_in_mylist("https://www.nicovideo.jp/user/10000005/video", ""),
                ],
                instance.mylist_info_db.mock_calls,
            )

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            if params.kind_get_upper_textbox == "valid":
                instance.get_all_table_row.assert_not_called()
                instance.set_all_table_row.assert_not_called()
            else:  # "empty"
                mylist_url = ""
                instance.get_all_table_row.assert_called_once_with()
                instance.set_all_table_row.assert_called_once_with(instance.get_all_table_row.return_value)

            instance.update_mylist_pane.assert_called_once_with()
            instance.update_table_pane.assert_called_once_with(mylist_url)

        params_list = [
            Params("valid", Result.success),
            Params("empty", Result.success),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
