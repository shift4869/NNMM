import copy
import sys
import tempfile
import unittest
from pathlib import Path

import orjson
from mock import MagicMock, patch
from PySide6.QtWidgets import QComboBox, QDialog, QLineEdit

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import ConfigBase, ConfigSave
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

CONFIG_FILE_PATH = "./config/config.json"


class TestConfigSave(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.config.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

        self.process_info.window.tbox_browser_path = MagicMock(spec=QLineEdit)
        self.process_info.window.cbox = MagicMock(spec=QComboBox)
        self.process_info.window.tbox_rss_save_path = MagicMock(spec=QLineEdit)
        self.process_info.window.tbox_db_path = MagicMock(spec=QLineEdit)

    def test_init(self):
        instance = ConfigSave(self.process_info)
        self.assertEqual(self.process_info, instance.process_info)

    def test_create_component(self):
        """create_component は QPushButton("設定保存") を作成しクリック接続する"""
        mock_qpush = self.enterContext(patch("nnmm.process.config.QPushButton"))
        btn = mock_qpush.return_value
        btn.clicked = MagicMock()
        btn.clicked.connect = MagicMock()

        instance = ConfigSave(self.process_info)
        actual = instance.create_component()

        mock_qpush.assert_called_with("設定保存")
        self.assertIs(actual, btn)
        btn.clicked.connect.assert_called()

    def test_callback(self):
        # ConfigSave.callback がウィジェットの設定を設定ファイルに反映すること
        tmp_cfg = Path(tempfile.NamedTemporaryFile(delete=False).name)
        try:
            prev_cfg = {
                "general": {"browser_path": "/b", "auto_reload": "(使用しない)", "rss_save_path": "/r"},
                "db": {"save_path": str(tmp_cfg)},
            }
            ConfigBase.config = prev_cfg

            # 設定書き出しを確認するために CONFIG_FILE_PATH を一時ファイルに差し替える
            orig_cfg_path = ConfigBase.CONFIG_FILE_PATH
            ConfigBase.CONFIG_FILE_PATH = str(tmp_cfg)

            # ウィンドウの値を prev_cfg と同じにする
            self.process_info.window.tbox_browser_path.text.return_value = "/b"
            self.process_info.window.cbox.currentText.return_value = "(使用しない)"
            self.process_info.window.tbox_rss_save_path.text.return_value = "/r"
            self.process_info.window.tbox_db_path.text.return_value = str(tmp_cfg)

            mock_popup = self.enterContext(patch("nnmm.process.config.popup"))
            mock_setcfg = self.enterContext(patch("nnmm.process.config.ConfigBase.set_config"))

            instance = ConfigSave(self.process_info)
            actual = instance.callback()

            self.assertEqual(Result.success, actual)
            mock_popup.assert_called_with("設定保存完了！")
            mock_setcfg.assert_called_once()

            saved_cfg = orjson.loads(Path(ConfigBase.CONFIG_FILE_PATH).read_bytes())
            self.assertEqual(prev_cfg, saved_cfg)

            mock_popup.reset_mock()
            mock_setcfg.reset_mock()

            # カスタムの "n分毎" フォーマットの場合は候補に追加され選択される
            self.process_info.window.cbox.currentText.return_value = "20分毎"
            instance = ConfigSave(self.process_info)
            actual = instance.callback()

            self.assertEqual(Result.success, actual)
            mock_popup.assert_called_with("設定保存完了！")
            mock_setcfg.assert_called_once()

            saved_cfg = orjson.loads(Path(ConfigBase.CONFIG_FILE_PATH).read_bytes())
            expected_cfg = copy.deepcopy(prev_cfg)
            expected_cfg["general"]["auto_reload"] = "20分毎"
            self.assertEqual(expected_cfg, saved_cfg)

            mock_popup.reset_mock()
            mock_setcfg.reset_mock()

            # カスタムの "n分毎" フォーマットが不正な場合はデフォルトの"(使用しない)"が適用される
            self.process_info.window.cbox.currentText.return_value = "invalid_format"
            instance = ConfigSave(self.process_info)
            actual = instance.callback()

            self.assertEqual(Result.success, actual)
            mock_popup.assert_called_with("設定保存完了！")
            mock_setcfg.assert_called_once()

            saved_cfg = orjson.loads(Path(ConfigBase.CONFIG_FILE_PATH).read_bytes())
            self.assertEqual(prev_cfg, saved_cfg)
        finally:
            ConfigBase.CONFIG_FILE_PATH = orig_cfg_path
            tmp_cfg.unlink(missing_ok=True)

        # DBパスが変更され既存DBファイルがあり移動成功した場合、新パスが書き込まれ成功
        tmp_prev = Path(tempfile.NamedTemporaryFile(delete=False).name)
        tmp_new = Path(tempfile.NamedTemporaryFile(delete=False).name)
        try:
            tmp_prev.write_text("db")
            prev_cfg = {
                "general": {"browser_path": "/b", "auto_reload": "(使用しない)", "rss_save_path": "/r"},
                "db": {"save_path": str(tmp_prev)},
            }
            new_cfg = {
                "general": {"browser_path": "/b", "auto_reload": "(使用しない)", "rss_save_path": "/r"},
                "db": {"save_path": str(tmp_new)},
            }
            ConfigBase.config = prev_cfg

            # 設定書き出しを確認するために CONFIG_FILE_PATH を一時ファイルに差し替える
            tmp_cfg = Path(tempfile.NamedTemporaryFile(delete=False).name)
            orig_cfg_path = ConfigBase.CONFIG_FILE_PATH
            ConfigBase.CONFIG_FILE_PATH = str(tmp_cfg)

            # ウィンドウが新しいDBパスを返す（差分あり）
            self.process_info.window.tbox_browser_path.text.return_value = "/b"
            self.process_info.window.cbox.currentText.return_value = "(使用しない)"
            self.process_info.window.tbox_rss_save_path.text.return_value = "/r"
            self.process_info.window.tbox_db_path.text.return_value = str(tmp_new)

            # 実際の DB コントローラ生成を防ぐためコンストラクタをパッチ
            mock_mdb = self.enterContext(patch("nnmm.process.config.MylistDBController"))
            mock_minfo = self.enterContext(patch("nnmm.process.config.MylistInfoDBController"))
            # 実際の shutil.move を使って移動を確認する（必要ならパッチでも可）
            instance = ConfigSave(self.process_info)
            actual = instance.callback()

            self.assertEqual(Result.success, actual)
            # 設定ファイルに新しいパスが書き込まれていること
            saved_cfg = orjson.loads(Path(ConfigBase.CONFIG_FILE_PATH).read_bytes())
            self.assertEqual(new_cfg, saved_cfg)
            # コントローラが再生成されていること
            mock_mdb.assert_called()
            mock_minfo.assert_called()
        finally:
            ConfigBase.CONFIG_FILE_PATH = orig_cfg_path
            tmp_prev.unlink(missing_ok=True)
            tmp_new.unlink(missing_ok=True)
            tmp_cfg.unlink(missing_ok=True)

        # DB移動に失敗した場合は prev path にフォールバックして書き込まれる
        tmp_prev = Path(tempfile.NamedTemporaryFile(delete=False).name)
        tmp_prev.write_text("db")
        try:
            prev_cfg = {
                "general": {"browser_path": "/b", "auto_reload": "(使用しない)", "rss_save_path": "/r"},
                "db": {"save_path": str(tmp_prev)},
            }
            ConfigBase.config = prev_cfg

            tmp_cfg = Path(tempfile.NamedTemporaryFile(delete=False).name)
            orig_cfg_path = ConfigBase.CONFIG_FILE_PATH
            ConfigBase.CONFIG_FILE_PATH = str(tmp_cfg)

            # ウィンドウが新しい（存在しない）DBパスを返す
            new_db = str(Path(tmp_prev.parent) / "nonexistent_dir" / "moved.db")
            self.process_info.window.tbox_browser_path.text.return_value = "/b"
            self.process_info.window.cbox.currentText.return_value = "(使用しない)"
            self.process_info.window.tbox_rss_save_path.text.return_value = "/r"
            self.process_info.window.tbox_db_path.text.return_value = new_db

            # shutil.move が例外を投げるように強制する
            self.enterContext(patch("nnmm.process.config.shutil.move", side_effect=Exception("fail")))
            mock_popup = self.enterContext(patch("nnmm.process.config.popup"))

            instance = ConfigSave(self.process_info)
            actual = instance.callback()

            self.assertEqual(Result.success, actual)
            # 移動失敗により以前のパスが書き戻されていること
            saved_cfg = orjson.loads(Path(ConfigBase.CONFIG_FILE_PATH).read_bytes())
            self.assertEqual(prev_cfg, saved_cfg)
            mock_popup.assert_called_with("設定保存完了！")
        finally:
            ConfigBase.CONFIG_FILE_PATH = orig_cfg_path
            tmp_prev.unlink(missing_ok=True)
            tmp_cfg.unlink(missing_ok=True)

        # 元のDBが存在しない場合は移動せず prev path を保持する
        try:
            prev_cfg = {
                "general": {"browser_path": "/b", "auto_reload": "(使用しない)", "rss_save_path": "/r"},
                "db": {"save_path": "invalid_path.db"},
            }
            ConfigBase.config = prev_cfg

            tmp_cfg = Path(tempfile.NamedTemporaryFile(delete=False).name)
            orig_cfg_path = ConfigBase.CONFIG_FILE_PATH
            ConfigBase.CONFIG_FILE_PATH = str(tmp_cfg)

            # ウィンドウが新しい（存在しない）DBパスを返す
            new_db = str(Path(tmp_prev.parent) / "nonexistent_dir" / "moved.db")
            self.process_info.window.tbox_browser_path.text.return_value = "/b"
            self.process_info.window.cbox.currentText.return_value = "(使用しない)"
            self.process_info.window.tbox_rss_save_path.text.return_value = "/r"
            self.process_info.window.tbox_db_path.text.return_value = new_db

            mock_popup = self.enterContext(patch("nnmm.process.config.popup"))

            instance = ConfigSave(self.process_info)
            actual = instance.callback()

            self.assertEqual(Result.success, actual)
            # 移動失敗により以前のパスが書き戻されていること
            saved_cfg = orjson.loads(Path(ConfigBase.CONFIG_FILE_PATH).read_bytes())
            self.assertEqual(prev_cfg, saved_cfg)
            mock_popup.assert_called_with("設定保存完了！")
        finally:
            ConfigBase.CONFIG_FILE_PATH = orig_cfg_path
            tmp_prev.unlink(missing_ok=True)
            tmp_cfg.unlink(missing_ok=True)

        # 必要なウィジェットが無ければ abort -> Result.failed
        self.process_info.window = MagicMock(spec=QDialog)  # no tbox/cbox attributes
        instance = ConfigSave(self.process_info)

        actual = instance.callback()
        self.assertEqual(Result.failed, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
