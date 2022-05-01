# coding: utf-8
"""MylistDBControllerのテスト

MylistDBController.MylistDBController()の各種機能をテストする
"""

import re
import random
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime
from logging import WARNING, getLogger
from mock import MagicMock, PropertyMock, patch
from pathlib import Path

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM.Model import *
from NNMM.MylistDBController import *

logger = getLogger("root")
logger.setLevel(WARNING)
TEST_DB_PATH = "./test/test.db"


class TestMylistDBController(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        Path(TEST_DB_PATH).unlink(missing_ok=True)
        pass

    def __GetMylistInfoSet(self) -> list[tuple]:
        """Mylistオブジェクトの情報セットを返す（mylist_url以外）
        """
        mylist_info = [
            (1, "投稿者1", "投稿動画", "uploaded", "投稿者1さんの投稿動画", "2021-05-29 00:00:11", "2021-10-16 00:00:11", "2021-10-17 00:00:11", "15分", False),
            (2, "投稿者2", "投稿動画", "uploaded", "投稿者2さんの投稿動画", "2021-05-29 00:00:22", "2021-10-16 00:00:22", "2021-10-17 00:00:22", "15分", False),
            (3, "投稿者1", "マイリスト1", "mylist", "「マイリスト1」-投稿者1さんのマイリスト", "2021-05-29 00:11:11", "2021-10-16 00:11:11", "2021-10-17 00:11:11", "15分", False),
            (4, "投稿者1", "マイリスト2", "mylist", "「マイリスト2」-投稿者1さんのマイリスト", "2021-05-29 00:22:11", "2021-10-16 00:22:11", "2021-10-17 00:22:11", "15分", False),
            (5, "投稿者3", "マイリスト3", "mylist", "「マイリスト3」-投稿者3さんのマイリスト", "2021-05-29 00:11:33", "2021-10-16 00:11:33", "2021-10-17 00:11:33", "15分", False),
        ]
        return mylist_info

    def __GetURLInfoSet(self) -> list[str]:
        """mylist_urlの情報セットを返す
        """
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def __MakeMylistSample(self, id: str) -> Mylist:
        """Mylistオブジェクトを作成する

        Note:
            マイリスト情報セット
                id (int): ID
                username (str): 投稿者名
                mylistname (str): マイリスト名
                type (str): マイリストのタイプ({"uploaded", "mylist"})
                showname (str): マイリストの一意名({username}_{type})
                                typeが"uploaded"の場合："{username}さんの投稿動画"
                                typeが"mylist"の場合："「{mylistname}」-{username}さんのマイリスト"
                url (str): マイリストURL
                created_at (str): 作成日時
                updated_at (str): 更新日時
                checked_at (str): 更新確認日時
                check_interval (str): 最低更新間隔
                is_include_new (boolean): 未視聴動画を含むかどうか

        Args:
            id (int): マイリストとURL情報セットのid

        Returns:
            Mylist: Mylistオブジェクト
        """
        ml = self.__GetMylistInfoSet()[id]
        mylist_url = self.__GetURLInfoSet()[id]
        r = Mylist(ml[0], ml[1], ml[2], ml[3], ml[4], mylist_url, ml[5], ml[6], ml[7], ml[8], ml[9])
        return r

    def __LoadToTable(self) -> list[dict]:
        """テスト用の初期レコードを格納したテーブルを用意する

        Returns:
            expect (dict[]): 全SELECTした場合の予測値
        """
        Path(TEST_DB_PATH).unlink(missing_ok=True)

        dbname = TEST_DB_PATH
        engine = create_engine(f"sqlite:///{dbname}", echo=False, pool_recycle=5, connect_args={"timeout": 30})
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine, autoflush=False)
        session = Session()

        MAX_RECORD_NUM = 5
        expect = []
        id_num = 1
        for i in range(0, MAX_RECORD_NUM):
            r = self.__MakeMylistSample(i)
            session.add(r)

            d = r.toDict()
            d["id"] = id_num
            id_num = id_num + 1
            expect.append(d)

        session.commit()
        session.close()
        return expect

    def test_GetListname(self):
        """shownameを取得する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            def GetListname(url, username, old_showname) -> str:
                pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
                if re.search(pattern, url):
                    return f"{username}さんの投稿動画"

                pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
                if re.search(pattern, url):
                    # TODO::マイリスト名の一部のみしか反映できていない
                    res_str = re.sub("-(.*)さんのマイリスト", f"-{username}さんのマイリスト", old_showname)
                    return res_str
                return ""

            for r in expect:
                now_username = "新しい" + r["username"]
                url = r["url"]
                old_showname = r["username"]
                actual_showname = m_cont.GetListname(url, now_username, old_showname)
                expect_showname = GetListname(url, now_username, old_showname)
                self.assertEqual(expect_showname, actual_showname)

    def test_Upsert(self):
        """MylistにUPSERTする機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)

            # INSERT
            MAX_RECORD_NUM = 5
            expect = []
            id_num = 1
            for i in range(0, MAX_RECORD_NUM):
                r = self.__MakeMylistSample(i)
                res = m_cont.Upsert(r.id, r.username, r.mylistname, r.type, r.showname, r.url, r.created_at, r.updated_at, r.checked_at, r.check_interval, r.is_include_new)
                self.assertEqual(res, 0)

                d = r.toDict()
                d["id"] = id_num
                id_num = id_num + 1
                expect.append(d)
            actual = m_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # UPDATE
            # idをランダムに選定し、statusを更新する
            t_id = random.sample(range(0, MAX_RECORD_NUM - 1), 2)
            for i in t_id:
                expect[i]["check_interval"] = "30分"
                r = expect[i]
                res = m_cont.Upsert(r["id"], r["username"], r["mylistname"], r["type"], r["showname"], r["url"],
                                    r["created_at"], r["updated_at"], r["checked_at"], r["check_interval"], r["is_include_new"])
                self.assertEqual(res, 1)
            actual = m_cont.Select()
            expect = sorted(expect, key=lambda x: x["id"])
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)
            pass

    def test_UpdateIncludeFlag(self):
        """Mylistの特定のレコードについて新着フラグを更新する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            url_info = self.__GetURLInfoSet()
            t_id = random.randint(0, len(url_info) - 1)
            mylist_url = url_info[t_id]
            res = m_cont.UpdateIncludeFlag(mylist_url, True)
            self.assertEqual(res, 0)

            for r in expect:
                if r["url"] == mylist_url:
                    r["is_include_new"] = True
            expect = sorted(expect, key=lambda x: x["id"])

            actual = m_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないマイリストを指定する
            res = m_cont.UpdateIncludeFlag("https://www.nicovideo.jp/user/99999999/video", True)
            self.assertEqual(res, -1)
            pass

    def test_UpdateUpdatedAt(self):
        """Mylistの特定のレコードについて更新日時を更新する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            url_info = self.__GetURLInfoSet()
            t_id = random.randint(0, len(url_info) - 1)
            mylist_url = url_info[t_id]

            dst_df = "%Y-%m-%d %H:%M:%S"
            dst = datetime.now().strftime(dst_df)
            res = m_cont.UpdateUpdatedAt(mylist_url, dst)
            self.assertEqual(res, 0)

            for r in expect:
                if r["url"] == mylist_url:
                    r["updated_at"] = dst
            expect = sorted(expect, key=lambda x: x["id"])

            actual = m_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないマイリストを指定する
            res = m_cont.UpdateUpdatedAt("https://www.nicovideo.jp/user/99999999/video", dst)
            self.assertEqual(res, -1)
            pass

    def test_UpdateCheckedAt(self):
        """Mylistの特定のレコードについて更新確認日時を更新する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            url_info = self.__GetURLInfoSet()
            t_id = random.randint(0, len(url_info) - 1)
            mylist_url = url_info[t_id]

            dst_df = "%Y-%m-%d %H:%M:%S"
            dst = datetime.now().strftime(dst_df)
            res = m_cont.UpdateCheckedAt(mylist_url, dst)
            self.assertEqual(res, 0)

            for r in expect:
                if r["url"] == mylist_url:
                    r["checked_at"] = dst
            expect = sorted(expect, key=lambda x: x["id"])

            actual = m_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないマイリストを指定する
            res = m_cont.UpdateCheckedAt("https://www.nicovideo.jp/user/99999999/video", dst)
            self.assertEqual(res, -1)
            pass

    def test_UpdateUsername(self):
        """Mylistの特定のレコードについてusernameを更新する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            url_info = self.__GetURLInfoSet()
            t_id = random.randint(0, len(url_info) - 1)
            mylist_url = url_info[t_id]
            now_username = "新しい" + expect[t_id]["username"]
            res = m_cont.UpdateUsername(mylist_url, now_username)
            self.assertEqual(res, 0)

            for r in expect:
                if r["url"] == mylist_url:
                    r["username"] = now_username
                    r["showname"] = m_cont.GetListname(mylist_url, now_username, r["showname"])
            expect = sorted(expect, key=lambda x: x["id"])

            actual = m_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないマイリストを指定する
            res = m_cont.UpdateUsername("https://www.nicovideo.jp/user/99999999/video", now_username)
            self.assertEqual(res, -1)
            pass

    def test_SwapId(self):
        """idを交換する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            # 交換元と交換先のidを選定する
            t_id = random.sample(range(0, len(expect)), 2)
            src_id = t_id[0] + 1
            dst_id = t_id[1] + 1

            actual = m_cont.SwapId(src_id, dst_id)
            expect_src = expect[src_id - 1]
            expect_dst = expect[dst_id - 1]
            expect_src["id"], expect_dst["id"] = expect_dst["id"], expect_src["id"]
            self.assertEqual((expect_src, expect_dst), actual)

            expect = sorted(expect, key=lambda x: x["id"])

            actual = m_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 交換元と交換先に同じidを指定する
            actual = m_cont.SwapId(src_id, src_id)
            self.assertEqual((None, None), actual)

            # 交換元と交換先に存在しないidを指定する
            actual = m_cont.SwapId(-src_id, -dst_id)
            self.assertEqual((None, None), actual)

    def test_DeleteFromURL(self):
        """Mylistのレコードを削除する機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            url_info = self.__GetURLInfoSet()
            t_id = random.randint(0, len(url_info) - 1)
            mylist_url = url_info[t_id]
            res = m_cont.DeleteFromURL(mylist_url)
            self.assertEqual(res, 0)

            expect = [e for e in expect if e["url"] != mylist_url]
            expect = sorted(expect, key=lambda x: x["id"])

            actual = m_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

            # 存在しないマイリストを指定する
            res = m_cont.DeleteFromURL("https://www.nicovideo.jp/user/99999999/video")
            self.assertEqual(res, -1)
            pass

    def test_Select(self):
        """MylistからSELECTする
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()
            expect = sorted(expect, key=lambda x: x["id"])

            actual = m_cont.Select()
            actual = sorted(actual, key=lambda x: x["id"])
            self.assertEqual(expect, actual)
            pass

    def test_SelectFromShowname(self):
        """Mylistからshownameを条件としてSELECTする機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            t_id = random.randint(0, len(expect) - 1)
            showname = expect[t_id]["showname"]
            actual = m_cont.SelectFromShowname(showname)

            expect = [e for e in expect if e["showname"] == showname]
            self.assertEqual(1, len(actual))
            self.assertEqual(expect, actual)

            # 存在しないshownameを指定する
            actual = m_cont.SelectFromShowname("存在しないマイリストshowname")
            self.assertEqual([], actual)
            pass

    def test_SelectFromURL(self):
        """Mylistからurlを条件としてSELECTする機能のテスト
        """
        with ExitStack() as stack:
            # mock = stack.enter_context(patch("NNMM.MylistDBController.MylistDBController.Func"))
            m_cont = MylistDBController(TEST_DB_PATH)
            expect = self.__LoadToTable()

            url_info = self.__GetURLInfoSet()
            t_id = random.randint(0, len(url_info) - 1)
            mylist_url = url_info[t_id]
            actual = m_cont.SelectFromURL(mylist_url)

            expect = [e for e in expect if e["url"] == mylist_url]
            self.assertEqual(1, len(actual))
            self.assertEqual(expect, actual)

            # 存在しないurlを指定する
            actual = m_cont.SelectFromURL("存在しないマイリストurl")
            self.assertEqual([], actual)
            pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
