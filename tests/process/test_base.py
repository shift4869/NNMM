import re
import sys
import unittest
from collections import namedtuple

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.main_window import MainWindow
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.base import ProcessBase
from NNMM.process.value_objects.mylist_row import MylistRow
from NNMM.process.value_objects.mylist_row_index import SelectedMylistRowIndex
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.process.value_objects.table_row import TableRowTuple
from NNMM.util import Result


class ConcreteProcessBase(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        return Result.success


class TestProcessBase(unittest.TestCase):
    def setUp(self) -> None:
        process_name = "-TEST_PROCESS-"
        main_window = MagicMock(spec=MainWindow)
        main_window.window = MagicMock(spec=sg.Window)
        main_window.values = MagicMock(spec=dict)
        main_window.mylist_db = MagicMock(spec=MylistDBController)
        main_window.mylist_info_db = MagicMock(spec=MylistInfoDBController)
        self.process_info = ProcessInfo.create(process_name, main_window)

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

    def _make_mylist_info_db(self, mylist_url) -> list[list[dict]]:
        NUM = 5
        res = []

        m = -1
        pattern = r"https://www.nicovideo.jp/user/1000000(\d)/video"
        if re.search(pattern, mylist_url):
            m = int(re.search(pattern, mylist_url)[1])
        if m == -1:
            return []

        table_cols_name = [
            "No.",
            "動画ID",
            "動画名",
            "投稿者",
            "状況",
            "投稿日時",
            "登録日時",
            "動画URL",
            "所属マイリストURL",
            "作成日時",
        ]
        table_cols = [
            "no",
            "video_id",
            "title",
            "username",
            "status",
            "uploaded_at",
            "registered_at",
            "video_url",
            "mylist_url",
            "created_at",
        ]
        table_rows = [
            [
                i,
                f"sm{m}000000{i + 1}",
                f"動画タイトル{m}_{i + 1}",
                f"投稿者{m}",
                "",
                "2022-02-01 02:30:00",
                "2022-02-02 02:30:00",
                f"https://www.nicovideo.jp/watch/sm{m}000000{i + 1}",
                f"https://www.nicovideo.jp/user/1000000{m}/video",
                "2022-02-03 02:30:00",
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
        process_name = "-TEST_PROCESS-"
        instance = ConcreteProcessBase(self.process_info)

        self.assertEqual(self.process_info, instance.process_info)
        self.assertEqual(process_name, instance.name)
        self.assertEqual(self.process_info.window, instance.window)
        self.assertEqual(self.process_info.values, instance.values)
        self.assertEqual(self.process_info.mylist_db, instance.mylist_db)
        self.assertEqual(self.process_info.mylist_info_db, instance.mylist_info_db)

        with self.assertRaises(ValueError):
            instance = ConcreteProcessBase("invalid_process_info")

    def test_run(self):
        instance = ConcreteProcessBase(self.process_info)
        actual = instance.run()
        self.assertIs(Result.success, actual)

    def test_get_selected_mylist_row_index(self):
        instance = ConcreteProcessBase(self.process_info)
        instance.window.__getitem__.return_value.get_indexes.side_effect = lambda: [0]
        actual = instance.get_selected_mylist_row_index()
        self.assertEqual(SelectedMylistRowIndex(0), actual)

        instance.window.__getitem__.return_value.get_indexes.side_effect = ValueError
        actual = instance.get_selected_mylist_row_index()
        self.assertIsNone(actual)

    def test_get_selected_mylist_row(self):
        mock_create = self.enterContext(patch("NNMM.process.base.SelectedMylistRow.create"))
        mock_create.side_effect = lambda showname: showname
        instance = ConcreteProcessBase(self.process_info)
        instance.values.__getitem__.side_effect = lambda key: ["values['-LIST-']"]
        actual = instance.get_selected_mylist_row()
        expect = "values['-LIST-']"
        self.assertEqual(expect, actual)

        instance.values.__getitem__.side_effect = lambda key: None
        actual = instance.get_selected_mylist_row()
        self.assertIsNone(actual)

        instance.values.__getitem__.side_effect = lambda key: ValueError
        actual = instance.get_selected_mylist_row()
        self.assertIsNone(actual)

    def test_get_all_mylist_row(self):
        mock_create = self.enterContext(patch("NNMM.process.base.MylistRowList.create"))
        mock_create.side_effect = lambda mylist_row_list: mylist_row_list
        instance = ConcreteProcessBase(self.process_info)
        instance.window.__getitem__.return_value.Values = "window['-LIST-'].Values"
        actual = instance.get_all_mylist_row()
        expect = "window['-LIST-'].Values"
        self.assertEqual(expect, actual)

        mock_create.side_effect = ValueError
        actual = instance.get_all_mylist_row()
        self.assertIsNone(actual)

    def test_get_selected_table_row_index_list(self):
        mock_create = self.enterContext(patch("NNMM.process.base.SelectedTableRowIndexList.create"))
        mock_create.side_effect = lambda table_row_index_list: table_row_index_list
        instance = ConcreteProcessBase(self.process_info)
        instance.values.__getitem__.side_effect = lambda key: "values['-TABLE-']"
        actual = instance.get_selected_table_row_index_list()
        expect = "values['-TABLE-']"
        self.assertEqual(expect, actual)

        mock_create.side_effect = ValueError
        actual = instance.get_selected_table_row_index_list()
        self.assertIsNone(actual)

    def test_get_selected_table_row_list(self):
        mock_create = self.enterContext(patch("NNMM.process.base.SelectedTableRowList.create"))
        mock_get_all_table_row = self.enterContext(patch("NNMM.process.base.ProcessBase.get_all_table_row"))
        mock_get_selected_table_row_index_list = self.enterContext(
            patch("NNMM.process.base.ProcessBase.get_selected_table_row_index_list")
        )
        mock_create.side_effect = lambda table_row_list: table_row_list

        def make_table_row_mock(index: int) -> MagicMock:
            r = MagicMock()
            r.row_number = index
            r.to_row.side_effect = lambda: index
            return r

        all_table_row = [make_table_row_mock(i) for i in range(10)]
        mock_get_all_table_row.side_effect = lambda: all_table_row

        mock_get_selected_table_row_index_list.return_value.to_int_list.side_effect = lambda: [2, 5]

        instance = ConcreteProcessBase(self.process_info)
        actual = instance.get_selected_table_row_list()
        expect = [3, 6]
        self.assertEqual(expect, actual)
        mock_create.assert_called_once_with([3, 6])

        mock_create.side_effect = ValueError
        actual = instance.get_selected_table_row_list()
        self.assertIsNone(actual)

    def test_get_all_table_row(self):
        mock_create = self.enterContext(patch("NNMM.process.base.TableRowList.create"))
        mock_create.side_effect = lambda table_row_list: table_row_list
        instance = ConcreteProcessBase(self.process_info)
        instance.window.__getitem__.return_value.Values = "window['-TABLE-']"
        actual = instance.get_all_table_row()
        expect = "window['-TABLE-']"
        self.assertEqual(expect, actual)

        mock_create.side_effect = ValueError
        actual = instance.get_all_table_row()
        self.assertIsNone(actual)

    def test_get_upper_textbox(self):
        mock_upper_textbox = self.enterContext(patch("NNMM.process.base.UpperTextbox"))
        mock_upper_textbox.side_effect = lambda table_row_index_list: table_row_index_list
        instance = ConcreteProcessBase(self.process_info)
        instance.window.__getitem__.return_value.get.side_effect = lambda: "window['-INPUT1-']"
        actual = instance.get_upper_textbox()
        expect = "window['-INPUT1-']"
        self.assertEqual(expect, actual)

        mock_upper_textbox.side_effect = ValueError
        actual = instance.get_upper_textbox()
        self.assertIsNone(actual)

    def test_get_bottom_textbox(self):
        mock_bottom_textbox = self.enterContext(patch("NNMM.process.base.BottomTextbox"))
        mock_bottom_textbox.side_effect = lambda table_row_index_list: table_row_index_list
        instance = ConcreteProcessBase(self.process_info)
        instance.window.__getitem__.return_value.get.side_effect = lambda: "window['-INPUT2-']"
        actual = instance.get_bottom_textbox()
        expect = "window['-INPUT2-']"
        self.assertEqual(expect, actual)

        mock_bottom_textbox.side_effect = ValueError
        actual = instance.get_bottom_textbox()
        self.assertIsNone(actual)

    def test_update_mylist_pane(self):
        instance = ConcreteProcessBase(self.process_info)

        def pre_run(s_index, is_include_new, has_mylist_db):
            instance.window.reset_mock()
            if s_index >= 0:

                def f():
                    return [s_index]

                instance.window.__getitem__.return_value.get_indexes.side_effect = f
            else:

                def f():
                    return []

                instance.window.__getitem__.return_value.get_indexes.side_effect = f

            instance.mylist_db.reset_mock()
            if has_mylist_db:
                m_list = self._make_mylist_db()
                m_list = [m | {"is_include_new": is_include_new} for m in m_list]
                instance.mylist_db.select.side_effect = lambda: m_list
            else:
                instance.mylist_db.select.side_effect = lambda: []

        def post_run(s_index, is_include_new, has_mylist_db):
            expect_window_call = [
                call.__getitem__("-LIST-"),
                call.__getitem__().get_indexes(),
            ]
            m_list = self._make_mylist_db()
            m_list = [m | {"is_include_new": is_include_new} for m in m_list]
            if not has_mylist_db:
                m_list = []
            for _, m in enumerate(m_list):
                if m["is_include_new"]:
                    mylist_row = MylistRow.create(m["showname"])
                    m["showname"] = mylist_row.with_new_mark_name()
            list_data = [m["showname"] for m in m_list]
            expect_window_call.extend([
                call.__getitem__("-LIST-"),
                call.__getitem__().update(values=list_data),
            ])
            if is_include_new:
                all_num = len(m_list)
                for i in range(all_num):
                    expect_window_call.extend([
                        call.__getitem__("-LIST-"),
                        call.__getitem__().Widget.itemconfig(i, fg="black", bg="light pink"),
                    ])

            s_index = max(s_index, 0)
            expect_window_call.extend([
                call.__getitem__("-LIST-"),
                call.__getitem__().Widget.see(s_index),
                call.__getitem__("-LIST-"),
                call.__getitem__().update(set_to_index=s_index),
            ])
            self.assertEqual(expect_window_call, instance.window.mock_calls)

            self.assertEqual([call.select()], instance.mylist_db.mock_calls)

        Params = namedtuple("Params", ["s_index", "is_include_new", "has_mylist_db", "result"])
        params_list = [
            Params(0, True, True, Result.success),
            Params(1, True, True, Result.success),
            Params(-1, True, True, Result.success),
            Params(0, False, True, Result.success),
            Params(1, False, True, Result.success),
            Params(-1, False, True, Result.success),
            Params(0, True, False, Result.success),
        ]
        for params in params_list:
            pre_run(*params[:-1])
            actual = instance.update_mylist_pane()
            expect = params.result
            self.assertIs(expect, actual)
            post_run(*params[:-1])

    def test_update_table_pane(self):
        instance = ConcreteProcessBase(self.process_info)
        mylist_url = "https://www.nicovideo.jp/user/10000001/video"

        def pre_run(s_index, s_mylist_url, has_mylist_db, has_mylist_info_db):
            instance.window.reset_mock()
            instance.mylist_db.reset_mock()
            instance.mylist_info_db.reset_mock()

            if s_mylist_url == "":

                def f():
                    return ""

                instance.window.__getitem__.return_value.get.side_effect = f

                records = self._make_mylist_info_db(mylist_url)
                records = [[i + 1] + list(r.values())[1:-1] for i, r in enumerate(records)]
                instance.window.__getitem__.return_value.Values = records
                if s_index >= 0:

                    def g():
                        return [s_index]

                    instance.window.__getitem__.return_value.get_indexes.side_effect = g
                else:

                    def g():
                        return []

                    instance.window.__getitem__.return_value.get_indexes.side_effect = g
            else:
                if has_mylist_db:
                    instance.mylist_db.select.side_effect = self._make_mylist_db
                else:
                    instance.mylist_db.select.side_effect = lambda: []
                if has_mylist_info_db:

                    def f(url):
                        return self._make_mylist_info_db(url)

                    instance.mylist_info_db.select_from_mylist_url.side_effect = f
                else:

                    def f(url):
                        return []

                    instance.mylist_info_db.select_from_mylist_url.side_effect = f

        def post_run(s_index, s_mylist_url, has_mylist_db, has_mylist_info_db):
            expect_window_call = []
            index = 0
            def_data = []
            if s_mylist_url == "":
                expect_window_call.extend([
                    call.__getitem__("-INPUT1-"),
                    call.__getitem__().get(),
                    call.__getitem__("-TABLE-"),
                    call.__getitem__("-LIST-"),
                    call.__getitem__().get_indexes(),
                ])
                records = self._make_mylist_info_db(mylist_url)
                def_data = [[str(i + 1)] + list(r.values())[1:-1] for i, r in enumerate(records)]

                index = max(s_index, 0)
                instance.mylist_db.assert_not_called()
                instance.mylist_info_db.assert_not_called()
            else:
                self.assertEqual([call.select()], instance.mylist_db.mock_calls)

                m_list = self._make_mylist_db()
                if not has_mylist_db:
                    m_list = []
                mylist_url_list = [m["url"] for m in m_list]
                for i, url in enumerate(mylist_url_list):
                    if mylist_url == url:
                        index = i
                        break

                self.assertEqual([call.select_from_mylist_url(s_mylist_url)], instance.mylist_info_db.mock_calls)

                records = self._make_mylist_info_db(s_mylist_url)
                if not has_mylist_info_db:
                    records = []
                for i, r in enumerate(records):
                    record = TableRowTuple._make([i + 1] + list(r.values())[1:-1])
                    table_row = [
                        record.row_index,
                        record.video_id,
                        record.title,
                        record.username,
                        record.status,
                        record.uploaded_at,
                        record.registered_at,
                        record.video_url,
                        record.mylist_url,
                    ]
                    table_row = list(map(str, table_row))
                    def_data.append(table_row)

            expect_window_call.extend([
                call.__getitem__("-LIST-"),
                call.__getitem__().Widget.see(index),
                call.__getitem__("-TABLE-"),
                call.__getitem__().update(values=def_data),
            ])
            if len(def_data) > 0:
                expect_window_call.extend([
                    call.__getitem__("-TABLE-"),
                    call.__getitem__().update(select_rows=[0]),
                ])
            expect_window_call.extend([
                call.__getitem__("-TABLE-"),
                call.__getitem__().update(row_colors=[(0, "", "")]),
            ])
            self.assertEqual(expect_window_call, instance.window.mock_calls)

        Params = namedtuple("Params", ["s_index", "s_mylist_url", "has_mylist_db", "has_mylist_info_db", "result"])
        params_list = [
            Params(1, mylist_url, True, True, Result.success),
            Params(1, mylist_url, True, False, Result.success),
            Params(1, mylist_url, False, True, Result.success),
            Params(1, mylist_url, False, False, Result.success),
            Params(1, "", True, True, Result.success),
            Params(1, "", True, False, Result.success),
            Params(1, "", False, True, Result.success),
            Params(1, "", False, False, Result.success),
            Params(-1, mylist_url, True, True, Result.success),
            Params(-1, mylist_url, True, False, Result.success),
            Params(-1, mylist_url, False, True, Result.success),
            Params(-1, mylist_url, False, False, Result.success),
            Params(-1, "", True, True, Result.success),
            Params(-1, "", True, False, Result.success),
            Params(-1, "", False, True, Result.success),
            Params(-1, "", False, False, Result.success),
        ]
        for params in params_list:
            pre_run(*params[:-1])
            actual = instance.update_table_pane(params.s_mylist_url)
            expect = params.result
            self.assertIs(expect, actual)
            post_run(*params[:-1])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
