import sys
import unittest
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.delete_mylist import DeleteMylist
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class TestDeleteMylist(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.delete_mylist.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.delete_mylist.logger.error"))
            mock_update_mylist_pane = stack.enter_context(patch("NNMM.process.delete_mylist.update_mylist_pane"))
            mock_popup_ok_cancel = stack.enter_context(patch("NNMM.process.delete_mylist.sg.popup_ok_cancel"))
            mock_mylist_db = MagicMock()

            instance = DeleteMylist(self.process_info)

            # 正常系
            showname_s = "sample_mylist_showname"
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
                mock_mylist_db.select_from_showname.reset_mock()
                if values_kind == "-LIST-":
                    instance.values = {
                        "-LIST-": [showname_s]
                    }
                    mock_mylist_db.select_from_showname.side_effect = return_select_from_showname
                elif values_kind == "-LIST_NEW_MARK-":
                    instance.values = {
                        "-LIST-": ["*:" + showname_s]
                    }
                    mock_mylist_db.select_from_showname.side_effect = return_select_from_showname
                elif values_kind == "-INPUT1-":
                    instance.values = {
                        "-INPUT1-": mylist_url_s
                    }
                elif values_kind == "-INPUT2-":
                    instance.values = {
                        "-INPUT2-": mylist_url_s
                    }

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
                instance.window.reset_mock()
                mock_update_mylist_pane.reset_mock()

            def post_run(values_kind, s_prev_mylist, s_popup_ok_cancel):
                if values_kind in ["-LIST-", "-LIST_NEW_MARK-"]:
                    instance.mylist_db.select_from_showname.assert_called_once_with(showname_s)
                else:
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
                    self.assertEqual([
                        call.__getitem__("-INPUT2-"),
                        call.__getitem__().update(value="マイリスト削除キャンセル"),
                    ], instance.window.mock_calls)
                    mock_update_mylist_pane.assert_not_called()
                    return

                instance.mylist_info_db.delete_in_mylist.assert_called_once_with(mylist_url_s)
                instance.mylist_db.delete_from_mylist_url.assert_called_once_with(mylist_url_s)
                mock_update_mylist_pane.assert_called_once_with(instance.window, instance.mylist_db)

                self.assertEqual([
                    call.__getitem__("-TABLE-"),
                    call.__getitem__().update(values=[[]]),
                    call.__getitem__("-INPUT1-"),
                    call.__getitem__().update(value=""),
                    call.__getitem__("-INPUT2-"),
                    call.__getitem__().update(value="マイリスト削除完了"),
                ], instance.window.mock_calls)

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
