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
                "2022-02-01 02:30:00",
                "2022-02-01 02:30:00",
                "2022-02-01 02:30:00",
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

    def callback(self) -> Result:
        mock_popup = self.enterContext(patch("nnmm.process.delete_mylist.popup"))

        Params = namedtuple(
            "Params",
            ["kind_selected_mylist_row", "kind_select_from_url", "popup", "result"],
        )

        def pre_run(params: Params) -> DeleteMylist:
            instance = self._get_instance()
            instance.get_selected_mylist_row = MagicMock()
            instance.get_upper_textbox = MagicMock()
            instance.get_bottom_textbox = MagicMock()
            m_list = self._make_mylist_db()
            mylist_url = m_list["url"]
            if params.kind_selected_mylist_row == "mylist":
                showname = "投稿者1さんの投稿動画"
                instance.get_selected_mylist_row.return_value = SelectedMylistRow.create(showname)
            elif params.kind_selected_mylist_row == "upper":
                textbox = MagicMock()
                textbox.to_str.return_value = mylist_url
                instance.get_upper_textbox.return_value = textbox
            elif params.kind_selected_mylist_row == "bottom":
                textbox = MagicMock()
                textbox.to_str.return_value = mylist_url
                instance.get_bottom_textbox.return_value = textbox
            else:  # "invalid"
                pass

            instance.mylist_db = MagicMock()
            if params.kind_select_from_url == "valid":
                pass
            elif params.kind_select_from_url == "not_exist":
                pass
            else:  # "error"
                pass
            return instance

        def post_run(actual: Result, instance: DeleteMylist, params: Params) -> None:
            pass

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mockli = self.enterContext(patch("nnmm.process.delete_mylist.logger.info"))
            mockle = self.enterContext(patch("nnmm.process.delete_mylist.logger.error"))
            mock_update_mylist_pane = self.enterContext(
                patch("nnmm.process.delete_mylist.ProcessBase.update_mylist_pane")
            )
            mock_get_selected_mylist_row = self.enterContext(
                patch("nnmm.process.delete_mylist.ProcessBase.get_selected_mylist_row")
            )
            mock_get_upper_textbox = self.enterContext(
                patch("nnmm.process.delete_mylist.ProcessBase.get_upper_textbox")
            )
            mock_get_bottom_textbox = self.enterContext(
                patch("nnmm.process.delete_mylist.ProcessBase.get_bottom_textbox")
            )
            mock_popup_ok_cancel = self.enterContext(patch("nnmm.process.delete_mylist.sg.popup_ok_cancel"))
            mock_mylist_db = MagicMock()

            instance = DeleteMylist(self.process_info)

            # 正常系
            showname_s = "投稿者1さんの投稿動画"
            mylist_url_s = "https://www.nicovideo.jp/user/11111111/video"

            def return_select_from_showname(showname):
                url_dict = {
                    showname_s: {"url": mylist_url_s},
                }
                res = url_dict.get(showname, {})
                return [res] if res else []

            def return_select_from_url(mylist_url):
                showname_dict = {
                    mylist_url_s: {"showname": showname_s},
                }
                return [showname_dict.get(mylist_url, {})]

            def pre_run(values_kind, s_prev_mylist, s_popup_ok_cancel):
                instance.window.reset_mock()
                mock_mylist_db.select_from_showname.reset_mock()
                mock_get_selected_mylist_row.reset_mock()
                mock_get_upper_textbox.reset_mock()
                mock_get_bottom_textbox.reset_mock()
                if values_kind == "-LIST-":

                    def f():
                        return SelectedMylistRow.create(showname_s)

                    mock_get_selected_mylist_row.side_effect = f
                    mock_mylist_db.select_from_showname.side_effect = return_select_from_showname
                elif values_kind == "-LIST_NEW_MARK-":

                    def f():
                        return SelectedMylistRow.create("*:" + showname_s)

                    mock_get_selected_mylist_row.side_effect = f
                    mock_mylist_db.select_from_showname.side_effect = return_select_from_showname
                elif values_kind == "-INPUT1-":

                    def f():
                        return UpperTextbox(mylist_url_s)

                    mock_get_upper_textbox.side_effect = f
                    mock_get_selected_mylist_row.side_effect = lambda: 0
                elif values_kind == "-INPUT2-":

                    def f():
                        return BottomTextbox(mylist_url_s)

                    mock_get_bottom_textbox.side_effect = f
                    mock_get_selected_mylist_row.side_effect = lambda: 0
                    mock_get_upper_textbox.side_effect = lambda: 0

                mock_mylist_db.select_from_url.reset_mock()
                if s_prev_mylist == "":
                    mock_mylist_db.select_from_url.side_effect = lambda mylist_url: [{}]
                elif s_prev_mylist == "invalid":
                    mock_mylist_db.select_from_url.side_effect = lambda mylist_url: ""
                else:
                    mock_mylist_db.select_from_url.side_effect = return_select_from_url
                mock_mylist_db.delete_from_mylist_url.reset_mock()
                instance.mylist_db = mock_mylist_db

                mock_popup_ok_cancel.reset_mock()
                if s_popup_ok_cancel:
                    mock_popup_ok_cancel.return_value = "Ok"
                else:
                    mock_popup_ok_cancel.return_value = "Cancel"

                instance.mylist_info_db.delete_in_mylist = MagicMock()
                mock_update_mylist_pane.reset_mock()

            def post_run(values_kind, s_prev_mylist, s_popup_ok_cancel):
                mock_get_selected_mylist_row.assert_called_once_with()
                if values_kind in ["-LIST-", "-LIST_NEW_MARK-"]:
                    instance.mylist_db.select_from_showname.assert_called_once_with(showname_s)
                    mock_get_upper_textbox.assert_not_called()
                    mock_get_bottom_textbox.assert_not_called()
                elif values_kind == "-INPUT1-":
                    mock_get_upper_textbox.assert_called_once_with()
                    mock_get_bottom_textbox.assert_not_called()
                    instance.mylist_db.select_from_showname.assert_not_called()
                elif values_kind == "-INPUT2-":
                    mock_get_upper_textbox.assert_called_once_with()
                    mock_get_bottom_textbox.assert_called_once_with()
                    instance.mylist_db.select_from_showname.assert_not_called()

                instance.mylist_db.select_from_url.assert_called_once_with(mylist_url_s)
                if s_prev_mylist in ["", "invalid"]:
                    mock_popup_ok_cancel.assert_not_called()
                    instance.mylist_info_db.delete_in_mylist.assert_not_called()
                    instance.mylist_db.delete_from_mylist_url.assert_not_called()
                    instance.window.assert_not_called()
                    mock_update_mylist_pane.assert_not_called()
                    return

                mock_popup_ok_cancel.assert_called_once_with(
                    f"{showname_s}\n{mylist_url_s}\nマイリスト削除します", title="削除確認"
                )
                if s_popup_ok_cancel:
                    pass
                else:
                    instance.mylist_info_db.delete_in_mylist.assert_not_called()
                    instance.mylist_db.delete_from_mylist_url.assert_not_called()
                    self.assertEqual(
                        [
                            call.__getitem__("-INPUT2-"),
                            call.__getitem__().update(value="マイリスト削除キャンセル"),
                        ],
                        instance.window.mock_calls,
                    )
                    mock_update_mylist_pane.assert_not_called()
                    return

                instance.mylist_info_db.delete_in_mylist.assert_called_once_with(mylist_url_s)
                instance.mylist_db.delete_from_mylist_url.assert_called_once_with(mylist_url_s)
                mock_update_mylist_pane.assert_called_once_with()

                self.assertEqual(
                    [
                        call.__getitem__("-TABLE-"),
                        call.__getitem__().update(values=[[]]),
                        call.__getitem__("-INPUT1-"),
                        call.__getitem__().update(value=""),
                        call.__getitem__("-INPUT2-"),
                        call.__getitem__().update(value="マイリスト削除完了"),
                    ],
                    instance.window.mock_calls,
                )

            params_list = [
                ("-LIST-", "s_prev_mylist", True, Result.success),
                ("-LIST_NEW_MARK-", "s_prev_mylist", True, Result.success),
                ("-INPUT1-", "s_prev_mylist", True, Result.success),
                ("-INPUT2-", "s_prev_mylist", True, Result.success),
                ("-LIST-", "", True, Result.failed),
                ("-LIST-", "invalid", True, Result.failed),
                ("-LIST-", "s_prev_mylist", False, Result.failed),
            ]
            for params in params_list:
                pre_run(params[0], params[1], params[2])
                actual = instance.run()
                expect = params[-1]
                self.assertIs(expect, actual)
                post_run(params[0], params[1], params[2])
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
