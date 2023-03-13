# coding: utf-8
"""CSVSaveLoadのテスト

CSVSaveLoadの各種機能をテストする
"""

import copy
import sys
import unittest
from contextlib import ExitStack
from logging import INFO, getLogger
from pathlib import Path

from mock import MagicMock, PropertyMock, mock_open, patch

from NNMM import CSVSaveLoad
from NNMM.MylistDBController import *

TEST_DB_PATH = "./test/test.db"
CSV_PATH = "./test/result.csv"


class TestCSVSaveLoad(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        Path(TEST_DB_PATH).unlink(missing_ok=True)
        Path(CSV_PATH).unlink(missing_ok=True)
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

            d = r.to_dict()
            d["id"] = id_num
            id_num = id_num + 1
            expect.append(d)

        session.commit()
        session.close()
        return expect

    def test_SaveMylist(self):
        """SaveMylistのテスト
        """
        with ExitStack() as stack:
            mockio = stack.enter_context(patch("pathlib.Path.open", mock_open()))
            m_cont = MylistDBController(TEST_DB_PATH)
            records = self.__LoadToTable()

            res = CSVSaveLoad.SaveMylist(m_cont, CSV_PATH)
            self.assertEqual(res, 0)

            # open呼び出し予測値
            expect = (("w", ), {"encoding": "utf_8_sig"})

            # open呼び出しチェック
            ocal = mockio.call_args_list
            actual = [(ca[0], ca[1]) for ca in ocal]
            self.assertEqual(len(actual), 1)
            actual = actual[0]
            self.assertEqual(expect, actual)

            # write呼び出し予測値
            expect = []
            mylist_cols = Mylist.__table__.c.keys()
            expect.append(",".join(mylist_cols) + "\n")
            for r in records:
                param_list = [str(r.get(s)) for s in mylist_cols]
                expect.append(",".join(param_list) + "\n")

            # write呼び出しチェック
            wcal = mockio().write.call_args_list
            actual = [ca[0][0] for ca in wcal]
            self.assertEqual(expect, actual)
        pass

    def test_LoadMylist(self):
        """LoadMylistのテスト
        """
        with ExitStack() as stack:
            m_cont = MylistDBController(TEST_DB_PATH)
            records = self.__LoadToTable()

            # Path.open().readline で返されるモックデータの用意
            readdata = []
            mylist_cols = Mylist.__table__.c.keys()
            readdata.append(",".join(mylist_cols) + "\n")
            for r in records:
                param_list = [str(r.get(s)) for s in mylist_cols]
                readdata.append(",".join(param_list) + "\n")

            # mock適用
            mockio = stack.enter_context(patch("pathlib.Path.open", mock_open(read_data="".join(readdata))))

            # DB初期化
            for r in records:
                m_cont.DeleteFromURL(r["url"])
            self.assertEqual(m_cont.Select(), [])

            # ロード呼び出し
            res = CSVSaveLoad.LoadMylist(m_cont, CSV_PATH)
            self.assertEqual(res, 0)

            # open呼び出し予測値
            expect = (("r", ), {"encoding": "utf_8_sig"})

            # open呼び出しチェック
            ocal = mockio.call_args_list
            actual = [(ca[0], ca[1]) for ca in ocal]
            self.assertEqual(len(actual), 1)
            actual = actual[0]
            self.assertEqual(expect, actual)

            # 実行後DBチェック
            expect = copy.deepcopy(records)
            actual = m_cont.Select()
            self.assertEqual(expect, actual)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
