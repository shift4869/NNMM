import os
import sys
import tempfile
import unittest
from pathlib import Path

import orjson
from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog, QWidget

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.config import ConfigBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class ConcreteConfigBase(ConfigBase):
    CONFIG_FILE_PATH = "./config/config.json"

    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        return None

    def callback() -> Result:
        return Result.success


class TestConfigBase(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.config.logger.info"))
        ConfigBase.config = None
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        process_config_base = ConcreteConfigBase(self.process_info)

        self.assertEqual(self.process_info, process_config_base.process_info)
        self.assertEqual(ConcreteConfigBase.CONFIG_FILE_PATH, ConfigBase.CONFIG_FILE_PATH)
        self.assertEqual(None, ConfigBase.config)

    def test_get_config(self):
        """ConfigBase.get_config が set_config を呼び出して設定を取得し、キャッシュすることを確認する"""
        config_sample = {"general": {"browser_path": "/path"}}

        def set_config():
            ConfigBase.config = config_sample

        mock_set_config = self.enterContext(patch("nnmm.process.config.ConfigBase.set_config", side_effect=set_config))

        # 初回は set_config が呼ばれ、返り値が返る
        actual1 = ConfigBase.get_config()
        self.assertEqual(ConfigBase.config, actual1)
        mock_set_config.assert_called_once()
        mock_set_config.reset_mock()

        # 2回目はキャッシュから返るため set_config は呼ばれない
        actual2 = ConfigBase.get_config()
        self.assertEqual(ConfigBase.config, actual2)
        mock_set_config.assert_not_called()

    def test_set_config(self):
        """ConfigBase.set_config が orjson.loads と Path.read_bytes を使って設定を読み込むことを確認する"""

        orig_path = ConfigBase.CONFIG_FILE_PATH

        # 正常系: 実ファイルに orjson.dumps で書き込み、set_config が辞書を返すこと
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            sample = {
                "general": {
                    "browser_path": "/path/to/browser",
                    "auto_reload": "(使用しない)",
                    "rss_save_path": "/path/to/rss",
                },
                "db": {"save_path": "/path/to/nnmm.db"},
            }
            tmp.close()
            Path(tmp.name).write_bytes(orjson.dumps(sample))
            ConfigBase.CONFIG_FILE_PATH = tmp.name

            cfg = ConfigBase.set_config()
            self.assertIsInstance(cfg, dict)
            self.assertIn("general", cfg)
            self.assertIn("db", cfg)
            self.assertEqual("/path/to/browser", cfg["general"]["browser_path"])
            self.assertEqual("(使用しない)", cfg["general"]["auto_reload"])
            self.assertEqual("/path/to/rss", cfg["general"]["rss_save_path"])
            self.assertEqual("/path/to/nnmm.db", cfg["db"]["save_path"])
            # キャッシュにも格納されていること
            self.assertEqual(ConfigBase.config, cfg)
        finally:
            ConfigBase.CONFIG_FILE_PATH = orig_path
            Path(tmp.name).unlink(missing_ok=True)

        # 異常系: ファイルが存在しない場合は IOError
        ConfigBase.CONFIG_FILE_PATH = orig_path + ".not_exists"
        with self.assertRaises(IOError):
            ConfigBase.set_config()
        ConfigBase.CONFIG_FILE_PATH = orig_path

        # 異常系: JSON が null 等で空の設定となる場合は IOError
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            tmp.close()
            Path(tmp.name).write_bytes(b"null")
            ConfigBase.CONFIG_FILE_PATH = tmp.name
            with self.assertRaises(IOError):
                ConfigBase.set_config()
        finally:
            ConfigBase.CONFIG_FILE_PATH = orig_path
            Path(tmp.name).unlink(missing_ok=True)

        # 異常系: JSON は存在するが構造が期待と異なる場合は IOError を投げる
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            tmp.close()
            # 'db' セクション欠如や general 内のキー不足など、構造不正を示す JSON
            bad_sample = {"general": {"browser_path": "/only_one_key"}}
            Path(tmp.name).write_bytes(orjson.dumps(bad_sample))
            ConfigBase.CONFIG_FILE_PATH = tmp.name
            with self.assertRaises(IOError):
                ConfigBase.set_config()

            # 別パターン：トップレベルキーが想定外
            Path(tmp.name).write_bytes(orjson.dumps({"unexpected": {}}))
            with self.assertRaises(IOError):
                ConfigBase.set_config()
        finally:
            ConfigBase.CONFIG_FILE_PATH = orig_path
            Path(tmp.name).unlink(missing_ok=True)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
