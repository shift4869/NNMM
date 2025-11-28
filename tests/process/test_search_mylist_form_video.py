import re
import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

import nnmm.process.search
from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.search import MylistSearchFromVideo
from nnmm.process.value_objects.mylist_row import MylistRow
from nnmm.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestMylistSearchFromVideoFromVideo(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.search.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> MylistSearchFromVideo:
        instance = MylistSearchFromVideo(self.process_info)
        return instance

    def _make_mylist_db(self) -> list[dict]:
        NUM = 5
        res = []
        col = [
            "id",
            "username",
            "mylistname",
            "type",
            "showname",
            "url",
            "created_at",
            "updated_at",
            "checked_at",
            "check_interval",
            "is_include_new",
        ]
        rows = [
            [
                i,
                f"投稿者{i + 1}",
                "投稿動画",
                "uploaded",
                f"投稿者{i + 1}さんの投稿動画",
                f"https://www.nicovideo.jp/user/1000000{i + 1}/video",
                "2025-11-28 12:34:56",
                "2025-11-28 12:34:56",
                "2025-11-28 12:34:56",
                "15分",
                True if i % 2 == 0 else False,
            ]
            for i in range(NUM)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_mylist_info_db(self, mylist_url) -> list[dict]:
        NUM = 5
        res = []

        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        m = int(re.search(pattern, mylist_url)[1])

        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url"]
        table_rows = [
            [
                i,
                f"sm{m}000000{i + 1}",
                f"動画タイトル{m}_{i + 1}",
                f"投稿者{m}",
                "",
                "2025-11-28 12:34:56",
                f"https://www.nicovideo.jp/watch/sm{m}000000{i + 1}",
                f"https://www.nicovideo.jp/user/1000000{m}/video",
            ]
            for i in range(NUM)
        ]

        for rows in table_rows:
            d = {}
            for r, c in zip(rows, table_cols):
                d[c] = r
            res.append(d)
        return res

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)

    def test_create_component(self):
        instance = self._get_instance()
        self.assertIsNone(instance.create_component())

    def test_callback(self):
        mock_popup_get_text = self.enterContext(patch("nnmm.process.search.popup_get_text"))
        mock_qlist_widget_item = self.enterContext(patch("nnmm.process.search.QListWidgetItem"))

        Params = namedtuple("Params", ["pattern", "get_indexes", "is_include_new", "is_hit", "result"])

        def pre_run(params: Params) -> MylistSearchFromVideo:
            instance = MylistSearchFromVideo(self.process_info)
            mock_popup_get_text.reset_mock()
            mock_popup_get_text.side_effect = lambda message: params.pattern

            instance.get_selected_mylist_row_index = MagicMock()
            if params.get_indexes >= 0:
                instance.get_selected_mylist_row_index.side_effect = lambda: SelectedMylistRowIndex(params.get_indexes)
            else:
                instance.get_selected_mylist_row_index.side_effect = lambda: None
            instance.window = MagicMock()

            m_list = self._make_mylist_db()
            if params.is_include_new:
                m_list = [m | {"is_include_new": True} for m in m_list]
            instance.mylist_db = MagicMock()
            instance.mylist_db.select.side_effect = lambda: m_list

            def _make_records(mylist_url):
                records = self._make_mylist_info_db(mylist_url)
                if not params.is_hit:
                    records = [r | {"title": "no_hit"} for r in records]
                return records

            instance.mylist_info_db = MagicMock()
            instance.mylist_info_db.select_from_mylist_url.side_effect = _make_records

            mock_qlist_widget_item.reset_mock()
            instance.set_bottom_textbox = MagicMock()
            return instance

        def post_run(actual: Result, instance: MylistSearchFromVideo, params: Params) -> None:
            self.assertEqual(params.result, actual)
            self.assertEqual([call("動画名検索（正規表現可）")], mock_popup_get_text.mock_calls)

            if params.pattern is None or params.pattern == "":
                instance.get_selected_mylist_row_index.assert_not_called()
                instance.mylist_db.assert_not_called()
                instance.window.assert_not_called()
                mock_qlist_widget_item.assert_not_called()
                return

            instance.get_selected_mylist_row_index.assert_called_once_with()
            index = params.get_indexes

            self.assertEqual([call.select()], instance.mylist_db.mock_calls)
            m_list = self._make_mylist_db()
            if params.is_include_new:
                m_list = [m | {"is_include_new": True} for m in m_list]

            include_new_index_list = []
            match_index_list = []
            for i, m in enumerate(m_list):
                if m["is_include_new"]:
                    mylist_row = MylistRow.create(m["showname"])
                    m["showname"] = mylist_row.with_new_mark_name()
                    include_new_index_list.append(i)

                mylist_url = m["url"]
                records = self._make_mylist_info_db(mylist_url)
                if not params.is_hit:
                    records = [r | {"title": "no_hit"} for r in records]
                for r in records:
                    if re.findall(params.pattern, r["title"]):
                        match_index_list.append(i)
                        index = i
            list_data = [m["showname"] for m in m_list]

            list_widget_calls = [call.list_widget.clear()]
            list_item_calls = []
            for i, data in enumerate(list_data):
                list_item_calls.append(call(data))
                if i in include_new_index_list:
                    list_item_calls.append(call().setBackground(nnmm.process.search.NEW_MYLIST_COLOR))
                if i in match_index_list:
                    list_item_calls.append(call().setBackground(nnmm.process.search.MATCHED_MYLIST_COLOR))
                list_widget_calls.append(call.list_widget.addItem(mock_qlist_widget_item.return_value))
            list_widget_calls.append(call.list_widget.setCurrentRow(index))

            self.assertEqual(list_widget_calls, instance.window.mock_calls)
            self.assertEqual(list_item_calls, mock_qlist_widget_item.mock_calls)

            if len(match_index_list) > 0:
                instance.set_bottom_textbox.assert_called_once_with(f"{len(match_index_list)}件ヒット！")
            else:
                instance.set_bottom_textbox.assert_called_once_with("該当なし")

        params_list = [
            Params("動画タイトル1_1", 0, True, True, Result.success),
            Params("not found", 0, True, True, Result.success),
            Params("動画タイトル1_1", -1, True, True, Result.success),
            Params("動画タイトル1_1", 0, False, True, Result.success),
            Params("動画タイトル1_1", 0, True, False, Result.success),
            Params("", 0, True, True, Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
