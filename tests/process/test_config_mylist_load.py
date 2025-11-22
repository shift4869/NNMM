import sys
import unittest
from pathlib import Path

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog, QListWidget

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import MylistLoadCSV
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

TEST_INPUT_PATH = "./tests/cache/input.csv"


class TestMylistLoadCSV(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.config.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = MylistLoadCSV(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)

    def test_create_component(self):
        """MylistLoadCSV.create_component が QPushButton("読込") を作成し、クリックに接続すること"""
        mock_qpush = self.enterContext(patch("nnmm.process.config.QPushButton"))
        mock_button = mock_qpush.return_value
        # signal のモックを準備
        mock_button.clicked = MagicMock()
        mock_button.clicked.connect = MagicMock()

        instance = MylistLoadCSV(self.process_info)
        actual = instance.create_component()

        mock_qpush.assert_called_with("読込")
        self.assertIs(mock_button, actual)
        mock_button.clicked.connect.assert_called()

    def test_callback(self):
        """MylistLoadCSV.callback の主要ケースを網羅するテスト（成功 / キャンセル / ファイル未存在 / 読込失敗）"""
        mock_file_dialog = self.enterContext(patch("nnmm.process.config.QFileDialog"))
        mock_popup = self.enterContext(patch("nnmm.process.config.popup"))
        mock_load_mylist = self.enterContext(patch("nnmm.process.config.load_mylist"))
        mock_update_pane = self.enterContext(patch("nnmm.process.config.ProcessBase.update_mylist_pane"))
        self.enterContext(patch("nnmm.process.config.time.sleep"))

        # 準備: テスト用ファイルを作成しておく（成功ケース）
        Path(TEST_INPUT_PATH).touch()

        # 1) 正常系：ファイル選択 -> load_mylist が成功 -> update_mylist_pane 実行
        mock_file_dialog.return_value.getOpenFileName.side_effect = lambda caption, dir, filter: (
            TEST_INPUT_PATH,
            filter,
        )
        mock_open_file_name = mock_file_dialog.return_value.getOpenFileName
        mock_load_mylist.return_value = Result.success
        self.process_info.window.list_widget = MagicMock(spec=QListWidget)

        instance = MylistLoadCSV(self.process_info)

        actual = instance.callback()
        self.assertIs(Result.success, actual)

        # getOpenFileName が呼ばれていること
        pgf_calls = mock_open_file_name.call_args_list
        self.assertGreaterEqual(len(pgf_calls), 1)
        # load_mylist が指定ファイルで呼ばれること
        mock_load_mylist.assert_called_with(self.process_info.mylist_db, str(Path(TEST_INPUT_PATH)))
        # 成功時は完了メッセージが表示され、update_mylist_pane が呼ばれる
        mock_popup.assert_any_call("読込完了")
        mock_update_pane.assert_called()

        mock_open_file_name.reset_mock()
        mock_popup.reset_mock()
        mock_load_mylist.reset_mock()
        mock_update_pane.reset_mock()

        # 2) キャンセルされた場合：getOpenFileName が None を返す -> failed
        mock_open_file_name.side_effect = lambda caption, dir, filter: (None, filter)
        actual = instance.callback()
        self.assertIs(Result.failed, actual)
        mock_load_mylist.assert_not_called()
        mock_popup.assert_not_called()

        mock_open_file_name.reset_mock()
        mock_popup.reset_mock()
        mock_load_mylist.reset_mock()

        # 3) ファイルが存在しない場合：getOpenFileName がパスを返すが実ファイルなし -> failed & エラーメッセージ
        # ensure file removed
        Path(TEST_INPUT_PATH).unlink(missing_ok=True)
        mock_open_file_name.side_effect = lambda caption, dir, filter: (TEST_INPUT_PATH, filter)
        actual = instance.callback()
        self.assertIs(Result.failed, actual)
        mock_popup.assert_any_call("読込ファイルが存在しません")
        mock_load_mylist.assert_not_called()

        mock_open_file_name.reset_mock()
        mock_popup.reset_mock()
        mock_load_mylist.reset_mock()

        # 4) 読込に失敗した場合：load_mylist がエラーを返す -> failed & 読込失敗メッセージ
        Path(TEST_INPUT_PATH).touch()
        mock_open_file_name.return_value = TEST_INPUT_PATH
        mock_load_mylist.return_value = Result.failed
        actual = instance.callback()
        self.assertIs(Result.failed, actual)
        mock_load_mylist.assert_called()
        mock_popup.assert_any_call("読込失敗")

        # 後片付け
        Path(TEST_INPUT_PATH).unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
