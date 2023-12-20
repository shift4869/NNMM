import sys
import threading
import unittest
from collections import namedtuple
from contextlib import ExitStack
from copy import deepcopy

import PySimpleGUI as sg
from mock import AsyncMock, MagicMock, ThreadingMock, call, patch

from NNMM.model import Mylist, MylistInfo
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.base import Base, ThreadDoneBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


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
        self.process_info.window = MagicMock(spec=sg.Window)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_db(self, num: int = 5) -> list[dict]:
        """mylist_db.select()で取得されるマイリストデータセット
        """
        res = []
        col = ["id", "username", "mylistname", "type", "showname", "url",
               "created_at", "updated_at", "checked_at", "check_interval", "is_include_new"]
        rows = [[i, f"投稿者{i + 1}", "投稿動画", "uploaded",
                 f"投稿者{i + 1}さんの投稿動画",
                 f"https://www.nicovideo.jp/user/1000000{i + 1}/video",
                 "2022-02-01 02:30:00", "2022-02-01 02:30:00", "2022-02-01 02:30:00",
                 "15分", True if i % 2 == 0 else False] for i in range(num)]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_mylist_info_db(self, mylist_url: str) -> list[dict]:
        """mylist_info_db.select()で取得される動画情報データセット
        """
        res = []
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況",
                           "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status",
                      "uploaded_at", "registered_at", "video_url", "mylist_url"]
        num = 5
        n = 0
        for k in range(num):
            table_rows = [[n, f"sm{k + 1}000000{i + 1}", f"動画タイトル{k + 1}_{i + 1}",
                           f"投稿者{k + 1}", "",
                           f"2022-02-01 0{k + 1}:00:0{i + 1}",
                           f"2022-02-01 0{k + 1}:01:0{i + 1}",
                           f"https://www.nicovideo.jp/watch/sm{k + 1}000000{i + 1}",
                           mylist_url] for i in range(num)]
            n = n + 1

            for rows in table_rows:
                d = {}
                for r, c in zip(rows, table_cols):
                    d[c] = r
                res.append(d)
        return res

    def _make_prev_video_lists(self, m_list: list[Mylist]) -> list[list[MylistInfo]]:
        """prev_video_lists データセット
        """
        prev_video_lists = []
        for record in m_list:
            mylist_url = record.get("url")
            prev_video_list = self._make_mylist_info_db(mylist_url)
            prev_video_lists.append(prev_video_list)
        return prev_video_lists

    def test_init(self):
        instance = ConcreteBase(self.process_info)
        self.assertIsNotNone(instance.lock)
        self.assertEqual(0, instance.done_count)
        self.assertEqual(ThreadDoneBase, instance.post_process)
        self.assertEqual("Concrete Kind", instance.L_KIND)
        self.assertEqual("Concrete Event Key", instance.E_DONE)

    def test_get_target_mylist(self):
        instance = ConcreteBase(self.process_info)
        actual = instance.get_target_mylist()
        self.assertEqual([], actual)

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.update_mylist.base.logger.info"))
            mock_thread = stack.enter_context(patch("NNMM.process.update_mylist.base.threading.Thread"))

            instance = ConcreteBase(self.process_info)

            actual = instance.run()
            self.assertIs(Result.success, actual)

            self.assertEqual([
                call.__getitem__("-INPUT2-"),
                call.__getitem__().update(value="更新中"),
                call.refresh(),
            ], instance.window.mock_calls)

            self.assertEqual([
                call(target=instance.update_mylist_info_thread, 
                     daemon=True),
                call().start(),
            ], mock_thread.mock_calls)

    def test_update_mylist_info_thread(self):
        return
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.update_mylist.base.logger.info"))
            mockle = stack.enter_context(patch("NNMM.process.update_mylist.base.logger.error"))
            mock_time = stack.enter_context(patch("NNMM.process.update_mylist.base.time"))
            mock_thread = stack.enter_context(patch("NNMM.process.update_mylist.base.threading"))
            mock_get_target_mylist = MagicMock()
            mock_get_prev_video_lists = MagicMock()
            mock_get_mylist_info_execute = MagicMock()
            mock_update_mylist_info_execute = MagicMock()

            instance = ConcreteBase(self.process_info)

            def pre_run(valid_m_list):
                instance.window.reset_mock()
                mock_get_target_mylist.reset_mock()
                if valid_m_list:
                    m_list = self._make_mylist_db()
                    mock_get_target_mylist.side_effect = lambda: m_list
                else:
                    mock_get_target_mylist.side_effect = lambda: []
                instance.get_target_mylist = mock_get_target_mylist
                mock_get_prev_video_lists.reset_mock()
                instance.get_prev_video_lists = mock_get_prev_video_lists
                mock_get_mylist_info_execute.reset_mock()
                instance.get_mylist_info_execute = mock_get_mylist_info_execute
                mock_update_mylist_info_execute.reset_mock()
                instance.update_mylist_info_execute = mock_update_mylist_info_execute
                mock_time.reset_mock()
                mock_time.time.side_effect = lambda: 0

            def post_run(valid_m_list):
                self.assertEqual([
                    call()
                ], mock_get_target_mylist.mock_calls)

                if not valid_m_list:
                    self.assertEqual([
                        call.write_event_value(instance.E_DONE, "")
                    ], instance.window.mock_calls)
                    return
                else:
                    instance.window.assert_not_called()

                m_list = self._make_mylist_db()
                self.assertEqual([
                    call(m_list)
                ], mock_get_prev_video_lists.mock_calls)

                self.assertEqual([
                    call(m_list)
                ], mock_get_mylist_info_execute.mock_calls)

                prev_video_lists = mock_get_prev_video_lists.return_value
                now_video_lists = mock_get_mylist_info_execute.return_value
                self.assertEqual([
                    call(m_list, prev_video_lists, now_video_lists)
                ], mock_update_mylist_info_execute.mock_calls)

                self.assertEqual([
                    call.Lock(),
                    call.Thread(target=instance.thread_done, daemon=False),
                    call.Thread().start(),
                ], mock_thread.mock_calls)

            Params = namedtuple("Params", ["valid_m_list", "result"])
            params_list = [
                Params(True, None),
                Params(False, None),
            ]
            for params in params_list:
                pre_run(params.valid_m_list)
                actual = instance.update_mylist_info_thread()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.valid_m_list)

    def test_thread_done(self):
        return
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.process.update_mylist.base.logger.info"))
            instance = ConcreteBase(self.process_info)

            mock_post_process = MagicMock()
            mock_mw = MagicMock()
            instance.POST_PROCESS = mock_post_process

            actual = instance.thread_done(mock_mw)
            self.assertEqual(None, actual)
            mock_post_process.assert_called_once_with()
            mock_post_process().run.assert_called_once_with(mock_mw)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
