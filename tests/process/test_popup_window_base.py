import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.popup import PopupWindowBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


# テスト用具体化PopupWindowBase
class ConcretePopupWindowBase(PopupWindowBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_window_layout(self):
        return [["layout"]]

    def init(self) -> Result:
        return Result.success


class TestPopupWindowBase(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    @unittest.skip("")
    def test_init(self):
        instance = ConcretePopupWindowBase(self.process_info)

        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(None, instance.popup_window)
        self.assertEqual("", instance.title)
        self.assertEqual((100, 100), instance.size)
        self.assertEqual({}, instance.process_dict)

        self.assertIs(Result.success, instance.init())

    @unittest.skip("")
    def test_make_window_layout(self):
        instance = ConcretePopupWindowBase(self.process_info)
        self.assertEqual([["layout"]], instance.create_window_layout())

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mock_logger_info = self.enterContext(patch("nnmm.process.popup.logger.info"))
            mock_window = self.enterContext(patch("nnmm.process.popup.QDialog"))
            mock_init = self.enterContext(patch("nnmm.process.popup.PopupWindowBase.init"))
            mock_layout = self.enterContext(patch("nnmm.process.popup.PopupWindowBase.make_window_layout"))
            mock_popup_ok = self.enterContext(patch("nnmm.process.popup.sg.popup_ok"))
            mock_process_info = self.enterContext(patch("nnmm.process.popup.ProcessInfo"))
            mock_process_base = MagicMock()

            event_list = [("-DO-", "value1"), ("-DO_NOTHING-", "value2"), ("-EXIT-", "value3")]
            instance = ConcretePopupWindowBase(self.process_info)

            def pre_run(s_init, s_layout):
                mock_init.reset_mock()
                mock_init.return_value = s_init
                instance.init = mock_init

                mock_layout.reset_mock()
                mock_layout.return_value = s_layout
                instance.create_window_layout = mock_layout

                mock_window.reset_mock()
                mock_window.return_value.read.side_effect = event_list
                mock_process_base.reset_mock()
                instance.process_dict = {"-DO-": mock_process_base}
                mock_process_info.reset_mock()
                mock_popup_ok.reset_mock()

            def post_run(s_init, s_layout):
                self.assertEqual(
                    [
                        call(),
                    ],
                    mock_init.mock_calls,
                )
                if s_init == Result.failed:
                    self.assertEqual(
                        [
                            call("情報ウィンドウの初期化に失敗しました。"),
                        ],
                        mock_popup_ok.mock_calls,
                    )
                    mock_layout.assert_not_called()
                    mock_window.assert_not_called()
                    mock_process_info.assert_not_called()
                    mock_process_base.assert_not_called()
                    return

                self.assertEqual(
                    [
                        call(),
                    ],
                    mock_layout.mock_calls,
                )
                if not s_layout:
                    self.assertEqual(
                        [
                            call("情報ウィンドウのレイアウト表示に失敗しました。"),
                        ],
                        mock_popup_ok.mock_calls,
                    )
                    mock_window.assert_not_called()
                    mock_process_info.assert_not_called()
                    mock_process_base.assert_not_called()
                    return

                self.assertEqual(
                    [
                        call(instance.title, s_layout, size=(100, 100), finalize=True, resizable=True, modal=True),
                        call().read(),
                        call().read(),
                        call().read(),
                        call().close(),
                    ],
                    mock_window.mock_calls,
                )

                self.assertEqual(
                    [
                        call(
                            "-DO-", instance.popup_window, instance.values, instance.mylist_db, instance.mylist_info_db
                        )
                    ],
                    mock_process_info.mock_calls,
                )

                self.assertEqual(
                    [call.__bool__(), call(mock_process_info()), call().run()], mock_process_base.mock_calls
                )

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
