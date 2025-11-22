import sys
import tempfile
import unittest
from pathlib import Path

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import MylistSaveCSV
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestMylistSaveCSV(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.config.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = MylistSaveCSV(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)

    def test_create_component(self):
        """QPushButton("保存") を作成しクリックに接続すること"""
        mock_qpush = self.enterContext(patch("nnmm.process.config.QPushButton"))
        mock_button = mock_qpush.return_value
        # signal のモックを準備
        mock_button.clicked = MagicMock()
        mock_button.clicked.connect = MagicMock()

        instance = MylistSaveCSV(self.process_info)
        actual = instance.create_component()

        mock_qpush.assert_called_with("保存")
        self.assertIs(mock_button, actual)
        mock_button.clicked.connect.assert_called()

    def test_callback_success(self):
        # 1) 保存正常系: ファイル選択 -> save_mylist 成功 -> 完了ポップアップ
        dialog_mock = self.enterContext(patch("nnmm.process.config.QFileDialog"))
        dialog_instance = dialog_mock.return_value

        tmp = Path(tempfile.NamedTemporaryFile(delete=False).name)
        try:
            dialog_instance.getOpenFileName.return_value = (str(tmp), "CSV file (*.csv)")
            mock_save = self.enterContext(patch("nnmm.process.config.save_mylist"))
            mock_save.return_value = Result.success
            mock_popup = self.enterContext(patch("nnmm.process.config.popup"))

            proc = MylistSaveCSV(self.process_info)
            actual = proc.callback()

            self.assertEqual(Result.success, actual)
            mock_save.assert_called_with(self.process_info.mylist_db, str(tmp))
            mock_popup.assert_any_call("保存完了")
        finally:
            tmp.unlink(missing_ok=True)

        # 2) キャンセル時は何もせず Result.failed を返す
        dialog_mock = self.enterContext(patch("nnmm.process.config.QFileDialog"))
        dialog_instance = dialog_mock.return_value
        dialog_instance.getOpenFileName.return_value = ("", "")

        mock_save = self.enterContext(patch("nnmm.process.config.save_mylist"))
        mock_popup = self.enterContext(patch("nnmm.process.config.popup"))

        proc = MylistSaveCSV(self.process_info)
        actual = proc.callback()

        self.assertEqual(Result.failed, actual)
        mock_save.assert_not_called()
        mock_popup.assert_not_called()

        # 3) save_mylist が失敗した場合は失敗ポップアップを出して Result.failed を返す
        dialog_mock = self.enterContext(patch("nnmm.process.config.QFileDialog"))
        dialog_instance = dialog_mock.return_value

        tmp = Path(tempfile.NamedTemporaryFile(delete=False).name)
        try:
            dialog_instance.getOpenFileName.return_value = (str(tmp), "CSV file (*.csv)")
            mock_save = self.enterContext(patch("nnmm.process.config.save_mylist"))
            mock_save.return_value = Result.failed
            mock_popup = self.enterContext(patch("nnmm.process.config.popup"))

            proc = MylistSaveCSV(self.process_info)
            actual = proc.callback()

            self.assertEqual(Result.failed, actual)
            mock_save.assert_called_with(self.process_info.mylist_db, str(tmp))
            mock_popup.assert_any_call("保存失敗")
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
