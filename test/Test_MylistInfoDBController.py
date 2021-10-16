# coding: utf-8
"""MylistInfoDBControllerのテスト

MylistInfoDBController.MylistInfoDBController()の各種機能をテストする
"""

import copy
import re
import random
import sys
import time
import traceback
import unittest
import warnings
from contextlib import ExitStack
from datetime import date, datetime, timedelta
from logging import WARNING, getLogger
from mock import MagicMock, PropertyMock, patch
from pathlib import Path

from sqlalchemy import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM.Model import *
from NNMM.MylistInfoDBController import *

logger = getLogger("root")
logger.setLevel(WARNING)
TEST_DB_FULLPATH = "./test/test.db"


class TestMylistInfoDBController(unittest.TestCase):
    """テストメインクラス
    """

    def setUp(self):
        # self.engine = create_engine("sqlite:///:memory:", echo=False, pool_recycle=5, connect_args={"timeout": 30})
        # Base.metadata.create_all(self.engine)
        # Session = sessionmaker(bind=self.engine)
        # self.session = Session()
        if Path(TEST_DB_FULLPATH).is_file():
            Path(TEST_DB_FULLPATH).unlink()
        pass

    def tearDown(self):
        # if self.engine.url.database == ":memory:":
        #     Base.metadata.drop_all(self.engine)

        if Path(TEST_DB_FULLPATH).is_file():
            Path(TEST_DB_FULLPATH).unlink()
        pass

    def __MakeMylistInfoSample(self, id, mylist_id):
        """
            video_id (str): 動画ID(smxxxxxxxx)
            title (str): 動画タイトル
            username (str): 投稿者名
            status (str): 視聴状況({"未視聴", ""})
            uploaded_at (str): 動画投稿日時
            video_url (str): 動画URL
            mylist_url (str): 所属マイリストURL
            created_at (str): 作成日時
        """
        video_info = [
            ("sm11111111", "動画タイトル1", "投稿者1", "未視聴", "2021-05-29 22:00:11", "https://www.nicovideo.jp/watch/sm11111111", "2021-10-16 00:00:11"),
            ("sm22222222", "動画タイトル2", "投稿者1", "未視聴", "2021-05-29 22:00:22", "https://www.nicovideo.jp/watch/sm22222222", "2021-10-16 00:00:22"),
            ("sm33333333", "動画タイトル3", "投稿者1", "未視聴", "2021-05-29 22:00:33", "https://www.nicovideo.jp/watch/sm33333333", "2021-10-16 00:00:33"),
            ("sm44444444", "動画タイトル4", "投稿者2", "未視聴", "2021-05-29 22:00:44", "https://www.nicovideo.jp/watch/sm44444444", "2021-10-16 00:00:44"),
            ("sm55555555", "動画タイトル5", "投稿者2", "未視聴", "2021-05-29 22:00:55", "https://www.nicovideo.jp/watch/sm55555555", "2021-10-16 00:00:55"),
        ]
        mylist_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/11111111/mylist/12345678",
            "https://www.nicovideo.jp/user/22222222/video",
        ]

        v = video_info[id]
        mylist_url = mylist_info[mylist_id]
        r = MylistInfo(v[0], v[1], v[2], v[3], v[4], v[5], mylist_url, v[6])
        return r

    def test_Upsert(self):
        """MylistInfoにUPSERTする機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistInfoDBController.MylistInfoDBController.Func"))
            mi_cont = MylistInfoDBController(TEST_DB_FULLPATH)

            # INSERT
            expect = []
            id_num = 1
            for i in range(0, 3):
                for j in range(0, 5):
                    r = self.__MakeMylistInfoSample(j, i)
                    res = mi_cont.Upsert(r.video_id, r.title, r.username, r.status, r.uploaded_at, r.video_url, r.mylist_url, r.created_at)
                    self.assertEqual(res, 0)

                    d = r.toDict()
                    d["id"] = id_num
                    id_num = id_num + 1
                    expect.append(d)
            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # UPDATE
            # idをランダムに選定し、statusを更新する
            t_id = random.sample(range(0, 15), 5)
            for i in t_id:
                expect[i]["status"] = ""
                r = expect[i]
                res = mi_cont.Upsert(r["video_id"], r["title"], r["username"], r["status"], r["uploaded_at"], r["video_url"], r["mylist_url"], r["created_at"])
                self.assertEqual(res, 1)
            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)
            pass

    def test_UpsertFromList(self):
        """MylistInfoにListからまとめて受け取りUPSERTする機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistInfoDBController.MylistInfoDBController.Func"))
            mi_cont = MylistInfoDBController(TEST_DB_FULLPATH)

            # INSERT
            expect = []
            records = []
            id_num = 1
            for i in range(0, 3):
                for j in range(0, 5):
                    r = self.__MakeMylistInfoSample(j, i)
                    d = r.toDict()
                    del d["id"]
                    records.append(d)

                    d = r.toDict()
                    d["id"] = id_num
                    id_num = id_num + 1
                    expect.append(d)

            res = mi_cont.UpsertFromList(records)
            self.assertEqual(res, 0)

            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 引数再設定
            records = copy.deepcopy(expect)
            for record in records:
                del record["id"]

            # UPDATE
            # idをランダムに選定し、statusを更新する
            t_id = random.sample(range(0, 15), 5)
            for i in t_id:
                expect[i]["status"] = ""
                records[i]["status"] = ""

            res = mi_cont.UpsertFromList(records)
            self.assertEqual(res, 1)

            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)
            pass

    def test_UpdateStatus(self):
        """MylistInfoの特定のレコードについてstatusを更新する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistInfoDBController.MylistInfoDBController.Func"))
            mi_cont = MylistInfoDBController(TEST_DB_FULLPATH)

            # INSERT
            expect = []
            id_num = 1
            for i in range(0, 3):
                for j in range(0, 5):
                    r = self.__MakeMylistInfoSample(j, i)
                    res = mi_cont.Upsert(r.video_id, r.title, r.username, r.status, r.uploaded_at, r.video_url, r.mylist_url, r.created_at)
                    self.assertEqual(res, 0)

                    d = r.toDict()
                    d["id"] = id_num
                    id_num = id_num + 1
                    expect.append(d)
            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # UPDATE
            # idをランダムに選定し、statusを更新する
            t_id = random.sample(range(0, 15), 5)
            for i in t_id:
                expect[i]["status"] = ""
                r = expect[i]
                res = mi_cont.UpdateStatus(r["video_id"], r["mylist_url"], "")
                self.assertEqual(res, 0)
            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないレコードを指定する
            res = mi_cont.UpdateStatus("sm99999999", "https://www.nicovideo.jp/watch/sm11111111", "")
            self.assertEqual(res, 1)

            # video_idの形式が不正
            res = mi_cont.UpdateStatus("nm99999999", "https://www.nicovideo.jp/watch/sm11111111", "")
            self.assertEqual(res, -1)

            # statusが不正
            r = expect[0]
            res = mi_cont.UpdateStatus(r["video_id"], r["mylist_url"], "不正なステータス")
            self.assertEqual(res, -1)
            pass

    def test_UpdateStatusInMylist(self):
        """MylistInfoについて特定のマイリストに含まれるレコードのstatusをすべて更新する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistInfoDBController.MylistInfoDBController.Func"))
            mi_cont = MylistInfoDBController(TEST_DB_FULLPATH)

            # INSERT
            expect = []
            id_num = 1
            for i in range(0, 3):
                for j in range(0, 5):
                    r = self.__MakeMylistInfoSample(j, i)
                    res = mi_cont.Upsert(r.video_id, r.title, r.username, r.status, r.uploaded_at, r.video_url, r.mylist_url, r.created_at)
                    self.assertEqual(res, 0)

                    d = r.toDict()
                    d["id"] = id_num
                    id_num = id_num + 1
                    expect.append(d)
            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # UPDATE
            # 特定のマイリストに含まれるレコードのstatusを更新する
            mylist_info = [
                "https://www.nicovideo.jp/user/11111111/video",
                "https://www.nicovideo.jp/user/11111111/mylist/12345678",
                "https://www.nicovideo.jp/user/22222222/video",
            ]
            t_id = random.randint(0, 2)
            mylist_url = mylist_info[t_id]
            res = mi_cont.UpdateStatusInMylist(mylist_url, "")
            self.assertEqual(res, 0)

            for r in expect:
                if r["mylist_url"] == mylist_url:
                    r["status"] = ""
            expect = sorted(expect, key=lambda x: x["id"])

            actual = mi_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないマイリストを指定する
            res = mi_cont.UpdateStatusInMylist("https://www.nicovideo.jp/user/99999999/video")
            self.assertEqual(res, 1)

            # statusが不正
            r = expect[0]
            res = mi_cont.UpdateStatusInMylist(mylist_url, "不正なステータス")
            self.assertEqual(res, -1)
            pass

    def test_UpdateUsernameInMylist(self):
        """MylistInfoについて特定のマイリストに含まれるレコードのusernameをすべて更新する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistInfoDBController.MylistInfoDBController.Func"))
            mi_cont = MylistInfoDBController(TEST_DB_FULLPATH)

            # INSERT
            expect = []
            id_num = 1
            for i in range(0, 3):
                for j in range(0, 5):
                    r = self.__MakeMylistInfoSample(j, i)
                    res = mi_cont.Upsert(r.video_id, r.title, r.username, r.status, r.uploaded_at, r.video_url, r.mylist_url, r.created_at)
                    self.assertEqual(res, 0)

                    d = r.toDict()
                    d["id"] = id_num
                    id_num = id_num + 1
                    expect.append(d)
            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # UPDATE
            # 特定のマイリストに含まれるレコードのusernameを更新する
            mylist_info = [
                "https://www.nicovideo.jp/user/11111111/video",
                "https://www.nicovideo.jp/user/11111111/mylist/12345678",
                "https://www.nicovideo.jp/user/22222222/video",
            ]
            t_id = random.randint(0, 2)
            mylist_url = mylist_info[t_id]
            username = "新しい投稿者"
            res = mi_cont.UpdateUsernameInMylist(mylist_url, username)
            self.assertEqual(res, 0)

            for r in expect:
                if r["mylist_url"] == mylist_url:
                    r["username"] = username
            expect = sorted(expect, key=lambda x: x["id"])

            actual = mi_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないマイリストを指定する
            res = mi_cont.UpdateUsernameInMylist("https://www.nicovideo.jp/user/99999999/video", username)
            self.assertEqual(res, 1)
            pass

    def test_DeleteFromMylistURL(self):
        """MylistInfoについて特定のマイリストに含まれるレコードをすべて削除する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistInfoDBController.MylistInfoDBController.Func"))
            mi_cont = MylistInfoDBController(TEST_DB_FULLPATH)

            # INSERT
            expect = []
            id_num = 1
            for i in range(0, 3):
                for j in range(0, 5):
                    r = self.__MakeMylistInfoSample(j, i)
                    res = mi_cont.Upsert(r.video_id, r.title, r.username, r.status, r.uploaded_at, r.video_url, r.mylist_url, r.created_at)
                    self.assertEqual(res, 0)

                    d = r.toDict()
                    d["id"] = id_num
                    id_num = id_num + 1
                    expect.append(d)
            actual = mi_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # DELETE
            # 特定のマイリストに含まれるレコードを削除する
            mylist_info = [
                "https://www.nicovideo.jp/user/11111111/video",
                "https://www.nicovideo.jp/user/11111111/mylist/12345678",
                "https://www.nicovideo.jp/user/22222222/video",
            ]
            t_id = random.randint(0, 2)
            mylist_url = mylist_info[t_id]
            res = mi_cont.DeleteFromMylistURL(mylist_url)
            self.assertEqual(res, 0)

            expect = [e for e in expect if e["mylist_url"] != mylist_url]
            expect = sorted(expect, key=lambda x: x["id"])

            actual = mi_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないマイリストを指定する
            res = mi_cont.DeleteFromMylistURL("https://www.nicovideo.jp/user/99999999/video")
            self.assertEqual(res, 1)
            pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
