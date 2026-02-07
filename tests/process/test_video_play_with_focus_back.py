import sys
import unittest
from collections import namedtuple

from mock import MagicMock, call, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row_index_list import SelectedTableRowIndexList
from nnmm.process.value_objects.table_row_list import SelectedTableRowList
from nnmm.process.video_play_with_focus_back import VideoPlayWithFocusBack
from nnmm.util import Result


class TestVideoPlayWithFocusBack(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.video_play_with_focus_back.logger.info"))
        self.enterContext(patch("nnmm.process.video_play_with_focus_back.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> VideoPlayWithFocusBack:
        instance = VideoPlayWithFocusBack(self.process_info)
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
                "2026-02-07 02:30:00",
                "2026-02-07 02:30:00",
                "2026-02-07 02:30:00",
                "15分",
                True,
            ]
            for i in range(NUM)
        ]

        for row in rows:
            d = {}
            for r, c in zip(row, col):
                d[c] = r
            res.append(d)
        return res

    def _make_table_row_list(self, mylist_url) -> list[list[str]]:
        """テーブル情報動画データセット"""
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
        ]
        for k in range(NUM):
            for i in range(NUM):
                # MylistInfo + showname系
                number = i + (k * NUM) + 1
                video_id = f"sm{k + 1}000000{i + 1}"
                title = f"動画タイトル{k + 1}_{i + 1}"
                username = f"投稿者{k + 1}"
                status = "未視聴"
                uploaded_at = f"2026-02-02 0{k + 1}:00:0{i + 1}"
                registered_at = f"2026-02-03 0{k + 1}:00:0{i + 1}"
                video_url = f"https://www.nicovideo.jp/watch/sm{k + 1}000000{i + 1}"
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
                ]
                res.append(table_rows)
        return res

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(self.process_info, instance.process_info)

    def test_component(self):
        instance = self._get_instance()
        actual = instance.create_component()
        self.assertIsNone(actual)

    def test_callback(self) -> Result:
        mock_config = self.enterContext(
            patch("nnmm.process.video_play_with_focus_back.process_config.ConfigBase.get_config")
        )
        mock_subprocess = self.enterContext(patch("nnmm.process.video_play_with_focus_back.subprocess.run"))
        mock_popup = self.enterContext(patch("nnmm.process.video_play_with_focus_back.popup"))
        mock_watched = self.enterContext(patch("nnmm.process.video_play_with_focus_back.Watched"))
        self.enterContext(patch("nnmm.process.video_play_with_focus_back.sleep"))
        self.enterContext(patch("nnmm.process.video_play_with_focus_back.Path"))
        Params = namedtuple(
            "Params",
            [
                "kind_get_selected_table_row_index_list",
                "kind_browser_path",
                "is_watched",
                "result",
            ],
        )

        def pre_run(params: Params) -> VideoPlayWithFocusBack:
            instance = self._get_instance()
            instance.get_selected_table_row_index_list = MagicMock()
            instance.get_selected_table_row_list = MagicMock()
            instance.mylist_info_db = MagicMock()
            instance.window = MagicMock()
            mock_config.reset_mock()
            mock_subprocess.reset_mock()
            mock_popup.reset_mock()
            mock_watched.reset_mock()

            if params.kind_get_selected_table_row_index_list == "valid":
                instance.get_selected_table_row_index_list.return_value = SelectedTableRowIndexList.create([0])
            else:  # "invalid"
                instance.get_selected_table_row_index_list.return_value = None

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            selected_table_row = self._make_table_row_list(mylist_url)[0]
            selected_table_row[4] = "" if params.is_watched else "未視聴"
            instance.get_selected_table_row_list.return_value = SelectedTableRowList.create([selected_table_row])

            if params.kind_browser_path == "valid":
                mock_config.return_value = {"general": {"browser_path": "valid_browser_path"}}
            else:  # "invalid"
                mock_config.return_value = {"general": {"browser_path": ""}}

            return instance

        def post_run(actual: Result, instance: VideoPlayWithFocusBack, params: Params) -> None:
            self.assertEqual(params.result, actual)
            instance.get_selected_table_row_index_list.assert_called_once_with()
            if params.kind_get_selected_table_row_index_list == "valid":
                pass
            else:  # "invalid"
                instance.get_selected_table_row_list.assert_not_called()
                instance.mylist_info_db.assert_not_called()
                instance.window.assert_not_called()
                mock_config.assert_not_called()
                mock_subprocess.assert_not_called()
                mock_popup.assert_not_called()
                mock_watched.assert_not_called()
                return

            instance.get_selected_table_row_list.assert_called_once_with()
            instance.mylist_info_db.select_from_video_id.assert_called()

            mock_config.assert_called_once_with()
            if params.kind_browser_path == "valid":
                video_url = (
                    instance.mylist_info_db.select_from_video_id.return_value.__getitem__.return_value.get.return_value
                )
                mock_subprocess.assert_called_once_with(["valid_browser_path", video_url])
                instance.window.activateWindow.assert_called_once_with()
                mock_popup.assert_not_called()
            else:  # "invalid"
                mock_subprocess.assert_not_called()
                instance.window.assert_not_called()
                mock_popup.assert_called_once_with("ブラウザパスが不正です。設定タブから設定してください。")
                return

            if params.is_watched:
                mock_watched.assert_not_called()
            else:  # "invalid"
                self.assertEqual([call(instance.process_info), call().callback()], mock_watched.mock_calls)

        params_list = [
            Params("valid", "valid", True, Result.success),
            Params("valid", "valid", False, Result.success),
            Params("valid", "invalid", True, Result.failed),
            Params("invalid", "valid", True, Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
