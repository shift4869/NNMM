# coding: utf-8
"""PopupWindowMain のテスト
"""

import copy
import shutil
import sys
import unittest
from contextlib import ExitStack
from logging import INFO, getLogger
from mock import MagicMock, patch, mock_open
from pathlib import Path

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase
from NNMM.PopupWindowMain import *


# テスト用具体化PopupWindowBase
class ConcretePopupWindowBase(PopupWindowBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None) -> None:
        super().__init__(log_sflag, log_eflag, process_name)

    def MakeWindowLayout(self, mw) -> list[list[sg.Frame]] | None:
        return mw

    def Init(self, mw) -> int:
        return 0

    def Run(self, mw) -> int:
        return super().Run(mw) if self.process_name == "テスト用具体化処理" else None


class TestPopupWindowMain(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PopupWindowBaseInit(self):
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
        self.assertEqual({}, cpwb.ep_dict)
        pass

    def test_PopupWindowBaseRun(self):
        """PopupWindowMainの子windowイベントループをテストする
        """
        e_log_sflag = True
        e_log_eflag = False
        e_process_name = "テスト用具体化処理"
        cpwb = ConcretePopupWindowBase(e_log_sflag, e_log_eflag, e_process_name)
        cpwb.ep_dict = {"-DO-": ConcretePopupWindowBase}

        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.PopupWindowMain.logger.info"))
            mockwd = stack.enter_context(patch("NNMM.PopupWindowMain.sg.Window"))

            def r_mock_func(title, layout, size, finalize, resizable, modal):
                r_mock = MagicMock()
                v_mock = MagicMock()
                v_mock.side_effect = [("-DO-", "value1"), ("-EXIT-", "value2")]
                type(r_mock).read = v_mock
                type(r_mock).close = lambda s: 0
                return r_mock

            mockwd.side_effect = r_mock_func

            # 正常系
            e_mw = [["dummy window"]]
            res = cpwb.Run(e_mw)
            self.assertEqual(0, res)

            # 異常系
            e_mw = None
            res = cpwb.Run(e_mw)
            self.assertEqual(-1, res)
        pass

    def test_PMWMakeWindowLayout(self):
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

        def ExpectMakeWindowLayout(mw):
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
        actual = pmw.MakeWindowLayout(mw)
        expect = ExpectMakeWindowLayout(mw)

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
        actual = pmw.MakeWindowLayout(mw)
        self.assertIsNone(actual)

        # インターバル文字列が負の数指定
        pmw.record["check_interval"] = "-15分"
        actual = pmw.MakeWindowLayout(mw)
        self.assertIsNone(actual)
        pmw.record["check_interval"] = "15分"

        # recordの設定が不完全
        del pmw.record["id"]
        actual = pmw.MakeWindowLayout(mw)
        self.assertIsNone(actual)

        # recordが設定されていない
        del pmw.record
        actual = pmw.MakeWindowLayout(mw)
        self.assertIsNone(actual)
        pass

    def test_PMWInit(self):
        """マイリスト情報windowの初期化処理をテストする
        """
        pmw = PopupMylistWindow()

        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.PopupWindowMain.logger.error"))

            NEW_MARK = "*:"
            mw = MagicMock()
            sfs_mock = MagicMock()
            type(sfs_mock).SelectFromShowname = lambda s, v: [v]
            type(mw).mylist_db = sfs_mock
            type(mw).mylist_info_db = "mylist_info_db"
            type(mw).values = {"-LIST-": [f"{NEW_MARK}mylist showname"]}

            # 正常系
            actual = pmw.Init(mw)
            self.assertEqual(0, actual)
            self.assertEqual("mylist showname", pmw.record)
            self.assertEqual("マイリスト情報", pmw.title)
            self.assertEqual((580, 450), pmw.size)
            self.assertEqual({"-SAVE-": PopupMylistWindowSave}, pmw.ep_dict)

            # 異常系
            # マイリストレコードオブジェクト取得失敗
            type(sfs_mock).SelectFromShowname = lambda s, v: []
            actual = pmw.Init(mw)
            self.assertEqual(-1, actual)

            # 選択されたマイリストのShowname取得失敗
            type(mw).values = {"-LIST-": []}
            actual = pmw.Init(mw)
            self.assertEqual(-1, actual)

            # 親windowが必要な属性を持っていない
            del type(mw).mylist_db
            del mw.mylist_db
            actual = pmw.Init(mw)
            self.assertEqual(-1, actual)

        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
