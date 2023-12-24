import sys
import unittest
from contextlib import ExitStack
from pathlib import Path

import PySimpleGUI as sg
from mock import MagicMock, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.config import MylistLoadCSV
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result

CONFIG_FILE_PATH = "./config/config.ini"


class TestMylistLoadCSV(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        process_mylist_load = MylistLoadCSV(self.process_info)
        self.assertEqual(self.process_info, process_mylist_load.process_info)

    def test_run(self):
        with ExitStack() as stack:
            mockpgf = stack.enter_context(patch("NNMM.process.config.sg.popup_get_file"))
            mockpu = stack.enter_context(patch("NNMM.process.config.sg.popup"))
            mocklml = stack.enter_context(patch("NNMM.process.config.load_mylist"))
            mockums = stack.enter_context(patch("NNMM.process.config.ProcessBase.update_mylist_pane"))

            TEST_INPUT_PATH = "./tests/input.csv"
            mockpgf.side_effect = [TEST_INPUT_PATH, None, TEST_INPUT_PATH, TEST_INPUT_PATH]
            mocklml.side_effect = [0, -1]
            Path(TEST_INPUT_PATH).touch()

            self.process_info.mylist_db.return_value = "mylist_db"
            process_mylist_load = MylistLoadCSV(self.process_info)

            # 正常系
            # 実行
            actual = process_mylist_load.run()
            self.assertIs(Result.success, actual)

            # 呼び出し確認
            default_path = Path("") / "input.csv"
            expect_kwargs = {"default_path": default_path.absolute(), "default_extension": "csv", "save_as": False}

            # pgfcal[{n回目の呼び出し}][args=0]
            # pgfcal[{n回目の呼び出し}][kwargs=1]
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("読込ファイル選択",), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            # lmlcal[{n回目の呼び出し}][args=0]
            lmlcal = mocklml.call_args_list
            self.assertEqual(len(lmlcal), 1)
            self.assertEqual((self.process_info.mylist_db, str(Path(TEST_INPUT_PATH))), lmlcal[0][0])
            mocklml.reset_mock()

            # pucal[{n回目の呼び出し}][args=0]
            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("読込完了",), pucal[0][0])
            mockpu.reset_mock()

            # mockums[{n回目の呼び出し}][args=0]
            umscal = mockums.call_args_list
            self.assertEqual(len(umscal), 1)
            self.assertEqual((), umscal[0][0])
            mockums.reset_mock()

            # 異常系
            # ファイル選択をキャンセルされた
            actual = process_mylist_load.run()
            self.assertIs(Result.failed, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("読込ファイル選択",), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            mocklml.assert_not_called()
            mockpu.assert_not_called()

            # ファイルが存在しない
            Path(TEST_INPUT_PATH).unlink(missing_ok=True)
            actual = process_mylist_load.run()
            self.assertIs(Result.failed, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("読込ファイル選択",), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            mocklml.assert_not_called()

            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("読込ファイルが存在しません",), pucal[0][0])
            mockpu.reset_mock()

            # 読込に失敗
            Path(TEST_INPUT_PATH).touch()
            actual = process_mylist_load.run()
            self.assertIs(Result.failed, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("読込ファイル選択",), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            mocklml.assert_called()

            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("読込失敗",), pucal[0][0])
            mockpu.reset_mock()

            Path(TEST_INPUT_PATH).unlink(missing_ok=True)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
