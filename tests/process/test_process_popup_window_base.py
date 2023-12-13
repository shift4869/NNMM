import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_popup import PopupWindowBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


# テスト用具体化PopupWindowBase
class ConcretePopupWindowBase(PopupWindowBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def make_window_layout(self) -> list[list[sg.Frame]] | None:
        return [["layout"]]

    def init(self) -> Result:
        return Result.success


class TestPopupWindowBase(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = ConcretePopupWindowBase(self.process_info)

        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(None, instance.popup_window)
        self.assertEqual("", instance.title)
        self.assertEqual((100, 100), instance.size)
        self.assertEqual({}, instance.process_dict)

        self.assertIs(Result.success, instance.init())

    def test_make_window_layout(self):
        instance = ConcretePopupWindowBase(self.process_info)
        self.assertEqual([["layout"]], instance.make_window_layout())

    def test_run(self):
        with ExitStack() as stack:
            mock_logger_info = stack.enter_context(patch("NNMM.process.process_popup.logger.info"))
            mock_window = stack.enter_context(patch("NNMM.process.process_popup.sg.Window"))
            mock_init = stack.enter_context(patch("NNMM.process.process_popup.PopupWindowBase.init"))
            mock_layout = stack.enter_context(patch("NNMM.process.process_popup.PopupWindowBase.make_window_layout"))
            mock_popup_ok = stack.enter_context(patch("NNMM.process.process_popup.sg.popup_ok"))
            mock_process_info = stack.enter_context(patch("NNMM.process.process_popup.ProcessInfo.create"))
            mock_process_base = MagicMock()

            event_list = [("-DO-", "value1"), ("-DO_NOTHING-", "value2"), ("-EXIT-", "value3")]
            instance = ConcretePopupWindowBase(self.process_info)

            def pre_run(s_init, s_layout):
                mock_init.reset_mock()
                mock_init.return_value = s_init
                instance.init = mock_init
                mock_layout.reset_mock()
                mock_layout.return_value = s_layout
                instance.make_window_layout = mock_layout

                mock_window.reset_mock()
                mock_window.return_value.read.side_effect = event_list
                mock_process_base.reset_mock()
                instance.process_dict = {
                    "-DO-": mock_process_base
                }
                mock_process_info.reset_mock()
                mock_popup_ok.reset_mock()

            def post_run(s_init, s_layout):
                self.assertEqual([
                    call(),
                ], mock_init.mock_calls)
                if s_init == Result.failed:
                    self.assertEqual([
                        call("情報ウィンドウの初期化に失敗しました。"),
                    ], mock_popup_ok.mock_calls)
                    mock_layout.assert_not_called()
                    mock_window.assert_not_called()
                    mock_process_info.assert_not_called()
                    mock_process_base.assert_not_called()
                    return

                self.assertEqual([
                    call(),
                ], mock_layout.mock_calls)
                if not s_layout:
                    self.assertEqual([
                        call("情報ウィンドウのレイアウト表示に失敗しました。"),
                    ], mock_popup_ok.mock_calls)
                    mock_window.assert_not_called()
                    mock_process_info.assert_not_called()
                    mock_process_base.assert_not_called()
                    return

                self.assertEqual([
                    call(instance.title, s_layout, size=(100, 100), finalize=True, resizable=True, modal=True),
                    call().read(),
                    call().read(),
                    call().read(),
                    call().close(),
                ], mock_window.mock_calls)

                self.assertEqual([
                    call("-DO-", instance)
                ], mock_process_info.mock_calls)

                self.assertEqual([
                    call.__bool__(),
                    call(mock_process_info()),
                    call().run()
                ], mock_process_base.mock_calls)

            Params = namedtuple("Params", ["init", "layout", "result"])
            params_list = [
                Params(Result.success, [["layout"]], Result.success),
                Params(Result.success, None, Result.failed),
                Params(Result.failed, [["layout"]], Result.failed),
            ]
            for params in params_list:
                pre_run(params.init, params.layout)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.init, params.layout)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
