import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from nnmm.process.value_objects.table_row_list import TableRowList
from nnmm.process.watched import Watched
from nnmm.util import Result


class TestWatched(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.watched.logger.info"))
        self.enterContext(patch("nnmm.process.watched.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> Watched:
        instance = Watched(self.process_info)
        return instance

    def _make_mylist_db(self, num: int = 5) -> list[dict]:
        """mylist_db.select()で取得されるマイリストデータセット"""
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
                False,
            ]
            for i in range(num)
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
        mock_is_mylist_include_new_video = self.enterContext(patch("nnmm.process.watched.is_mylist_include_new_video"))
        Params = namedtuple(
            "Params",
            [
                "kind_selected_table_row_index_list",
                "update_status_res",
                "is_mylist_include_new_video_res",
                "result",
            ],
        )

        def pre_run(params: Params) -> Watched:
            instance = self._get_instance()
            instance.get_selected_table_row_index_list = MagicMock()
            instance.get_all_table_row = MagicMock()
            instance.mylist_db = MagicMock()
            instance.mylist_info_db = MagicMock()
            instance.window.table_widget = MagicMock()

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            r_list = self._make_table_row_list(mylist_url)
            if params.kind_selected_table_row_index_list == "valid":
                instance.get_selected_table_row_index_list.return_value = SelectedTableRowIndexList.create([0])
            else:  # "invalid"
                instance.get_selected_table_row_index_list.return_value = None

            instance.get_all_table_row.return_value = TableRowList.create(r_list)

            instance.mylist_info_db.update_status.return_value = params.update_status_res

            instance.mylist_info_db.select_from_mylist_url.return_value = []

            mock_is_mylist_include_new_video.reset_mock()
            mock_is_mylist_include_new_video.return_value = params.is_mylist_include_new_video_res

            instance.set_all_table_row = MagicMock()
            instance.update_mylist_pane = MagicMock()
            return instance

        def post_run(actual: Result, instance: Watched, params: Params) -> None:
            self.assertEqual(params.result, actual)
            instance.get_selected_table_row_index_list.assert_called_once_with()
            if params.kind_selected_table_row_index_list == "valid":
                pass
            else:  # "invalid"
                instance.get_all_table_row.assert_not_called()
                instance.mylist_db.assert_not_called()
                instance.mylist_info_db.assert_not_called()
                instance.window.table_widget.assert_not_called()
                instance.set_all_table_row.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                return

            instance.get_all_table_row.assert_called_once_with()

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            r_list = self._make_table_row_list(mylist_url)
            table_row_list = TableRowList.create(r_list)
            row_index = 0
            selected_row = table_row_list[row_index]
            video_id = selected_row.video_id.id
            mylist_url = selected_row.mylist_url.non_query_url
            self.assertEqual(
                [
                    call.update_status(video_id, mylist_url, ""),
                    call.select_from_mylist_url(mylist_url),
                ],
                instance.mylist_info_db.mock_calls,
            )

            mock_is_mylist_include_new_video.assert_called_once_with([])
            if not params.is_mylist_include_new_video_res:
                self.assertEqual(
                    [call.update_include_flag(mylist_url, False)],
                    instance.mylist_db.mock_calls,
                )
            else:
                instance.mylist_db.assert_not_called()

            instance.set_all_table_row.assert_called()

            self.assertEqual(
                [call.selectRow(row_index)],
                instance.window.table_widget.mock_calls,
            )

            instance.update_mylist_pane.assert_called_once_with()

        params_list = [
            Params("valid", 0, False, Result.success),
            Params("valid", 0, True, Result.success),
            Params("valid", -1, False, Result.success),
            Params("invalid", 0, False, Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
