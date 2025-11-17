import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from nnmm.process.value_objects.table_row_list import SelectedTableRowList
from nnmm.process.video_play import VideoPlay
from nnmm.util import Result


class TestVideoPlay(unittest.TestCase):
    def setUp(self):
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.values = MagicMock(spec=dict)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _make_mylist_db(self, num: int = 5) -> list[dict]:
        """mylist_db.select()で取得されるマイリストデータセット"""
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
            for i in range(num)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_table_data(self, mylist_url) -> list[str]:
        """self.window["-TABLE-"].Valuesで取得されるテーブル情報動画データセット"""
        NUM = 5
        res = []
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
            "マイリスト表示名",
            "マイリスト名",
            "作成日時",
        ]
        for k in range(NUM):
            for i in range(NUM):
                # MylistInfo + showname系
                number = i + (k * NUM)
                video_id = f"sm{k + 1}000000{i + 1}"
                title = f"動画タイトル{k + 1}_{i + 1}"
                username = f"投稿者{k + 1}"
                status = ""
                uploaded_at = f"2022-02-02 0{k + 1}:00:0{i + 1}"
                registered_at = f"2022-02-03 0{k + 1}:00:0{i + 1}"
                video_url = f"https://www.nicovideo.jp/watch/sm{k + 1}000000{i + 1}"
                created_at = f"2022-02-01 0{k + 1}:00:0{i + 1}"
                showname = f"showname_{mylist_url}"
                mylistname = f"mylistname_{mylist_url}"
                table_rows = [
                    number,
                    video_id,
                    title,
                    username,
                    status,
                    uploaded_at,
                    registered_at,
                    video_url,
                    mylist_url,
                    created_at,
                    showname,
                    mylistname,
                ]
                res.append(table_rows)
        return res

    def _convert_table_data_to_dict(self, table_data: list[list[str]]) -> list[dict]:
        table_cols_name = [
            "id",
            "video_id",
            "title",
            "username",
            "status",
            "uploaded_at",
            "registered_at",
            "video_url",
            "mylist_url",
            "created_at",
            "showname",
            "mylistname",
        ]
        res = []
        for table_rows in table_data:
            res.append(dict(zip(table_cols_name, table_rows)))
        return res

    def _get_mylist_info_from_video_id(self, table_data, video_id) -> list[dict]:
        table_dict_list = self._convert_table_data_to_dict(table_data)
        for table_dict in table_dict_list:
            if table_dict.get("video_id") == video_id:
                return [table_dict]
        return []

    def test_run(self):
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("nnmm.process.video_play.logger.info"))
            mock_config = stack.enter_context(patch("nnmm.process.video_play.process_config.ConfigBase.get_config"))
            mock_execute = stack.enter_context(patch("nnmm.process.video_play.sg.execute_command_subprocess"))
            mock_popup = stack.enter_context(patch("nnmm.process.video_play.sg.popup_ok"))
            mock_watched = stack.enter_context(patch("nnmm.process.video_play.Watched"))
            mock_selected_table_row_index_list = stack.enter_context(
                patch("nnmm.process.video_play.ProcessBase.get_selected_table_row_index_list")
            )
            mock_selected_table_row_list = stack.enter_context(
                patch("nnmm.process.video_play.ProcessBase.get_selected_table_row_list")
            )

            instance = VideoPlay(self.process_info)

            DUMMY_EXE = "./tests/dummy.exe"
            dummy_path = Path(DUMMY_EXE)

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            def_data = self._make_table_data(mylist_url)

            def pre_run(s_values, is_cmd, is_watched):
                dummy_path.touch()
                s_def_data = deepcopy(def_data)
                mock_selected_table_row_index_list.reset_mock()
                if isinstance(s_values, int):

                    def f():
                        return SelectedTableRowIndexList.create([s_values])

                    mock_selected_table_row_index_list.side_effect = f
                else:

                    def f():
                        return SelectedTableRowIndexList.create([])

                    mock_selected_table_row_index_list.side_effect = f

                mock_selected_table_row_list.reset_mock()
                COLS_LENGTH = 9
                s_def_data = [[i + 1] + r[1:COLS_LENGTH] for i, r in enumerate(s_def_data)]
                if isinstance(s_values, int):
                    STATUS_INDEX = 4
                    if is_watched:
                        s_def_data[s_values][STATUS_INDEX] = "未視聴"
                    else:
                        s_def_data[s_values][STATUS_INDEX] = ""

                    def f():
                        return SelectedTableRowList.create(s_def_data)

                    mock_selected_table_row_list.side_effect = f

                instance.mylist_info_db.reset_mock()

                def f(video_id):
                    return self._get_mylist_info_from_video_id(s_def_data, video_id)

                instance.mylist_info_db.select_from_video_id.side_effect = f

                mock_config.reset_mock()
                if is_cmd:
                    dummy_path.touch()

                    def f(key, default):
                        return dummy_path

                    mock_config.return_value.__getitem__.return_value.get.side_effect = f
                else:

                    def f(key, default):
                        return ""

                    mock_config.return_value.__getitem__.return_value.get.side_effect = f
                mock_execute.reset_mock()
                mock_popup.reset_mock()
                mock_watched.reset_mock()

            def post_run(s_values, is_cmd, is_watched):
                dummy_path.unlink(missing_ok=True)
                self.assertEqual([call()], mock_selected_table_row_index_list.mock_calls)
                if not isinstance(s_values, int):
                    mock_selected_table_row_list.assert_not_called()
                    instance.mylist_info_db.assert_not_called()
                    mock_config.assert_not_called()
                    mock_execute.assert_not_called()
                    mock_popup.assert_not_called()
                    mock_watched.assert_not_called()
                    return

                self.assertEqual(
                    [
                        call(),
                    ],
                    mock_selected_table_row_list.mock_calls,
                )

                s_def_data = deepcopy(def_data)
                video_id = s_def_data[s_values][1]
                self.assertEqual([call.select_from_video_id(video_id)], instance.mylist_info_db.mock_calls)

                self.assertEqual(
                    [call(), call().__getitem__("general"), call().__getitem__().get("browser_path", "")],
                    mock_config.mock_calls,
                )
                if is_cmd:
                    table_dict = self._convert_table_data_to_dict(s_def_data)
                    video_url = table_dict[s_values].get("video_url")
                    mock_execute.assert_called_once_with(dummy_path, video_url)
                    mock_popup.assert_not_called()
                else:
                    mock_execute.assert_not_called()
                    mock_popup.assert_called_once_with("ブラウザパスが不正です。設定タブから設定してください。")
                    return

                if is_watched:
                    self.assertEqual([call(instance.process_info), call().run()], mock_watched.mock_calls)
                else:
                    mock_watched.assert_not_called()

            Params = namedtuple("Params", ["s_values", "is_cmd", "is_watched", "result"])
            params_list = [
                Params(0, True, True, Result.success),
                Params(0, True, False, Result.success),
                Params(0, False, True, Result.failed),
                Params("invalid", True, True, Result.failed),
            ]
            for params in params_list:
                pre_run(params.s_values, params.is_cmd, params.is_watched)
                actual = instance.run()
                expect = params.result
                self.assertIs(expect, actual)
                post_run(params.s_values, params.is_cmd, params.is_watched)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
