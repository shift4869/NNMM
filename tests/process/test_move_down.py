import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.move_down import MoveDown
from nnmm.process.value_objects.mylist_row import SelectedMylistRow
from nnmm.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from nnmm.process.value_objects.mylist_row_list import MylistRowList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestMoveDown(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.move_down.logger.info"))
        self.enterContext(patch("nnmm.process.move_down.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> MoveDown:
        instance = MoveDown(self.process_info)
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
                "kind_selected_mylist_row",
                "kind_selected_mylist_row_index",
                "selected_mylist_row_index",
                "result",
            ],
        )

        def pre_run(params: Params) -> MoveDown:
            instance = self._get_instance()
            instance.get_selected_mylist_row = MagicMock()
            instance.get_selected_mylist_row_index = MagicMock()
            instance.get_all_mylist_row = MagicMock()
            instance.mylist_db = MagicMock()
            instance.mylist_info_db = MagicMock()
            instance.window.list_widget = MagicMock()

            m_list = self._make_mylist_db()
            src_index = params.selected_mylist_row_index
            if params.kind_selected_mylist_row == "valid":
                showname = m_list[src_index]["showname"]
                instance.get_selected_mylist_row.return_value = SelectedMylistRow(showname)
            else:  # "invalid"
                instance.get_selected_mylist_row.return_value = None

            if params.kind_selected_mylist_row_index == "valid":
                instance.get_selected_mylist_row_index.return_value = SelectedMylistRowIndex(
                    params.selected_mylist_row_index
                )
            else:  # "invalid"
                instance.get_selected_mylist_row_index.return_value = None

            mylist_row_list: list[str] = [item["showname"] for item in m_list]
            instance.get_all_mylist_row.return_value = MylistRowList.create(mylist_row_list)

            def select_from_showname(showname):
                for item in m_list:
                    if item["showname"] == showname:
                        return [item]
                return [[]]

            instance.mylist_db.select_from_showname.side_effect = select_from_showname
            instance.mylist_db.select.side_effect = lambda: m_list
            instance.update_mylist_pane = MagicMock()

            return instance

        def post_run(actual: Result, instance: MoveDown, params: Params) -> None:
            self.assertEqual(params.result, actual)
            m_list = self._make_mylist_db()

            instance.get_selected_mylist_row.assert_called_once_with()
            if params.kind_selected_mylist_row == "valid":
                pass
            else:  # "invalid"
                instance.get_selected_mylist_row_index.assert_not_called()
                instance.get_all_mylist_row.assert_not_called()
                instance.mylist_db.assert_not_called()
                instance.mylist_info_db.assert_not_called()
                instance.window.list_widget.assert_not_called()
                return

            instance.get_selected_mylist_row_index.assert_called_once_with()
            instance.get_all_mylist_row.assert_called_once_with()

            if params.kind_selected_mylist_row_index == "valid" and params.selected_mylist_row_index >= 4:
                # 最下のマイリストのため下に動かせない
                self.assertEqual(
                    [
                        call.select(),
                    ],
                    instance.mylist_db.mock_calls,
                )
                instance.window.list_widget.assert_not_called()
                return

            src_index = params.selected_mylist_row_index
            dst_index = src_index + 1
            self.assertEqual(
                [
                    call.select(),
                    call.select_from_showname(m_list[src_index]["showname"]),
                    call.select_from_showname(m_list[dst_index]["showname"]),
                    call.swap_id(src_index, dst_index),
                ],
                instance.mylist_db.mock_calls,
            )
            self.assertEqual(
                [
                    call.setCurrentRow(dst_index),
                ],
                instance.window.list_widget.mock_calls,
            )
            instance.update_mylist_pane.assert_called_once_with()

        params_list = [
            Params("valid", "valid", 0, Result.success),
            Params("valid", "invalid", 0, Result.success),
            Params("valid", "valid", 4, Result.failed),
            Params("invalid", "invalid", 0, Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
