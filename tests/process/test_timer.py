import sys
import unittest
from collections import namedtuple

import freezegun
from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.timer import Timer
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestTimer(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.timer.logger.info"))
        self.enterContext(patch("nnmm.process.timer.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> Timer:
        instance = Timer(self.process_info)
        return instance

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)
        self.assertIsNone(instance.timer)
        self.assertTrue(instance.first_set)

    def test_timer_cancel(self):
        instance = self._get_instance()
        instance.timer = MagicMock()

        instance.timer.remainingTime.return_value = 0
        actual = instance._timer_cancel()
        self.assertIsNone(actual)
        instance.timer.stop.assert_not_called()

        instance.timer.remainingTime.return_value = 10
        actual = instance._timer_cancel()
        self.assertIsNone(actual)
        self.assertIsNone(instance.timer)

    def test_component(self):
        instance = self._get_instance()
        actual = instance.create_component()
        self.assertIsNone(actual)

    def test_callback(self) -> Result:
        mock_config = self.enterContext(patch("nnmm.process.timer.ConfigBase.get_config"))
        mock_partial = self.enterContext(patch("nnmm.process.timer.partial.Partial"))
        mock_qtimer = self.enterContext(patch("nnmm.process.timer.QTimer"))
        mock_process_info = self.enterContext(patch("nnmm.process.timer.ProcessInfo.create"))
        self.enterContext(freezegun.freeze_time("2026-02-07 00:01:00"))
        Params = namedtuple(
            "Params",
            [
                "config_i_str",
                "kind_skip",
                "result",
            ],
        )

        def pre_run(params: Params) -> Timer:
            instance = self._get_instance()
            instance.get_bottom_textbox = MagicMock()
            instance._timer_cancel = MagicMock()
            mock_config.reset_mock()
            mock_partial.reset_mock()
            mock_qtimer.reset_mock()
            mock_process_info.reset_mock()

            mock_config.return_value = {"general": {"auto_reload": params.config_i_str}}

            if params.kind_skip == "first_set":
                instance.first_set = True
                instance.get_bottom_textbox.return_value.to_str.return_value = ""
            elif params.kind_skip == "running":
                instance.first_set = False
                instance.get_bottom_textbox.return_value.to_str.return_value = "更新中"
            else:  # "start"
                instance.first_set = False
                instance.get_bottom_textbox.return_value.to_str.return_value = ""

            return instance

        def post_run(actual: Result, instance: Timer, params: Params) -> None:
            self.assertEqual(params.result, actual)
            mock_config.assert_called_once_with()
            i_str = params.config_i_str
            if i_str == "(使用しない)" or i_str == "":
                instance._timer_cancel.assert_called_once_with()
                mock_process_info.assert_not_called()
                mock_partial.assert_not_called()
                mock_qtimer.assert_not_called()
                return

            if i_str == "invalid":
                instance._timer_cancel.assert_not_called()
                mock_process_info.assert_not_called()
                mock_partial.assert_not_called()
                mock_qtimer.assert_not_called()
                return

            instance.get_bottom_textbox.return_value.to_str.assert_called_once_with()

            if params.kind_skip == "first_set":
                mock_process_info.assert_not_called()
                mock_partial.assert_not_called()
            elif params.kind_skip == "running":
                mock_process_info.assert_not_called()
                mock_partial.assert_not_called()
            else:  # "start"
                mock_process_info.assert_called_once_with("インターバル更新", instance.window)
                self.assertEqual([call(mock_process_info.return_value), call().callback()], mock_partial.mock_calls)

            instance._timer_cancel.assert_called_once_with()
            mock_qtimer.assert_called()

        params_list = [
            Params("15分毎", "first_set", Result.success),
            Params("15分毎", "running", Result.success),
            Params("15分毎", "start", Result.success),
            Params("(使用しない)", "first_set", Result.failed),
            Params("", "first_set", Result.failed),
            Params("invalid", "first_set", Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
