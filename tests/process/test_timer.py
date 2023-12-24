import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

import freezegun
import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.timer import Timer
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.process.value_objects.textbox_bottom import BottomTextbox
from NNMM.util import Result


class TestTimer(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = Timer(self.process_info)
        self.assertIsNone(instance.timer_thread)

    def test_timer_cancel(self):
        instance = Timer(self.process_info)

        instance.timer_thread = MagicMock()
        actual = instance._timer_cancel()
        self.assertIsNone(actual)
        self.assertIsNone(instance.timer_thread)

        instance.timer_thread = None
        actual = instance._timer_cancel()
        self.assertIsNone(actual)
        self.assertIsNone(instance.timer_thread)

    def test_run(self):
        with ExitStack() as stack:
            f_now = "2021-11-23 01:00:00"
            mockfg = stack.enter_context(freezegun.freeze_time(f_now))
            mockli = stack.enter_context(patch("NNMM.process.timer.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.timer.logger.error"))
            mock_config = stack.enter_context(patch("NNMM.process.timer.ConfigBase.get_config"))
            mock_threading_timer = stack.enter_context(patch("NNMM.process.timer.threading.Timer"))
            mock_timer_cancel = stack.enter_context(patch("NNMM.process.timer.Timer._timer_cancel"))
            mock_bottom_textbox = stack.enter_context(patch("NNMM.process.timer.ProcessBase.get_bottom_textbox"))
            mock_timer_thread = MagicMock()

            instance = Timer(self.process_info)

            def pre_run(is_use_auto_reload, interval_num, skip_kind, is_cancel):
                mock_config.reset_mock()
                if is_use_auto_reload:
                    if isinstance(interval_num, int):
                        config_dict = {"auto_reload": f"{interval_num}分毎"}
                    else:
                        config_dict = {"auto_reload": "invalid_interval_num"}
                else:
                    config_dict = {"auto_reload": "(使用しない)"}
                mock_config.return_value.__getitem__.side_effect = lambda key: config_dict

                instance.window.reset_mock()
                instance.values.reset_mock()
                mock_bottom_textbox.reset_mock()
                if skip_kind == "-FIRST_SET-":

                    def f():
                        return BottomTextbox.create("")

                    mock_bottom_textbox.side_effect = f
                    instance.values.get.side_effect = lambda key: "-FIRST_SET-"
                elif skip_kind == "-NOW_PROCESSING-":

                    def f():
                        return BottomTextbox.create("更新中")

                    mock_bottom_textbox.side_effect = f
                    instance.values.get.side_effect = lambda key: ""
                else:

                    def f():
                        return BottomTextbox.create("")

                    mock_bottom_textbox.side_effect = f
                    instance.values.get.side_effect = lambda key: ""

                mock_timer_thread.reset_mock()
                if is_cancel:
                    instance.timer_thread = mock_timer_thread
                else:
                    instance.timer_thread = None
                mock_threading_timer.reset_mock()
                mock_timer_cancel.reset_mock()

            def post_run(is_use_auto_reload, interval_num, skip_kind, is_cancel):
                self.assertEqual([call(), call().__getitem__("general")], mock_config.mock_calls)

                if is_use_auto_reload:
                    if not isinstance(interval_num, int) or interval_num < 0:
                        instance.window.assert_not_called()
                        instance.values.assert_not_called()
                        mock_timer_thread.assert_not_called()
                        mock_threading_timer.assert_not_called()
                        mock_bottom_textbox.assert_not_called()
                        return
                else:
                    mock_timer_cancel.assert_called_once_with()

                    mock_timer_thread.assert_not_called()
                    instance.window.assert_not_called()
                    instance.values.assert_not_called()
                    mock_timer_thread.assert_not_called()
                    mock_threading_timer.assert_not_called()
                    mock_bottom_textbox.assert_not_called()
                    return

                self.assertEqual(
                    [
                        call(),
                    ],
                    mock_bottom_textbox.mock_calls,
                )

                expect_window_call = []
                expect_values_call = [call.get("-TIMER_SET-")]
                if skip_kind == "-FIRST_SET-":
                    expect_values_call.append(call.__setitem__("-TIMER_SET-", ""))
                elif skip_kind == "-NOW_PROCESSING-":
                    expect_values_call.append(call.__setitem__("-TIMER_SET-", ""))
                else:
                    expect_window_call.append(call.write_event_value("-PARTIAL_UPDATE-", ""))

                self.assertEqual(expect_window_call, instance.window.mock_calls)
                self.assertEqual(expect_values_call, instance.values.mock_calls)

                mock_timer_cancel.assert_called_once_with()

                self.assertEqual(
                    [call(interval_num * 60, instance.run), call().setDaemon(True), call().start()],
                    mock_threading_timer.mock_calls,
                )

            Params = namedtuple("Params", ["is_use_auto_reload", "interval_num", "skip_kind", "is_cancel", "result"])
            params_list = [
                Params(True, 15, "", True, Result.success),
                Params(True, 15, "-FIRST_SET-", True, Result.success),
                Params(True, 15, "-NOW_PROCESSING-", True, Result.success),
                Params(True, 15, "", False, Result.success),
                Params(True, 15, "-FIRST_SET-", False, Result.success),
                Params(True, 15, "-NOW_PROCESSING-", False, Result.success),
                Params(True, -1, "", True, Result.failed),
                Params(True, "invalid_interval_num", "", True, Result.failed),
                Params(False, 15, "", True, Result.failed),
                Params(False, 15, "", False, Result.failed),
            ]
            for params in params_list:
                pre_run(params.is_use_auto_reload, params.interval_num, params.skip_kind, params.is_cancel)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.is_use_auto_reload, params.interval_num, params.skip_kind, params.is_cancel)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
