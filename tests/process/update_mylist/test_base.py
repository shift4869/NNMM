import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.base import Base, ThreadDoneBase
from nnmm.process.update_mylist.value_objects.mylist_with_video_list import MylistWithVideoList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class ConcreteBase(Base):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.L_KIND = "Concrete Kind"
        self.E_DONE = "Concrete Event Key"

    def get_target_mylist(self) -> list[dict]:
        return []


class TestBase(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.update_mylist.base.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def test_init(self):
        instance = ConcreteBase(self.process_info)
        self.assertEqual(ThreadDoneBase, instance.post_process)
        self.assertEqual("Concrete Kind", instance.L_KIND)
        self.assertEqual("Concrete Event Key", instance.E_DONE)

    def test_get_target_mylist(self):
        instance = ConcreteBase(self.process_info)
        actual = instance.get_target_mylist()
        self.assertEqual([], actual)

    def test_create_component(self):
        mock_qpush = self.enterContext(patch("nnmm.process.update_mylist.base.QPushButton"))
        mock_btn = mock_qpush.return_value
        mock_btn.clicked = MagicMock()
        mock_btn.clicked.connect = MagicMock()

        instance = ConcreteBase(self.process_info)

        actual = instance.create_component()

        mock_qpush.assert_called_with(self.process_info.name)
        self.assertIs(actual, mock_btn)
        mock_btn.clicked.connect.assert_called()

    def test_callback(self):
        mock_thread = self.enterContext(patch("nnmm.process.update_mylist.base.threading"))

        instance = ConcreteBase(self.process_info)
        instance.set_bottom_textbox = MagicMock()

        actual = instance.callback()
        self.assertIs(Result.success, actual)

        instance.set_bottom_textbox.assert_called_once_with("更新中", False)

        self.assertEqual(
            [
                call.Thread(target=instance.update_mylist_info_thread, daemon=True),
                call.Thread().start(),
            ],
            mock_thread.mock_calls,
        )

    def test_update_mylist_info_thread(self):
        mock_time = self.enterContext(patch("nnmm.process.update_mylist.base.time"))
        mock_mylist_with_video_list = self.enterContext(
            patch("nnmm.process.update_mylist.base.MylistWithVideoList.create", spec=MylistWithVideoList)
        )
        mock_fetcher = self.enterContext(patch("nnmm.process.update_mylist.base.Fetcher"))
        mock_database_updater = self.enterContext(patch("nnmm.process.update_mylist.base.DatabaseUpdater"))
        mock_thread = self.enterContext(patch("nnmm.process.update_mylist.base.threading"))

        mock_time.time.return_value = 0

        # 正常系
        instance = ConcreteBase(self.process_info)
        instance.get_target_mylist = MagicMock()
        instance.get_target_mylist.return_value = ["valid_target_mylist"]

        actual = instance.update_mylist_info_thread()
        self.assertEqual(Result.success, actual)
        self.assertEqual(
            [call(["valid_target_mylist"], instance.mylist_info_db)], mock_mylist_with_video_list.mock_calls
        )
        self.assertEqual(
            [call(mock_mylist_with_video_list.return_value, instance.process_info), call().execute()],
            mock_fetcher.mock_calls,
        )
        self.assertEqual(
            [call(mock_fetcher.return_value.execute.return_value, instance.process_info), call().execute()],
            mock_database_updater.mock_calls,
        )
        self.assertEqual(
            [call.Thread(target=instance.thread_done, daemon=False), call.Thread().start()],
            mock_thread.mock_calls,
        )

        mock_fetcher.reset_mock()
        mock_database_updater.reset_mock()
        mock_thread.reset_mock()

        # 異常系
        instance.get_target_mylist = MagicMock()
        instance.get_target_mylist.return_value = []

        actual = instance.update_mylist_info_thread()
        self.assertEqual(Result.failed, actual)

        mock_fetcher.assert_not_called()
        mock_database_updater.assert_not_called()
        mock_thread.assert_not_called()

    def test_thread_done(self):
        instance = ConcreteBase(self.process_info)

        instance.post_process = MagicMock()
        instance.window.mylist_db = instance.mylist_db
        instance.window.mylist_info_db = instance.mylist_info_db
        actual = instance.thread_done()
        self.assertEqual(Result.success, actual)

        process_info = ProcessInfo.create("-UPDATE_THREAD_DONE-", instance.window)
        self.assertEqual(
            [call(process_info), call().callback()],
            instance.post_process.mock_calls,
        )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
