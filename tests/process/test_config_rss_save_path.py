import sys
import tempfile
import unittest
from collections import namedtuple
from pathlib import Path

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import ConfigBase, ConfigRSSSavePath
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestConfigRSSSavePath(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.config.logger.info"))
        ConfigBase.config = None
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        process_config_base = ConfigRSSSavePath(self.process_info)

        self.assertEqual(self.process_info, process_config_base.process_info)
        self.assertEqual(ConfigRSSSavePath.CONFIG_FILE_PATH, ConfigBase.CONFIG_FILE_PATH)
        self.assertEqual(None, ConfigBase.config)

    def test_create_component(self):
        """ConfigRSSSavePath.create_component が QPushButton("参照") を作成しクリック接続すること"""
        mock_qpush = self.enterContext(patch("nnmm.process.config.QPushButton"))
        mock_button = mock_qpush.return_value
        mock_button.clicked = MagicMock()
        mock_button.clicked.connect = MagicMock()

        instance = ConfigRSSSavePath(self.process_info)
        comp = instance.create_component()

        mock_qpush.assert_called_with("参照")
        self.assertIs(comp, mock_button)
        mock_button.clicked.connect.assert_called()

    def test_callback(self):
        dialog_mock = self.enterContext(patch("nnmm.process.config.QFileDialog"))
        dialog_inst = dialog_mock.return_value

        Params = namedtuple(
            "Params",
            ["is_use_tbox", "kind_tbox_text", "kind_browser_path_str", "result"],
        )

        def pre_run(params: Params) -> ConfigRSSSavePath:
            self.tmp = Path(tempfile.NamedTemporaryFile(delete=False).name)

            if params.is_use_tbox:
                tbox_mock = MagicMock()
                if params.kind_tbox_text == "valid_existing_path":
                    tbox_mock.text.return_value = self.tmp
                elif params.kind_tbox_text == "valid_non_existing_path":
                    tbox_mock.text.return_value = self.tmp.name + "_nonexistent"
                else:  # params.kind_tbox_text == "invalid_path":
                    tbox_mock.text.return_value = -1
                self.process_info.window.tbox_rss_save_path = tbox_mock
            else:
                self.process_info.window = MagicMock(spec=QDialog)  # tbox_rss_save_path を持たない

            dialog_inst.getExistingDirectory.reset_mock()
            if params.kind_browser_path_str == "valid_existing_path":
                dialog_inst.getExistingDirectory.return_value = self.tmp
            elif params.kind_browser_path_str == "valid_non_existing_path":
                dialog_inst.getExistingDirectory.return_value = self.tmp.name + "_nonexistent"
            elif params.kind_browser_path_str == "empty_path":
                dialog_inst.getExistingDirectory.return_value = ""
            else:  # params.kind_browser_path_str == "invalid_path":
                dialog_inst.getExistingDirectory.return_value = -1

            return ConfigRSSSavePath(self.process_info)

        def post_run(actual, instance, params: Params):
            self.assertEqual(params.result, actual)
            if params.is_use_tbox:
                dialog_inst.getExistingDirectory.assert_called_once()
                if params.kind_browser_path_str == "valid_existing_path":
                    self.process_info.window.tbox_rss_save_path.setText.assert_called_once()
                else:
                    self.process_info.window.tbox_rss_save_path.setText.assert_not_called()
            else:
                dialog_inst.getExistingDirectory.assert_not_called()
                self.assertFalse(hasattr(self.process_info.window, "tbox_rss_save_path"))

            self.tmp.unlink(missing_ok=True)

        params_list = [
            Params(True, "valid_existing_path", "valid_existing_path", Result.success),
            Params(True, "valid_non_existing_path", "valid_existing_path", Result.success),
            Params(True, "invalid_path", "valid_existing_path", Result.success),
            Params(True, "valid_existing_path", "valid_non_existing_path", Result.failed),
            Params(True, "valid_existing_path", "empty_path", Result.failed),
            Params(True, "valid_existing_path", "invalid_path", Result.failed),
            Params(False, "valid_existing_path", "valid_existing_path", Result.failed),
        ]

        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
