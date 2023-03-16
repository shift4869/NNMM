# coding: utf-8
"""PopupWindowMain のテスト
"""
import copy
import sys
import unittest
from contextlib import ExitStack
from logging import WARNING, getLogger

import PySimpleGUI as sg
from mock import MagicMock, call, patch

from NNMM.PopupWindowMain import PopupMylistWindow, PopupMylistWindowSave, PopupVideoWindow, PopupWindowBase

logger = getLogger("NNMM.PopupWindowMain")
logger.setLevel(WARNING)


# テスト用具体化PopupWindowBase
class ConcretePopupWindowBase(PopupWindowBase):
    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None) -> None:
        super().__init__(log_sflag, log_eflag, process_name)

    def make_window_layout(self, mw) -> list[list[sg.Frame]] | None:
        return mw

    def init(self, mw) -> int:
        return mw

    def run(self, mw) -> int:
        return super().run(mw) if self.process_name == "テスト用具体化処理" else None


class TestPopupWindowMain(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PopupWindowBaseinit(self):
        """PopupWindowMainの初期化後の状態をテストする
        """
        e_log_sflag = True
        e_log_eflag = False
        e_process_name = "テスト用具体化処理"
        cpwb = ConcretePopupWindowBase(e_log_sflag, e_log_eflag, e_process_name)

        self.assertEqual(e_log_sflag, cpwb.log_sflag)
        self.assertEqual(e_log_eflag, cpwb.log_eflag)
        self.assertEqual(e_process_name, cpwb.process_name)

        self.assertEqual(None, cpwb.window)
        self.assertEqual("", cpwb.title)
        self.assertEqual((100, 100), cpwb.size)
        self.assertEqual({}, cpwb.process_dict)

    def test_PopupWindowBaserun(self):
        """PopupWindowMainの子windowイベントループをテストする
        """
        e_log_sflag = True
        e_log_eflag = False
        e_process_name = "テスト用具体化処理"
        cpwb = ConcretePopupWindowBase(e_log_sflag, e_log_eflag, e_process_name)
        cpwb.process_dict = {"-DO-": MagicMock}

        with ExitStack() as stack:
            mock_logger_info = stack.enter_context(patch.object(logger, "info"))
            mock_window = stack.enter_context(patch("NNMM.PopupWindowMain.sg.Window"))
            mock_popup_ok = stack.enter_context(patch("NNMM.PopupWindowMain.sg.popup_ok"))

            mock_window.return_value.read.side_effect = [("-DO-", "value1"), ("-EXIT-", "value2")]

            # 正常系
            e_mw = [["dummy window layout"]]
            res = cpwb.run(e_mw)
            self.assertEqual(0, res)
            expect = [
                call(cpwb.title, cpwb.make_window_layout(e_mw), size=cpwb.size, finalize=True, resizable=True, modal=True),
                call().read(),
                call().read(),
                call().close(),
            ]
            self.assertEqual(expect, mock_window.mock_calls)

            # 異常系
            # レイアウト作成に失敗
            e_mw = None
            res = cpwb.run(e_mw)
            self.assertEqual(-1, res)

            # 初期化に失敗
            e_mw = -1
            res = cpwb.run(e_mw)
            self.assertEqual(-1, res)
        pass

    def test_PMWmake_window_layout(self):
        """マイリスト情報windowのレイアウトをテストする
        """
        pmw = PopupMylistWindow()

        e_record = {
            "id": 0,
            "username": "投稿者1",
            "mylistname": "マイリスト名1",
            "type": "mylist",
            "showname": "「マイリスト名1」-投稿者1さんのマイリスト",
            "url": "https://www.nicovideo.jp/user/11111111/mylist/10000011",
            "created_at": "21-11-11 01:00:00",
            "updated_at": "21-11-11 01:00:20",
            "checked_at": "21-11-11 01:00:10",
            "check_interval": "15分",
            "is_include_new": True,
        }
        pmw.record = copy.deepcopy(e_record)

        title = "マイリスト情報"
        pmw.title = title

        def expect_make_window_layout(mw):
            # 画面のレイアウトを作成する
            horizontal_line = "-" * 132
            csize = (20, 1)
            tsize = (50, 1)
            thsize = (5, 1)

            r = e_record
            id_index = r["id"]
            username = r["username"]
            mylistname = r["mylistname"]
            typename = r["type"]
            showname = r["showname"]
            url = r["url"]
            created_at = r["created_at"]
            updated_at = r["updated_at"]
            checked_at = r["checked_at"]
            is_include_new = "True" if r["is_include_new"] else "False"

            # インターバル文字列をパース
            unit_list = ["分", "時間", "日", "週間", "ヶ月"]
            check_interval = r["check_interval"]
            t = str(check_interval)
            for u in unit_list:
                t = t.replace(u, "")
            check_interval_num = int(t)
            check_interval_unit = str(check_interval).replace(str(t), "")

            cf = [
                [sg.Text(horizontal_line)],
                [sg.Text("ID", size=csize, visible=False), sg.Input(f"{id_index}", key="-ID_INDEX-", visible=False, readonly=True, size=tsize)],
                [sg.Text("ユーザー名", size=csize), sg.Input(f"{username}", key="-USERNAME-", readonly=True, size=tsize)],
                [sg.Text("マイリスト名", size=csize), sg.Input(f"{mylistname}", key="-MYLISTNAME-", readonly=True, size=tsize)],
                [sg.Text("種別", size=csize), sg.Input(f"{typename}", key="-TYPE-", readonly=True, size=tsize)],
                [sg.Text("表示名", size=csize), sg.Input(f"{showname}", key="-SHOWNAME-", readonly=True, size=tsize)],
                [sg.Text("URL", size=csize), sg.Input(f"{url}", key="-URL-", readonly=True, size=tsize)],
                [sg.Text("作成日時", size=csize), sg.Input(f"{created_at}", key="-CREATED_AT-", readonly=True, size=tsize)],
                [sg.Text("更新日時", size=csize), sg.Input(f"{updated_at}", key="-UPDATED_AT-", readonly=True, size=tsize)],
                [sg.Text("更新確認日時", size=csize), sg.Input(f"{checked_at}", key="-CHECKED_AT-", readonly=True, size=tsize)],
                [sg.Text("更新確認インターバル", size=csize),
                    sg.InputCombo([i for i in range(1, 60)], default_value=check_interval_num, key="-CHECK_INTERVAL_NUM-", background_color="light goldenrod", size=thsize),
                    sg.InputCombo(unit_list, default_value=check_interval_unit, key="-CHECK_INTERVAL_UNIT-", background_color="light goldenrod", size=thsize)],
                [sg.Text("未視聴フラグ", size=csize), sg.Input(f"{is_include_new}", key="-IS_INCLUDE_NEW-", readonly=True, size=tsize)],
                [sg.Text(horizontal_line)],
                [sg.Text("")],
                [sg.Text("")],
                [sg.Column([[sg.Button("保存", key="-SAVE-"), sg.Button("閉じる", key="-EXIT-")]], justification="right")],
            ]
            layout = [[
                sg.Frame(title, cf)
            ]]
            return layout

        # 正常系
        mw = None
        actual = pmw.make_window_layout(mw)
        expect = expect_make_window_layout(mw)

        # sgオブジェクトは別IDで生成されるため、各要素を比較する
        # self.assertEqual(expect, actual)
        self.assertEqual(type(expect), type(actual))
        self.assertEqual(len(expect), len(actual))
        for e1, a1 in zip(expect, actual):
            self.assertEqual(len(e1), len(a1))
            for e2, a2 in zip(e1, a1):
                for e3, a3 in zip(e2.Rows, a2.Rows):
                    self.assertEqual(len(e3), len(a3))
                    for e4, a4 in zip(e3, a3):
                        if hasattr(a4, "DisplayText") and a4.DisplayText:
                            self.assertEqual(e4.DisplayText, a4.DisplayText)
                        if hasattr(a4, "Key") and a4.Key:
                            self.assertEqual(e4.Key, a4.Key)

        # 異常系
        # インターバル文字列が不正な文字列
        pmw.record["check_interval"] = "不正なインターバル文字列"
        actual = pmw.make_window_layout(mw)
        self.assertIsNone(actual)

        # インターバル文字列が負の数指定
        pmw.record["check_interval"] = "-15分"
        actual = pmw.make_window_layout(mw)
        self.assertIsNone(actual)
        pmw.record["check_interval"] = "15分"

        # recordの設定が不完全
        del pmw.record["id"]
        actual = pmw.make_window_layout(mw)
        self.assertIsNone(actual)

        # recordが設定されていない
        del pmw.record
        actual = pmw.make_window_layout(mw)
        self.assertIsNone(actual)
        pass

    def test_PMWinit(self):
        """マイリスト情報windowの初期化処理をテストする
        """
        with ExitStack() as stack:
            mock_logger_error = stack.enter_context(patch.object(logger, "error"))

            pmw = PopupMylistWindow()

            NEW_MARK = "*:"
            mw = MagicMock()
            sfs_mock = MagicMock()
            type(sfs_mock).select_from_showname = lambda s, v: [v]
            type(mw).mylist_db = sfs_mock
            type(mw).mylist_info_db = "mylist_info_db"
            type(mw).values = {"-LIST-": [f"{NEW_MARK}mylist showname"]}

            # 正常系
            actual = pmw.init(mw)
            self.assertEqual(0, actual)
            self.assertEqual("mylist showname", pmw.record)
            self.assertEqual("マイリスト情報", pmw.title)
            self.assertEqual((580, 450), pmw.size)
            self.assertEqual({"-SAVE-": PopupMylistWindowSave}, pmw.process_dict)

            # 異常系
            # マイリストレコードオブジェクト取得失敗
            type(sfs_mock).select_from_showname = lambda s, v: []
            actual = pmw.init(mw)
            self.assertEqual(-1, actual)

            # 選択されたマイリストのShowname取得失敗
            type(mw).values = {"-LIST-": []}
            actual = pmw.init(mw)
            self.assertEqual(-1, actual)

            # 親windowが必要な属性を持っていない
            del type(mw).mylist_db
            del mw.mylist_db
            actual = pmw.init(mw)
            self.assertEqual(-1, actual)
        pass

    def test_PMWSrun(self):
        """マイリスト情報windowの変更を保存する機能をテストする
        """
        with ExitStack() as stack:
            mock_logger_info = stack.enter_context(patch.object(logger, "info"))
            mock_logger_error = stack.enter_context(patch.object(logger, "error"))
            pmw = PopupMylistWindowSave()

            def getmock(value):
                r = MagicMock()
                type(r).get = lambda s: value
                return r

            expect_window_dict = {
                "-ID_INDEX-": 0,
                "-USERNAME-": "投稿者1",
                "-MYLISTNAME-": "マイリスト名1",
                "-TYPE-": "mylist",
                "-SHOWNAME-": "「マイリスト名1」-投稿者1さんのマイリスト",
                "-URL-": "https://www.nicovideo.jp/user/11111111/mylist/10000011",
                "-CREATED_AT-": "21-11-11 01:00:00",
                "-UPDATED_AT-": "21-11-11 01:00:20",
                "-CHECKED_AT-": "21-11-11 01:00:10",
                "-IS_INCLUDE_NEW-": True,
                "-CHECK_INTERVAL_NUM-": 15,
                "-CHECK_INTERVAL_UNIT-": "分",
            }
            for k, v in expect_window_dict.items():
                expect_window_dict[k] = getmock(v)

            mockwm = MagicMock()
            mockwin = MagicMock()
            mockakd = MagicMock()
            type(mockakd).keys = expect_window_dict.keys
            type(mockwin).AllKeysDict = mockakd
            mockwin.__getitem__.side_effect = expect_window_dict.__getitem__
            mockwin.__iter__.side_effect = expect_window_dict.__iter__
            mockwin.__contains__.side_effect = expect_window_dict.__contains__
            type(mockwm).window = mockwin
            type(mockwm).values = []

            def mockUpsert(s, id_index, username, mylistname, typename, showname, url, created_at, updated_at, checked_at, check_interval, is_include_new):
                return 0

            mockmb = MagicMock()
            type(mockmb).Upsert = mockUpsert
            type(mockwm).mylist_db = mockmb
            type(mockwm).mylist_info_db = []

            # 正常系
            actual = pmw.run(mockwm)
            self.assertEqual(0, actual)

            # 異常系
            # インターバル文字列が不正な値
            expect_window_dict["-CHECK_INTERVAL_UNIT-"] = getmock("不正な時間単位")
            actual = pmw.run(mockwm)
            self.assertEqual(-1, actual)

            # レイアウトに想定しているキーが存在しない
            del expect_window_dict["-CHECK_INTERVAL_UNIT-"]
            actual = pmw.run(mockwm)
            self.assertEqual(-1, actual)

            # 引数のwindowが必要な属性を持っていない
            del type(mockwm).mylist_db
            del mockwm.mylist_db
            actual = pmw.run(mockwm)
            self.assertEqual(-1, actual)
        pass

    def test_PVWmake_window_layout(self):
        """動画情報windowのレイアウトをテストする
        """
        pvw = PopupVideoWindow()

        e_record = {
            "id": 0,
            "video_id": "sm11111111",
            "title": "動画タイトル1",
            "username": "投稿者1",
            "status": "未視聴",
            "uploaded_at": "2021-05-29 22:00:11",
            "registered_at": "2021-05-29 22:01:11",
            "video_url": "https://www.nicovideo.jp/watch/sm11111111",
            "mylist_url": "https://www.nicovideo.jp/user/11111111/mylist/12345678",
            "created_at": "2021-10-16 00:00:11",
        }
        pvw.record = copy.deepcopy(e_record)

        title = "動画情報"
        pvw.title = title

        def expect_make_window_layout(mw):
            # 画面のレイアウトを作成する
            horizontal_line = "-" * 132
            csize = (20, 1)
            tsize = (50, 1)

            r = e_record
            id_index = r["id"]
            video_id = r["video_id"]
            title = r["title"]
            username = r["username"]
            status = r["status"]
            uploaded_at = r["uploaded_at"]
            registered_at = r["registered_at"]
            video_url = r["video_url"]
            mylist_url = r["mylist_url"]
            created_at = r["created_at"]

            cf = [
                [sg.Text(horizontal_line)],
                [sg.Text("ID", size=csize, visible=False), sg.Input(f"{id_index}", key="-ID_INDEX-", visible=False, readonly=True, size=tsize)],
                [sg.Text("動画ID", size=csize), sg.Input(f"{video_id}", key="-USERNAME-", readonly=True, size=tsize)],
                [sg.Text("動画名", size=csize), sg.Input(f"{title}", key="-MYLISTNAME-", readonly=True, size=tsize)],
                [sg.Text("投稿者", size=csize), sg.Input(f"{username}", key="-TYPE-", readonly=True, size=tsize)],
                [sg.Text("状況", size=csize), sg.Input(f"{status}", key="-SHOWNAME-", readonly=True, size=tsize)],
                [sg.Text("投稿日時", size=csize), sg.Input(f"{uploaded_at}", key="-URL-", readonly=True, size=tsize)],
                [sg.Text("登録日時", size=csize), sg.Input(f"{registered_at}", key="-URL-", readonly=True, size=tsize)],
                [sg.Text("動画URL", size=csize), sg.Input(f"{video_url}", key="-CREATED_AT-", readonly=True, size=tsize)],
                [sg.Text("マイリストURL", size=csize), sg.Input(f"{mylist_url}", key="-UPDATED_AT-", readonly=True, size=tsize)],
                [sg.Text("作成日時", size=csize), sg.Input(f"{created_at}", key="-CHECKED_AT-", readonly=True, size=tsize)],
                [sg.Text(horizontal_line)],
                [sg.Text("")],
                [sg.Column([[sg.Button("閉じる", key="-EXIT-")]], justification="right")],
            ]
            layout = [[
                sg.Frame(title, cf)
            ]]
            return layout

        # 正常系
        mw = None
        actual = pvw.make_window_layout(mw)
        expect = expect_make_window_layout(mw)

        # sgオブジェクトは別IDで生成されるため、各要素を比較する
        # self.assertEqual(expect, actual)
        self.assertEqual(type(expect), type(actual))
        self.assertEqual(len(expect), len(actual))
        for e1, a1 in zip(expect, actual):
            self.assertEqual(len(e1), len(a1))
            for e2, a2 in zip(e1, a1):
                for e3, a3 in zip(e2.Rows, a2.Rows):
                    self.assertEqual(len(e3), len(a3))
                    for e4, a4 in zip(e3, a3):
                        if hasattr(a4, "DisplayText") and a4.DisplayText:
                            self.assertEqual(e4.DisplayText, a4.DisplayText)
                        if hasattr(a4, "Key") and a4.Key:
                            self.assertEqual(e4.Key, a4.Key)

        # 異常系
        # recordの設定が不完全
        del pvw.record["id"]
        actual = pvw.make_window_layout(mw)
        self.assertIsNone(actual)

        # recordが設定されていない
        del pvw.record
        actual = pvw.make_window_layout(mw)
        self.assertIsNone(actual)

    def test_PVWinit(self):
        """動画情報windowの初期化処理をテストする
        """
        with ExitStack() as stack:
            mock_logger_info = stack.enter_context(patch.object(logger, "info"))
            mock_logger_error = stack.enter_context(patch.object(logger, "error"))

            pvw = PopupVideoWindow()

            e_video_id = "sm11111111"
            e_mylist_url = "https://www.nicovideo.jp/user/11111111/mylist/12345678"
            e_tv = [
                0,
                e_video_id,
                "動画タイトル1",
                "投稿者1",
                "未視聴",
                "2021-05-29 22:00:11",
                "2021-05-29 22:01:11",
                "https://www.nicovideo.jp/watch/sm11111111",
                e_mylist_url,
                "2021-10-16 00:00:11",
            ]
            mw = MagicMock()
            mock_table = MagicMock()
            mock_table.Values = [e_tv]
            mw.window = {"-TABLE-": mock_table}
            mw.values = {"-TABLE-": [0]}
            mock_mylist_info_db = MagicMock()
            mock_mylist_info_db.select_from_id_url.side_effect = lambda video_id, mylist_url: [video_id + "_" + mylist_url]
            mw.mylist_info_db = mock_mylist_info_db
            mw.mylist_db = "mylist_db"

            # 正常系
            actual = pvw.init(mw)
            self.assertEqual(0, actual)
            self.assertEqual(f"{e_video_id}_{e_mylist_url}", pvw.record)
            self.assertEqual("動画情報", pvw.title)
            self.assertEqual((580, 400), pvw.size)

            # 異常系
            # 動画情報レコードオブジェクト取得失敗
            mock_mylist_info_db.select_from_id_url.side_effect = lambda video_id, mylist_url: []
            actual = pvw.init(mw)
            self.assertEqual(-1, actual)

            # テーブルの行が選択されていない
            mw.values = {"-TABLE-": None}
            actual = pvw.init(mw)
            self.assertEqual(-1, actual)

            # 引数が不正
            mw.values = None
            actual = pvw.init(mw)
            self.assertEqual(-1, actual)

            # 親windowが必要な属性を持っていない
            del mw.mylist_info_db
            actual = pvw.init(mw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
