import sys
import unittest
from contextlib import ExitStack
from pathlib import Path

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import MylistSaveCSV
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

CONFIG_FILE_PATH = "./config/config.ini"


class TestMylistSaveCSV(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        process_mylist_save = MylistSaveCSV(self.process_info)
        self.assertEqual(self.process_info, process_mylist_save.process_info)

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mockpgf = self.enterContext(patch("nnmm.process.config.sg.popup_get_file"))
            mocksml = self.enterContext(patch("nnmm.process.config.save_mylist"))
            mockpu = self.enterContext(patch("nnmm.process.config.sg.popup"))

            TEST_RESULT_PATH = "./tests/result.csv"
            mockpgf.side_effect = [TEST_RESULT_PATH, None, TEST_RESULT_PATH]
            mocksml.side_effect = [0, -1]

            self.process_info.mylist_db.return_value = "mylist_db"
            process_mylist_save = MylistSaveCSV(self.process_info)

            # 正常系
            # 実行
            actual = process_mylist_save.run()
            self.assertIs(Result.success, actual)

            # 呼び出し確認
            default_path = Path("") / "result.csv"
            expect_kwargs = {"default_path": default_path.absolute(), "default_extension": "csv", "save_as": True}

            # pgfcal[{n回目の呼び出し}][args=0]
            # pgfcal[{n回目の呼び出し}][kwargs=1]
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("保存先ファイル選択",), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            # lmlcal[{n回目の呼び出し}][args=0]
            lmlcal = mocksml.call_args_list
            self.assertEqual(len(lmlcal), 1)
            self.assertEqual((self.process_info.mylist_db, str(Path(TEST_RESULT_PATH))), lmlcal[0][0])
            mocksml.reset_mock()

            # pucal[{n回目の呼び出し}][args=0]
            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("保存完了",), pucal[0][0])
            mockpu.reset_mock()

            # 異常系
            # ファイル選択をキャンセルされた
            actual = process_mylist_save.run()
            self.assertIs(Result.failed, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("保存先ファイル選択",), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            mocksml.assert_not_called()
            mockpu.assert_not_called()

            # マイリスト保存に失敗
            actual = process_mylist_save.run()
            self.assertIs(Result.failed, actual)

            # 呼び出し確認
            pgfcal = mockpgf.call_args_list
            self.assertEqual(len(pgfcal), 1)
            self.assertEqual(("保存先ファイル選択",), pgfcal[0][0])
            self.assertEqual(expect_kwargs, pgfcal[0][1])
            mockpgf.reset_mock()

            lmlcal = mocksml.call_args_list
            self.assertEqual(len(lmlcal), 1)
            self.assertEqual((self.process_info.mylist_db, str(Path(TEST_RESULT_PATH))), lmlcal[0][0])
            mocksml.reset_mock()

            pucal = mockpu.call_args_list
            self.assertEqual(len(pucal), 1)
            self.assertEqual(("保存失敗",), pucal[0][0])
            mockpu.reset_mock()
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
