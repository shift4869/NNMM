import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.base import Base, ThreadDoneBase
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
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.values = MagicMock(spec=dict)
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

    @unittest.skip("")
    def test_run(self):
        with ExitStack() as stack:
            mockli = self.enterContext(patch("nnmm.process.update_mylist.base.logger.info"))
            mock_thread = self.enterContext(patch("nnmm.process.update_mylist.base.threading"))

            instance = ConcreteBase(self.process_info)

            actual = instance.run()
            self.assertIs(Result.success, actual)

            self.assertEqual(
                [
                    call.__getitem__("-INPUT2-"),
                    call.__getitem__().update(value="更新中"),
                    call.refresh(),
                ],
                instance.window.mock_calls,
            )

            self.assertEqual(
                [
                    call.Thread(target=instance.update_mylist_info_thread, daemon=True),
                    call.Thread().start(),
                ],
                mock_thread.mock_calls,
            )

    def test_update_mylist_info_thread(self):
        with ExitStack() as stack:
            mockli = self.enterContext(patch("nnmm.process.update_mylist.base.logger.info"))
            mock_get_target_mylist = self.enterContext(patch("nnmm.process.update_mylist.base.Base.get_target_mylist"))
            mock_time = self.enterContext(patch("nnmm.process.update_mylist.base.time"))
            mock_mylist_with_video_list = self.enterContext(
                patch("nnmm.process.update_mylist.base.MylistWithVideoList.create")
            )
            mock_fetcher = self.enterContext(patch("nnmm.process.update_mylist.base.Fetcher"))
            mock_database_updater = self.enterContext(patch("nnmm.process.update_mylist.base.DatabaseUpdater"))
            mock_thread = self.enterContext(patch("nnmm.process.update_mylist.base.threading"))

            mock_time.time.return_value = 0

            instance = ConcreteBase(self.process_info)
            instance.get_target_mylist = mock_get_target_mylist

            def pre_run(valid_m_list):
                mock_get_target_mylist.reset_mock()
                if valid_m_list:
                    mock_get_target_mylist.side_effect = lambda: "get_target_mylist()"
                else:
                    mock_get_target_mylist.side_effect = lambda: []
                mock_mylist_with_video_list.reset_mock()
                mock_mylist_with_video_list.side_effect = lambda m, db: "MylistWithVideoList.create()"
                mock_fetcher.reset_mock()
                mock_fetcher.return_value.execute.side_effect = lambda: "Fetcher().create()"
                mock_database_updater.reset_mock()
                mock_database_updater.return_value.execute.side_effect = lambda: "DatabaseUpdater().create()"

            def post_run(valid_m_list):
                self.assertEqual([call()], mock_get_target_mylist.mock_calls)
                if valid_m_list:
                    pass
                else:
                    mock_mylist_with_video_list.assert_not_called()
                    mock_fetcher.assert_not_called()
                    mock_database_updater.assert_not_called()
                    return
                self.assertEqual(
                    [call("get_target_mylist()", instance.mylist_info_db)], mock_mylist_with_video_list.mock_calls
                )
                self.assertEqual(
                    [call("MylistWithVideoList.create()", instance.process_info), call().execute()],
                    mock_fetcher.mock_calls,
                )
                self.assertEqual(
                    [call("Fetcher().create()", instance.process_info), call().execute()],
                    mock_database_updater.mock_calls,
                )

            Params = namedtuple("Params", ["valid_m_list", "result"])
            params_list = [
                Params(True, Result.success),
                Params(False, Result.failed),
            ]
            for params in params_list:
                pre_run(*params[:-1])
                actual = instance.update_mylist_info_thread()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(*params[:-1])

    @unittest.skip("")
    def test_thread_done(self):
        with ExitStack() as stack:
            mockli = self.enterContext(patch("nnmm.process.update_mylist.base.logger.info"))
            instance = ConcreteBase(self.process_info)

            instance.post_process = MagicMock()
            actual = instance.thread_done()
            self.assertEqual(Result.success, actual)

            process_info = ProcessInfo.create("-UPDATE_THREAD_DONE-", instance)
            self.assertEqual(
                [call(process_info), call().run()],
                instance.post_process.mock_calls,
            )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
