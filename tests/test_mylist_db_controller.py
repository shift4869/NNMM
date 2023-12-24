import random
import re
import sys
import unittest
from datetime import datetime

from NNMM.model import Mylist
from NNMM.mylist_db_controller import MylistDBController


class TestMylistDBController(unittest.TestCase):
    def setUp(self):
        self.test_db_path = ":memory:"
        self.controller = MylistDBController(self.test_db_path)

    def _get_mylist_list(self) -> list[tuple]:
        """Mylistオブジェクトの情報セットを返す（mylist_url以外）"""
        mylist_list = [
            (
                1,
                "投稿者1",
                "投稿動画",
                "uploaded",
                "投稿者1さんの投稿動画",
                "2021-05-29 00:00:11",
                "2021-10-16 00:00:11",
                "2021-10-17 00:00:11",
                "15分",
                False,
            ),
            (
                2,
                "投稿者2",
                "投稿動画",
                "uploaded",
                "投稿者2さんの投稿動画",
                "2021-05-29 00:00:22",
                "2021-10-16 00:00:22",
                "2021-10-17 00:00:22",
                "15分",
                False,
            ),
            (
                3,
                "投稿者1",
                "マイリスト1",
                "mylist",
                "「マイリスト1」-投稿者1さんのマイリスト",
                "2021-05-29 00:11:11",
                "2021-10-16 00:11:11",
                "2021-10-17 00:11:11",
                "15分",
                False,
            ),
            (
                4,
                "投稿者1",
                "マイリスト2",
                "mylist",
                "「マイリスト2」-投稿者1さんのマイリスト",
                "2021-05-29 00:22:11",
                "2021-10-16 00:22:11",
                "2021-10-17 00:22:11",
                "15分",
                False,
            ),
            (
                5,
                "投稿者3",
                "マイリスト3",
                "mylist",
                "「マイリスト3」-投稿者3さんのマイリスト",
                "2021-05-29 00:11:33",
                "2021-10-16 00:11:33",
                "2021-10-17 00:11:33",
                "15分",
                False,
            ),
        ]
        return mylist_list

    def _get_mylist_url_list(self) -> list[str]:
        """mylist_urlの情報セットを返す"""
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
        ]
        return url_info

    def _make_mylist_sample(self, id: str) -> Mylist:
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
        ml = self._get_mylist_list()[id]
        mylist_url = self._get_mylist_url_list()[id]
        r = Mylist(ml[0], ml[1], ml[2], ml[3], ml[4], mylist_url, ml[5], ml[6], ml[7], ml[8], ml[9])
        return r

    def _load_table(self) -> list[dict]:
        """テスト用の初期レコードを格納したテーブルを用意する

        Returns:
            expect (list[dict]): 全SELECTした場合の予測値
        """
        controller = self.controller
        MAX_RECORD_NUM = 5
        expect = []
        id_num = 0
        for i in range(MAX_RECORD_NUM):
            r = self._make_mylist_sample(i)
            res = controller.upsert(
                i,
                r.username,
                r.mylistname,
                r.type,
                r.showname,
                r.url,
                r.created_at,
                r.updated_at,
                r.checked_at,
                r.check_interval,
                r.is_include_new,
            )
            self.assertEqual(res, 0)

            d = r.to_dict()
            d["id"] = id_num
            id_num = id_num + 1
            expect.append(d)
        return expect

    def test_get_showname(self):
        """shownameを取得する機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        def get_showname(url: str, username: str, old_showname: str) -> str:
            pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
            if re.search(pattern, url):
                return f"{username}さんの投稿動画"

            pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
            if re.search(pattern, url):
                res_str = re.sub("-(.*)さんのマイリスト", f"-{username}さんのマイリスト", old_showname)
                return res_str
            return ""

        for r in expect:
            now_username = "新しい" + r["username"]
            url = r["url"]
            old_showname = r["username"]
            actual_showname = controller.get_showname(url, now_username, old_showname)
            expect_showname = get_showname(url, now_username, old_showname)
            self.assertEqual(expect_showname, actual_showname)

    def test_upsert(self):
        """MylistにUPSERTする機能のテスト"""
        controller = self.controller

        # INSERT
        MAX_RECORD_NUM = 5
        expect = []
        id_num = 1
        for i in range(0, MAX_RECORD_NUM):
            r = self._make_mylist_sample(i)
            res = controller.upsert(
                r.id,
                r.username,
                r.mylistname,
                r.type,
                r.showname,
                r.url,
                r.created_at,
                r.updated_at,
                r.checked_at,
                r.check_interval,
                r.is_include_new,
            )
            self.assertEqual(res, 0)

            d = r.to_dict()
            d["id"] = id_num
            id_num = id_num + 1
            expect.append(d)
        actual = controller.select()
        expect = sorted(expect, key=lambda x: x["id"])
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # UPDATE
        # idをランダムに選定し、statusを更新する
        t_id = random.sample(range(0, MAX_RECORD_NUM - 1), 2)
        for i in t_id:
            expect[i]["check_interval"] = "30分"
            r = expect[i]
            res = controller.upsert(
                r["id"],
                r["username"],
                r["mylistname"],
                r["type"],
                r["showname"],
                r["url"],
                r["created_at"],
                r["updated_at"],
                r["checked_at"],
                r["check_interval"],
                r["is_include_new"],
            )
            self.assertEqual(res, 1)
        actual = controller.select()
        expect = sorted(expect, key=lambda x: x["id"])
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

    def test_update_include_flag(self):
        """Mylistの特定のレコードについて新着フラグを更新する機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        url_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(url_info) - 1)
        mylist_url = url_info[t_id]
        res = controller.update_include_flag(mylist_url, True)
        self.assertEqual(res, 0)

        for r in expect:
            if r["url"] == mylist_url:
                r["is_include_new"] = True
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないマイリストを指定する
        res = controller.update_include_flag("https://www.nicovideo.jp/user/99999999/video", True)
        self.assertEqual(res, -1)

    def test_update_updated_at(self):
        """Mylistの特定のレコードについて更新日時を更新する機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        url_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(url_info) - 1)
        mylist_url = url_info[t_id]

        dst_df = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now().strftime(dst_df)
        res = controller.update_updated_at(mylist_url, dst)
        self.assertEqual(res, 0)

        for r in expect:
            if r["url"] == mylist_url:
                r["updated_at"] = dst
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないマイリストを指定する
        res = controller.update_updated_at("https://www.nicovideo.jp/user/99999999/video", dst)
        self.assertEqual(res, -1)

    def test_update_checked_at(self):
        """Mylistの特定のレコードについて更新確認日時を更新する機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        url_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(url_info) - 1)
        mylist_url = url_info[t_id]

        dst_df = "%Y-%m-%d %H:%M:%S"
        dst = datetime.now().strftime(dst_df)
        res = controller.update_checked_at(mylist_url, dst)
        self.assertEqual(res, 0)

        for r in expect:
            if r["url"] == mylist_url:
                r["checked_at"] = dst
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないマイリストを指定する
        res = controller.update_checked_at("https://www.nicovideo.jp/user/99999999/video", dst)
        self.assertEqual(res, -1)

    def test_update_username(self):
        """Mylistの特定のレコードについてusernameを更新する機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        url_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(url_info) - 1)
        mylist_url = url_info[t_id]
        now_username = "新しい" + expect[t_id]["username"]
        res = controller.update_username(mylist_url, now_username)
        self.assertEqual(res, 0)

        for r in expect:
            if r["url"] == mylist_url:
                r["username"] = now_username
                r["showname"] = controller.get_showname(mylist_url, now_username, r["showname"])
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないマイリストを指定する
        res = controller.update_username("https://www.nicovideo.jp/user/99999999/video", now_username)
        self.assertEqual(res, -1)

    def test_swap_id(self):
        """idを交換する機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        # 交換元と交換先のidを選定する
        t_id = random.sample(range(0, len(expect) - 1), 2)
        src_id, dst_id = t_id

        actual = controller.swap_id(src_id, dst_id)
        expect_src = expect[src_id]
        expect_dst = expect[dst_id]
        expect_src["id"], expect_dst["id"] = expect_dst["id"], expect_src["id"]
        self.assertEqual((expect_src, expect_dst), actual)

        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 交換元と交換先に同じidを指定する
        actual = controller.swap_id(src_id, src_id)
        self.assertEqual((None, None), actual)

        # 交換元と交換先に存在しないidを指定する
        actual = controller.swap_id(-src_id, -dst_id)
        self.assertEqual((None, None), actual)

    def test_delete_from_mylist_url(self):
        """Mylistのレコードを削除する機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        url_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(url_info) - 1)
        mylist_url = url_info[t_id]
        res = controller.delete_from_mylist_url(mylist_url)
        self.assertEqual(res, 0)

        expect = [e for e in expect if e["url"] != mylist_url]
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないマイリストを指定する
        res = controller.delete_from_mylist_url("https://www.nicovideo.jp/user/99999999/video")
        self.assertEqual(res, -1)

    def test_select(self):
        """MylistからSELECTする"""
        controller = self.controller
        expect = self._load_table()
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

    def test_select_from_showname(self):
        """Mylistからshownameを条件としてSELECTする機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        t_id = random.randint(0, len(expect) - 1)
        showname = expect[t_id]["showname"]
        actual = controller.select_from_showname(showname)

        expect = [e for e in expect if e["showname"] == showname]
        self.assertEqual(1, len(actual))
        self.assertEqual(expect, actual)

        # 存在しないshownameを指定する
        actual = controller.select_from_showname("存在しないマイリストshowname")
        self.assertEqual([], actual)

    def test_select_from_url(self):
        """Mylistからurlを条件としてSELECTする機能のテスト"""
        controller = self.controller
        expect = self._load_table()

        url_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(url_info) - 1)
        mylist_url = url_info[t_id]
        actual = controller.select_from_url(mylist_url)

        expect = [e for e in expect if e["url"] == mylist_url]
        self.assertEqual(1, len(actual))
        self.assertEqual(expect, actual)

        # 存在しないurlを指定する
        actual = controller.select_from_url("存在しないマイリストurl")
        self.assertEqual([], actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
    unittest.main(warnings="ignore")
