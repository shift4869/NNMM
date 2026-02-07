import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.delete_mylist import DeleteMylist
from nnmm.process.value_objects.mylist_row import SelectedMylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.textbox_bottom import BottomTextbox
from nnmm.process.value_objects.textbox_upper import UpperTextbox
from nnmm.util import Result


class TestDeleteMylist(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.delete_mylist.logger.info"))
        self.enterContext(patch("nnmm.process.delete_mylist.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> DeleteMylist:
        instance = DeleteMylist(self.process_info)
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
        mock_btn = self.enterContext(patch("nnmm.process.delete_mylist.QPushButton"))
        instance = self._get_instance()
        actual = instance.create_component()
        self.assertEqual(mock_btn.return_value, actual)
        mock_btn.assert_any_call(self.process_info.name)
        mock_btn.return_value.clicked.connect.assert_called_once()

    def test_callback(self) -> Result:
        mock_popup = self.enterContext(patch("nnmm.process.delete_mylist.popup"))

        Params = namedtuple(
            "Params",
            [
                "kind_selected_mylist_row",
                "kind_select_from_url",
                "popup",
                "result",
            ],
        )

        def pre_run(params: Params) -> DeleteMylist:
            instance = self._get_instance()
            instance.get_selected_mylist_row = MagicMock()
            instance.get_upper_textbox = MagicMock()
            instance.get_bottom_textbox = MagicMock()
            instance.mylist_db = MagicMock()
            instance.mylist_info_db = MagicMock()

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            if params.kind_selected_mylist_row == "mylist":
                showname = "投稿者1さんの投稿動画"
                instance.get_selected_mylist_row.return_value = SelectedMylistRow.create(showname)
                instance.mylist_db.select_from_showname.return_value = m_list
            elif params.kind_selected_mylist_row == "upper":
                instance.get_selected_mylist_row.return_value = None
                textbox = MagicMock()
                textbox.to_str.return_value = mylist_url
                instance.get_upper_textbox.return_value = textbox
                instance.get_bottom_textbox.return_value = None
            elif params.kind_selected_mylist_row == "bottom":
                instance.get_selected_mylist_row.return_value = None
                textbox = MagicMock()
                textbox.to_str.return_value = mylist_url
                instance.get_upper_textbox.return_value = None
                instance.get_bottom_textbox.return_value = textbox
            else:  # "invalid"
                instance.get_selected_mylist_row.return_value = None
                instance.get_upper_textbox.return_value = None
                instance.get_bottom_textbox.return_value = None

            if params.kind_select_from_url == "valid":
                instance.mylist_db.select_from_url.return_value = m_list
            elif params.kind_select_from_url == "not_exist":
                instance.mylist_db.select_from_url.return_value = [{}]
            else:  # "error"
                instance.mylist_db.select_from_url.return_value = []

            mock_popup.reset_mock()
            if params.popup == "popup_ok":
                mock_popup.return_value = "OK"
            else:  # "popup_cancel"
                mock_popup.return_value = "Cancel"

            instance.update_mylist_pane = MagicMock()
            instance.set_all_table_row = MagicMock()
            instance.set_upper_textbox = MagicMock()
            instance.set_bottom_textbox = MagicMock()

            return instance

        def post_run(actual: Result, instance: DeleteMylist, params: Params) -> None:
            self.assertEqual(params.result, actual)
            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]

            instance.get_selected_mylist_row.assert_called_once_with()
            if params.kind_selected_mylist_row == "mylist":
                instance.mylist_db.select_from_showname.assert_called()
                instance.get_upper_textbox.return_value.to_str.assert_not_called()
                instance.get_bottom_textbox.return_value.to_str.assert_not_called()
            elif params.kind_selected_mylist_row == "upper":
                instance.mylist_db.select_from_showname.assert_not_called()
                instance.get_upper_textbox.return_value.to_str.assert_called_once_with()
            elif params.kind_selected_mylist_row == "bottom":
                instance.mylist_db.select_from_showname.assert_not_called()
                instance.get_bottom_textbox.return_value.to_str.assert_called_once_with()
            else:  # "invalid"
                instance.mylist_db.select_from_showname.assert_not_called()
                instance.get_upper_textbox.assert_called_once_with()
                instance.get_bottom_textbox.assert_called_once_with()
                instance.mylist_db.select_from_url.assert_called()
                mock_popup.assert_not_called()
                instance.mylist_info_db.delete_in_mylist.assert_not_called()
                instance.mylist_db.delete_from_mylist_url.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.set_all_table_row.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                instance.set_bottom_textbox.assert_not_called()
                return

            instance.mylist_db.select_from_url.assert_called()
            if params.kind_select_from_url not in ["valid", "not_exist"]:
                # "invalid"
                mock_popup.assert_not_called()
                instance.mylist_info_db.delete_in_mylist.assert_not_called()
                instance.mylist_db.delete_from_mylist_url.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.set_all_table_row.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                instance.set_bottom_textbox.assert_not_called()
                return

            prev_mylist = m_list[0]
            showname = prev_mylist.get("showname", "")
            msg = f"{showname}\n{mylist_url}\nマイリスト削除します"
            mock_popup.assert_called_once_with(message=msg, title="削除確認", ok_cancel=True)
            if params.popup == "popup_ok":
                pass
            else:  # "popup_cancel"
                instance.set_bottom_textbox.assert_called_once_with("マイリスト削除キャンセル")
                instance.mylist_info_db.delete_in_mylist.assert_not_called()
                instance.mylist_db.delete_from_mylist_url.assert_not_called()
                instance.update_mylist_pane.assert_not_called()
                instance.set_all_table_row.assert_not_called()
                instance.set_upper_textbox.assert_not_called()
                return

            instance.mylist_info_db.delete_in_mylist.assert_called_once_with(mylist_url)
            instance.mylist_db.delete_from_mylist_url.assert_called_once_with(mylist_url)
            instance.update_mylist_pane.assert_called_once_with()
            instance.set_all_table_row.assert_called_once_with([])
            instance.set_upper_textbox.assert_called_once_with("")
            instance.set_bottom_textbox.assert_called_once_with("マイリスト削除完了")

        params_list = [
            Params("mylist", "valid", "popup_ok", Result.success),
            Params("upper", "valid", "popup_ok", Result.success),
            Params("bottom", "valid", "popup_ok", Result.success),
            Params("invalid", "not_exist", "popup_ok", Result.failed),
            Params("mylist", "invalid", "popup_ok", Result.failed),
            Params("mylist", "valid", "popup_cancel", Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
