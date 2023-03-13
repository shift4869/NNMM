# coding: utf-8
"""Timer のテスト
"""

import sys
import unittest
from contextlib import ExitStack
from logging import INFO, getLogger

import freezegun
import PySimpleGUI as sg
from mock import MagicMock, mock_open, patch

from NNMM.GuiFunction import *
from NNMM.Timer import ProcessTimer

TEST_DB_PATH = "./test/test.db"


class TestTimer(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_TimerInit(self):
        """タイマーの初期化後の状態をテストする
        """
        pt = ProcessTimer()
        self.assertIsNone(pt.timer_thread)
        self.assertIsNone(pt.window)
        self.assertIsNone(pt.values)
        pass

    def test_TimerRun(self):
        """タイマーの実行時の処理をテストする
        """
        with ExitStack() as stack:
            f_now = "2021-11-23 01:00:00"
            mockfg = stack.enter_context(freezegun.freeze_time(f_now))
            mockli = stack.enter_context(patch("NNMM.MainWindow.logger.info"))
            mockle = stack.enter_context(patch("NNMM.MainWindow.logger.error"))
            mockcpg = stack.enter_context(patch("NNMM.ConfigMain.ProcessConfigBase.GetConfig"))
            mocktr = stack.enter_context(patch("threading.Timer"))

            pt = ProcessTimer()

            mockcpg.side_effect = lambda: {"general": {"auto_reload": "15分毎"}}

            def mockThread(s, interval, function, *args, **kwargs):
                r = MagicMock()
                type(r).setDaemon = lambda s, f: f
                type(r).start = lambda s: 0
                type(r).cancel = lambda s: 0
                return r

            mocktr.side_effect = mockThread

            def getmock(value):
                r = MagicMock()
                type(r).get = lambda s: value
                return r

            expect_values_dict = {
                "-TIMER_SET-": "",
            }
            expect_window_dict = {
                "-INPUT2-": "",
            }
            for k, v in expect_window_dict.items():
                expect_window_dict[k] = getmock(v)

            mockwm = MagicMock()
            mockwin = MagicMock()
            type(mockwin).write_event_value = lambda s, k, v: f"{k}_{v}"
            mockwin.__getitem__.side_effect = expect_window_dict.__getitem__
            mockwin.__iter__.side_effect = expect_window_dict.__iter__
            mockwin.__contains__.side_effect = expect_window_dict.__contains__
            type(mockwm).window = mockwin
            type(mockwm).values = expect_values_dict

            # イベント起動想定
            actual = pt.Run(mockwm)
            self.assertEqual(0, actual)

            # 既に更新中のためスキップ想定
            expect_window_dict["-INPUT2-"] = getmock("更新中")
            actual = pt.Run(mockwm)
            self.assertEqual(1, actual)

            # 初回起動のためスキップ想定
            expect_values_dict["-TIMER_SET-"] = "-FIRST_SET-"
            actual = pt.Run(mockwm)
            self.assertEqual(1, actual)

            # オートリロードしない設定
            mockcpg.side_effect = lambda: {"general": {"auto_reload": "(使用しない)"}}
            actual = pt.Run(mockwm)
            self.assertEqual(2, actual)

            # オートリロード間隔の指定が不正
            mockcpg.side_effect = lambda: {"general": {"auto_reload": "不正な時間指定"}}
            actual = pt.Run(mockwm)
            self.assertEqual(-1, actual)

            # 引数エラー
            del mockwm.window
            del type(mockwm).window
            actual = pt.Run(mockwm)
            self.assertEqual(-1, actual)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
