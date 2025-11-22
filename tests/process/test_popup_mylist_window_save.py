import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result, interval_translate


class TestPopupMylistWindowSave(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_record(self, interval_num) -> dict:
        return {
            "-ID_INDEX-": 0,
            "-USERNAME-": "username_1",
            "-MYLISTNAME-": "mylistname_1",
            "-TYPE-": "uploaded",
            "-SHOWNAME-": "showname_1",
            "-URL-": "url_1",
            "-CREATED_AT-": "2023-12-13 12:34:56",
            "-UPDATED_AT-": "2023-12-13 12:34:56",
            "-CHECKED_AT-": "2023-12-13 12:34:56",
            "-CHECK_FAILED_COUNT-": 0,
            "-IS_INCLUDE_NEW-": True,
            "-CHECK_INTERVAL_NUM-": interval_num,
            "-CHECK_INTERVAL_UNIT-": "分",
        }

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mock_logger_info = self.enterContext(patch("nnmm.process.popup.logger.info"))
            mock_logger_error = self.enterContext(patch("nnmm.process.popup.logger.error"))
            mock_window = MagicMock()
            mock_mylist_db = MagicMock()

            instance = PopupMylistWindowSave(self.process_info)

            def pre_run(valid_keys_dict_flag, s_interval_num):
                s_record = self._make_record(s_interval_num)

                def _return_get(v):
                    r = MagicMock()
                    r.get.return_value = v
                    return r

                mock_window.reset_mock()
                if valid_keys_dict_flag:
                    mock_window.AllKeysDict.keys.side_effect = s_record.keys
                    mock_window.__getitem__.side_effect = lambda key: _return_get(s_record[key])
                else:
                    mock_window.AllKeysDict.keys.side_effect = lambda: []

                instance.window = mock_window

                mock_mylist_db.reset_mock()
                instance.mylist_db = mock_mylist_db

            def post_run(valid_keys_dict_flag, s_interval_num):
                s_record = self._make_record(s_interval_num)
                if valid_keys_dict_flag:
                    expect_calls = [call.AllKeysDict.keys()]
                    expect_calls.extend([call.__getitem__(key) for key in s_record.keys()])
                    self.assertEqual(expect_calls, mock_window.mock_calls)
                else:
                    mock_window.__getitem__.assert_not_called()
                    mock_mylist_db.assert_not_called()
                    return

                id_index = s_record["-ID_INDEX-"]
                username = s_record["-USERNAME-"]
                mylistname = s_record["-MYLISTNAME-"]
                typename = s_record["-TYPE-"]
                showname = s_record["-SHOWNAME-"]
                url = s_record["-URL-"]
                created_at = s_record["-CREATED_AT-"]
                updated_at = s_record["-UPDATED_AT-"]
                checked_at = s_record["-CHECKED_AT-"]
                check_failed_count = s_record["-CHECK_FAILED_COUNT-"]
                is_include_new = str(s_record["-IS_INCLUDE_NEW-"]) == "True"
                check_interval_num = s_record["-CHECK_INTERVAL_NUM-"]
                check_interval_unit = s_record["-CHECK_INTERVAL_UNIT-"]
                check_interval = str(check_interval_num) + check_interval_unit
                interval_str = check_interval
                dt = interval_translate(interval_str) - 1
                if dt < -1:
                    mock_mylist_db.assert_not_called()
                    return

                self.assertEqual(
                    [
                        call.upsert(
                            id_index,
                            username,
                            mylistname,
                            typename,
                            showname,
                            url,
                            created_at,
                            updated_at,
                            checked_at,
                            check_interval,
                            check_failed_count,
                            is_include_new,
                        )
                    ],
                    mock_mylist_db.mock_calls,
                )

            Params = namedtuple("Params", ["valid_keys_dict_flag", "s_interval_num", "result"])
            params_list = [
                Params(True, 15, Result.success),
                Params(False, 15, Result.failed),
                Params(True, -1, Result.failed),
            ]
            for params in params_list:
                pre_run(params.valid_keys_dict_flag, params.s_interval_num)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.valid_keys_dict_flag, params.s_interval_num)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
