import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog, QVBoxLayout

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.popup import PopupWindowBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class ConcretePopupWindowBase(PopupWindowBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self._init_ret = Result.success
        self._layout_ret = MagicMock(spec=QVBoxLayout)

    def create_window_layout(self) -> QVBoxLayout | None:
        return self._layout_ret

    def init(self) -> Result:
        return self._init_ret


class TestPopupWindowBase(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.popup.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = ConcretePopupWindowBase(self.process_info)

        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(None, instance.popup_window)
        self.assertEqual("", instance.title)
        self.assertEqual("", instance.url)

    def test_create_component(self):
        instance = ConcretePopupWindowBase(self.process_info)
        self.assertIsNone(instance.create_component())

    def test_init_method(self):
        instance = ConcretePopupWindowBase(self.process_info)
        self.assertEqual(Result.success, instance.init())

    def test_make_window_layout(self):
        instance = ConcretePopupWindowBase(self.process_info)
        self.assertIsInstance(instance.create_window_layout(), QVBoxLayout)

    def test_callback(self):
        mock_popup = self.enterContext(patch("nnmm.process.popup.popup"))
        mock_qdialog = self.enterContext(patch("nnmm.process.popup.QDialog"))
        qdialog_inst = mock_qdialog.return_value
        qdialog_inst.setWindowTitle = MagicMock()
        qdialog_inst.setLayout = MagicMock()
        qdialog_inst.exec = MagicMock()

        # 正常系
        instance = ConcretePopupWindowBase(self.process_info)
        instance.title = "テストタイトル"
        instance.url = "テストURL"

        actual = instance.callback()

        self.assertEqual(Result.success, actual)
        mock_popup.assert_not_called()
        mock_qdialog.assert_called_once()
        qdialog_inst.setWindowTitle.assert_called_once_with("テストタイトル")
        qdialog_inst.setLayout.assert_called_once_with(instance._layout_ret)
        qdialog_inst.exec.assert_called_once()

        mock_popup.reset_mock()
        mock_qdialog.reset_mock()

        # 異常系: ウィンドウレイアウト作成失敗
        instance = ConcretePopupWindowBase(self.process_info)
        instance._layout_ret = None

        actual = instance.callback()

        self.assertEqual(Result.failed, actual)
        mock_popup.assert_called_with("情報ウィンドウのレイアウト表示に失敗しました。")
        mock_qdialog.assert_not_called()

        mock_popup.reset_mock()
        mock_qdialog.reset_mock()

        # 異常系: ウィンドウレイアウト作成失敗
        instance = ConcretePopupWindowBase(self.process_info)
        instance._init_ret = Result.failed

        res = instance.callback()

        self.assertEqual(Result.failed, res)
        mock_popup.assert_called_with("情報ウィンドウの初期化に失敗しました。")
        mock_qdialog.assert_not_called()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
