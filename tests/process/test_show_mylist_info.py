import sys
import unittest

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.show_mylist_info import ShowMylistInfo
from nnmm.process.value_objects.mylist_row import SelectedMylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestShowMylistInfo(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.show_mylist_info.logger.info"))
        self.enterContext(patch("nnmm.process.show_mylist_info.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> ShowMylistInfo:
        instance = ShowMylistInfo(self.process_info)
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

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)

    def test_component(self):
        instance = self._get_instance()
        actual = instance.create_component()
        self.assertIsNone(actual)

    def test_callback(self) -> Result:
        instance = self._get_instance()
        instance.get_selected_mylist_row = MagicMock()
        instance.mylist_db.select_from_showname = MagicMock()
        instance.set_upper_textbox = MagicMock()
        instance.update_table_pane = MagicMock()

        m_list = self._make_mylist_db()
        mylist_url = m_list[0]["url"]
        showname = m_list[0]["showname"]
        instance.get_selected_mylist_row.return_value = SelectedMylistRow.create(showname)
        instance.mylist_db.select_from_showname.return_value = [{"url": mylist_url}]

        actual = instance.callback()
        self.assertEqual(Result.success, actual)
        instance.get_selected_mylist_row.assert_called_once_with()
        instance.mylist_db.select_from_showname.assert_called_once_with(showname)
        instance.set_upper_textbox.assert_called_once_with(mylist_url)
        instance.update_table_pane.assert_called_once_with(mylist_url)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
