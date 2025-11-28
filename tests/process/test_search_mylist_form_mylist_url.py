import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

import nnmm.process.search
from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.search import MylistSearchFromMylistURL
from nnmm.process.value_objects.mylist_row import MylistRow
from nnmm.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestMylistSearchFromMylistURL(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.search.logger.info"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> MylistSearchFromMylistURL:
        instance = MylistSearchFromMylistURL(self.process_info)
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
                "2022-02-01 02:30:00",
                "2022-02-01 02:30:00",
                "2022-02-01 02:30:00",
                "15分",
                False,
            ]
            for i in range(NUM)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
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

        Params = namedtuple("Params", ["search_mylist_url", "get_indexes", "is_include_new", "is_hit", "result"])

        def pre_run(params: Params) -> MylistSearchFromMylistURL:
            instance = MylistSearchFromMylistURL(self.process_info)
            mock_popup_get_text.reset_mock()
            mock_popup_get_text.side_effect = lambda message: params.search_mylist_url

            instance.get_selected_mylist_row_index = MagicMock()
            if params.get_indexes >= 0:
                instance.get_selected_mylist_row_index.side_effect = lambda: SelectedMylistRowIndex(params.get_indexes)
            else:
                instance.get_selected_mylist_row_index.side_effect = lambda: None
            instance.window = MagicMock()

            m_list = self._make_mylist_db()
            if params.is_include_new:
                m_list = [m | {"is_include_new": True} for m in m_list]
            if not params.is_hit:
                m_list = [m | {"url": "no_hit"} for m in m_list]
            instance.mylist_db = MagicMock()
            instance.mylist_db.select.side_effect = lambda: m_list

            mock_qlist_widget_item.reset_mock()
            instance.set_bottom_textbox = MagicMock()
            return instance

        def post_run(actual: Result, instance: MylistSearchFromMylistURL, params: Params) -> None:
            self.assertEqual(params.result, actual)
            self.assertEqual([call("マイリストURL入力（完全一致）")], mock_popup_get_text.mock_calls)

            if params.search_mylist_url is None or params.search_mylist_url == "":
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
            if not params.is_hit:
                m_list = [m | {"url": "no_hit"} for m in m_list]

            include_new_index_list = []
            match_index_list = []
            for i, m in enumerate(m_list):
                if m["is_include_new"]:
                    mylist_row = MylistRow.create(m["showname"])
                    m["showname"] = mylist_row.with_new_mark_name()
                    include_new_index_list.append(i)
                if params.search_mylist_url == m["url"]:
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

        valid_mylist_url = "https://www.nicovideo.jp/user/10000001/video"
        params_list = [
            Params(valid_mylist_url, 0, True, True, Result.success),
            Params("not found", 0, True, True, Result.success),
            Params(valid_mylist_url, -1, True, True, Result.success),
            Params(valid_mylist_url, 0, False, True, Result.success),
            Params(valid_mylist_url, 0, True, False, Result.success),
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
