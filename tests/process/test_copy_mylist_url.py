import sys
import unittest
from collections import namedtuple

from mock import MagicMock, patch
from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.copy_mylist_url import CopyMylistUrl
from nnmm.process.value_objects.mylist_row import SelectedMylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result


class TestCopyMylistUrl(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("nnmm.process.copy_mylist_url.logger.info"))
        self.enterContext(patch("nnmm.process.copy_mylist_url.logger.error"))
        self.process_info = MagicMock(spec=ProcessInfo)
        self.process_info.name = "-TEST_PROCESS-"
        self.process_info.window = MagicMock(spec=QDialog)
        self.process_info.mylist_db = MagicMock(spec=MylistDBController)
        self.process_info.mylist_info_db = MagicMock(spec=MylistInfoDBController)

    def _get_instance(self) -> CopyMylistUrl:
        instance = CopyMylistUrl(self.process_info)
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
        mock_pyperclip = self.enterContext(patch("nnmm.process.copy_mylist_url.pyperclip.copy"))
        Params = namedtuple(
            "Params",
            [
                "kind_get_selected_mylist_row",
                "result",
            ],
        )

        def pre_run(params: Params) -> CopyMylistUrl:
            instance = self._get_instance()
            instance.get_selected_mylist_row = MagicMock()
            instance.set_bottom_textbox = MagicMock()
            instance.mylist_db = MagicMock()
            mock_pyperclip.reset_mock()

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            showname = m_list[0]["showname"]
            if params.kind_get_selected_mylist_row == "valid":
                instance.get_selected_mylist_row.return_value = SelectedMylistRow.create(showname)
            else:  # "invalid"
                instance.get_selected_mylist_row.return_value = None

            instance.mylist_db.select_from_showname.return_value = [{"url": mylist_url}]

            return instance

        def post_run(actual: Result, instance: CopyMylistUrl, params: Params) -> None:
            self.assertEqual(params.result, actual)
            instance.get_selected_mylist_row.assert_called_once_with()
            if params.kind_get_selected_mylist_row == "valid":
                pass
            else:  # "invalid"
                instance.set_bottom_textbox.assert_not_called()
                instance.mylist_db.assert_not_called()
                mock_pyperclip.assert_not_called()
                return

            m_list = self._make_mylist_db()
            mylist_url = m_list[0]["url"]
            showname = m_list[0]["showname"]
            instance.mylist_db.select_from_showname.assert_called_once_with(showname)

            mock_pyperclip.assert_called_once_with(mylist_url)
            instance.set_bottom_textbox.assert_called_once_with("マイリストURLコピー成功！")

        params_list = [
            Params("valid", Result.success),
            Params("invalid", Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.callback()
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
