import sys
import unittest

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import ConfigLoad
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

CONFIG_FILE_PATH = "./config/config.json"


class TestConfigLoad(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.config.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = ConfigLoad(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)

    def test_create_component(self):
        instance = ConfigLoad(self.process_info)
        component = instance.create_component()
        self.assertIsNone(component)

    def test_callback(self):
        """ConfigLoad.callback が設定をウィジェットに反映すること（標準候補 / カスタム候補）"""
        window = self.process_info.window
        # 必要なウィジェットを用意
        window.tbox_browser_path = MagicMock()
        window.cbox = MagicMock()
        window.tbox_rss_save_path = MagicMock()
        window.tbox_db_path = MagicMock()

        instance = ConfigLoad(self.process_info)

        # 標準の auto_reload が候補に含まれる場合
        cfg = {
            "general": {"browser_path": "/path/browser", "auto_reload": "(使用しない)", "rss_save_path": "/path/rss"},
            "db": {"save_path": "/path/nnmm.db"},
        }
        self.enterContext(patch("nnmm.process.config.ConfigBase.get_config", return_value=cfg))
        actual = instance.callback()
        self.assertEqual(Result.success, actual)
        window.tbox_browser_path.setText.assert_called_with("/path/browser")
        window.tbox_rss_save_path.setText.assert_called_with("/path/rss")
        window.tbox_db_path.setText.assert_called_with("/path/nnmm.db")
        window.cbox.clear.assert_called_once()
        window.cbox.addItems.assert_called_once()
        window.cbox.setCurrentText.assert_called_with("(使用しない)")

        # リセット
        window.cbox.reset_mock()
        window.tbox_browser_path.reset_mock()
        window.tbox_rss_save_path.reset_mock()
        window.tbox_db_path.reset_mock()

        # カスタムの "n分毎" フォーマットの場合は候補に追加され選択される
        cfg = {
            "general": {"browser_path": "/b2", "auto_reload": "20分毎", "rss_save_path": "/r2"},
            "db": {"save_path": "/d2"},
        }
        self.enterContext(patch("nnmm.process.config.ConfigBase.get_config", return_value=cfg))
        actual = instance.callback()
        self.assertEqual(Result.success, actual)
        window.tbox_browser_path.setText.assert_called_with("/b2")
        window.tbox_rss_save_path.setText.assert_called_with("/r2")
        window.tbox_db_path.setText.assert_called_with("/d2")
        window.cbox.clear.assert_called_once()
        window.cbox.addItems.assert_called_once()
        window.cbox.addItem.assert_called_with("20分毎")
        window.cbox.setCurrentText.assert_called_with("20分毎")

        # リセット
        window.cbox.reset_mock()
        window.tbox_browser_path.reset_mock()
        window.tbox_rss_save_path.reset_mock()
        window.tbox_db_path.reset_mock()

        # カスタムの "n分毎" フォーマットが不正な場合はデフォルトの"(使用しない)"が適用される
        cfg = {
            "general": {"browser_path": "/b3", "auto_reload": "invalid_format", "rss_save_path": "/r3"},
            "db": {"save_path": "/d3"},
        }
        self.enterContext(patch("nnmm.process.config.ConfigBase.get_config", return_value=cfg))
        actual = instance.callback()
        self.assertEqual(Result.success, actual)
        window.tbox_browser_path.setText.assert_called_with("/b3")
        window.tbox_rss_save_path.setText.assert_called_with("/r3")
        window.tbox_db_path.setText.assert_called_with("/d3")
        window.cbox.clear.assert_called_once()
        window.cbox.addItems.assert_called_once()
        window.cbox.setCurrentText.assert_called_with("(使用しない)")

        # リセット
        window.cbox.reset_mock()
        window.tbox_browser_path.reset_mock()
        window.tbox_rss_save_path.reset_mock()
        window.tbox_db_path.reset_mock()

        # 異常系: ウィジェットが存在しない場合は失敗を返す
        # window は QDialog だが tbox や cbox を持たない
        self.process_info.window = MagicMock(spec=QDialog)
        instance = ConfigLoad(self.process_info)

        # 設定は空で返す（中身は使われない）
        self.enterContext(patch("nnmm.process.config.ConfigBase.get_config", return_value={}))

        res = instance.callback()
        self.assertEqual(Result.failed, res)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
