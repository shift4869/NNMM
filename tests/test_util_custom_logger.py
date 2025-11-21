import sys
import unittest

from mock import MagicMock, patch
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QDialog

import nnmm.util
from nnmm.util import CustomLogger, window_cache


class TestUtilCustomLogger(unittest.TestCase):
    def test_custom_logger_info(self):
        """CustomLogger が GUI テキストエリアにログを追記することをテストする"""
        self.enterContext(patch("nnmm.util.Logger.info"))

        # 元のキャッシュを退避しておく
        global window_cache
        orig_cache = nnmm.util.window_cache

        class DummyTextarea:
            def __init__(self):
                self.appended_text = ""
                self.last_move = None
                self.updated = False

            def append(self, text):
                self.appended_text = text

            def moveCursor(self, op):
                self.last_move = op

            def update(self):
                self.updated = True

        mock_window = MagicMock(spec=QDialog)
        nnmm.util.window_cache = mock_window

        logger = CustomLogger("testlogger")

        # 通常の info は textarea に追記されること
        mock_window.textarea = DummyTextarea()
        logger.info("info message")
        self.assertIn("info message", mock_window.textarea.appended_text)
        self.assertEqual(QTextCursor.MoveOperation.End, mock_window.textarea.last_move)
        self.assertTrue(mock_window.textarea.updated)

        # args を伴う呼び出しは GUI 更新を行わないこと
        mock_window.textarea = DummyTextarea()
        logger.info("ignored", "with_arg")
        self.assertEqual("", mock_window.textarea.appended_text)
        self.assertIsNone(mock_window.textarea.last_move)
        self.assertFalse(mock_window.textarea.updated)

        # window指定がない場合も GUI 更新を行わないこと
        mock_window = MagicMock(spec=QDialog)
        nnmm.util.window_cache = None
        mock_window.textarea = DummyTextarea()
        logger.info("info message")
        self.assertEqual("", mock_window.textarea.appended_text)
        self.assertIsNone(mock_window.textarea.last_move)
        self.assertFalse(mock_window.textarea.updated)

        # window指定が不正なインスタンスタイプの場合も GUI 更新を行わないこと
        mock_window = MagicMock()
        nnmm.util.window_cache = mock_window
        mock_window.textarea = DummyTextarea()
        logger.info("info message")
        self.assertEqual("", mock_window.textarea.appended_text)
        self.assertIsNone(mock_window.textarea.last_move)
        self.assertFalse(mock_window.textarea.updated)

        # 後始末
        window_cache = orig_cache

    def test_custom_logger_error(self):
        """CustomLogger が GUI テキストエリアにログを追記することをテストする"""
        self.enterContext(patch("nnmm.util.Logger.error"))

        # 元のキャッシュを退避しておく
        global window_cache
        orig_cache = nnmm.util.window_cache

        class DummyTextarea:
            def __init__(self):
                self.appended_text = ""
                self.last_move = None
                self.updated = False

            def append(self, text):
                self.appended_text = text

            def moveCursor(self, op):
                self.last_move = op

            def update(self):
                self.updated = True

        mock_window = MagicMock(spec=QDialog)
        nnmm.util.window_cache = mock_window

        logger = CustomLogger("testlogger")

        # 通常の error は textarea に追記されること
        mock_window.textarea = DummyTextarea()
        logger.error("error message")
        self.assertIn("error message", mock_window.textarea.appended_text)
        self.assertEqual(QTextCursor.MoveOperation.End, mock_window.textarea.last_move)
        self.assertTrue(mock_window.textarea.updated)

        # args を伴う呼び出しは GUI 更新を行わないこと
        mock_window.textarea = DummyTextarea()
        logger.error("ignored", "with_arg")
        self.assertEqual("", mock_window.textarea.appended_text)
        self.assertIsNone(mock_window.textarea.last_move)
        self.assertFalse(mock_window.textarea.updated)

        # window指定がない場合も GUI 更新を行わないこと
        mock_window = MagicMock(spec=QDialog)
        nnmm.util.window_cache = None
        mock_window.textarea = DummyTextarea()
        logger.error("error message")
        self.assertEqual("", mock_window.textarea.appended_text)
        self.assertIsNone(mock_window.textarea.last_move)
        self.assertFalse(mock_window.textarea.updated)

        # window指定が不正なインスタンスタイプの場合も GUI 更新を行わないこと
        mock_window = MagicMock()
        nnmm.util.window_cache = mock_window
        mock_window.textarea = DummyTextarea()
        logger.error("error message")
        self.assertEqual("", mock_window.textarea.appended_text)
        self.assertIsNone(mock_window.textarea.last_move)
        self.assertFalse(mock_window.textarea.updated)

        # 後始末
        window_cache = orig_cache


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
