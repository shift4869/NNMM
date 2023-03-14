# coding: utf-8
"""MylistInfoDBControllerのテスト

MylistInfoDBController.MylistInfoDBController()の各種機能をテストする
"""

import copy
import random
import sys
import unittest

from NNMM.Model import MylistInfo
from NNMM.MylistInfoDBController import MylistInfoDBController


class TestMylistInfoDBController(unittest.TestCase):
    def setUp(self):
        self.test_db_path = ":memory:"
        self.controller = MylistInfoDBController(self.test_db_path)

    def _get_video_list(self) -> list[tuple]:
        """動画情報セットを返す（mylist_url以外）
        """
        video = [
            ("sm11111111", "動画タイトル1", "投稿者1", "未視聴", "2021-05-29 22:00:11", "2021-05-29 22:01:11", "https://www.nicovideo.jp/watch/sm11111111", "2021-10-16 00:00:11"),
            ("sm22222222", "動画タイトル2", "投稿者1", "未視聴", "2021-05-29 22:00:22", "2021-05-29 22:02:22", "https://www.nicovideo.jp/watch/sm22222222", "2021-10-16 00:00:22"),
            ("sm33333333", "動画タイトル3", "投稿者1", "未視聴", "2021-05-29 22:00:33", "2021-05-29 22:03:33", "https://www.nicovideo.jp/watch/sm33333333", "2021-10-16 00:00:33"),
            ("sm44444444", "動画タイトル4", "投稿者2", "未視聴", "2021-05-29 22:00:44", "2021-05-29 22:04:44", "https://www.nicovideo.jp/watch/sm44444444", "2021-10-16 00:00:44"),
            ("sm55555555", "動画タイトル5", "投稿者2", "未視聴", "2021-05-29 22:00:55", "2021-05-29 22:05:55", "https://www.nicovideo.jp/watch/sm55555555", "2021-10-16 00:00:55"),
        ]
        return video

    def _get_mylist_url_list(self) -> list[str]:
        """mylist_urlの情報セットを返す
        """
        mylist_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/11111111/mylist/12345678",
            "https://www.nicovideo.jp/user/22222222/video",
        ]
        return mylist_info

    def _make_video_sample(self, id: int, mylist_id: int) -> MylistInfo:
        """MylistInfoオブジェクトを作成する

        Note:
            動画情報セット
                video_id (str): 動画ID(smxxxxxxxx)
                title (str): 動画タイトル
                username (str): 投稿者名
                status (str): 視聴状況({"未視聴", ""})
                uploaded_at (str): 投稿日時
                registered_at (str): 登録日時
                video_url (str): 動画URL
                created_at (str): 作成日時
            マイリスト情報セット
                mylist_url (str): 所属マイリストURL

        Args:
            id (int): 動画情報セットのid
            mylist_id (int): マイリスト情報セットのid

        Returns:
            MylistInfo: MylistInfoオブジェクト
        """
        v = self._get_video_list()[id]
        mylist_url = self._get_mylist_url_list()[mylist_id]
        r = MylistInfo(v[0], v[1], v[2], v[3], v[4], v[5], v[6], mylist_url, v[7])
        return r

    def _load_table(self) -> list[dict]:
        """テスト用の初期レコードを格納したテーブルを用意する

        Returns:
            expect (list[dict]): 全SELECTした場合の予測値
        """
        controller = self.controller
        expect = []
        records = []
        id_num = 1
        for i in range(0, 3):
            for j in range(0, 5):
                r = self._make_video_sample(j, i)
                d = r.to_dict()
                del d["id"]
                records.append(d)

                d = r.to_dict()
                d["id"] = id_num
                id_num = id_num + 1
                expect.append(d)
        res = controller.upsert_from_list(records)
        self.assertEqual(res, 0)
        return expect

    def test_upsert(self):
        """MylistInfoにUPSERTする機能のテスト
        """
        controller = self.controller

        # INSERT
        expect = []
        id_num = 1
        for i in range(0, 3):
            for j in range(0, 5):
                r = self._make_video_sample(j, i)
                res = controller.upsert(
                    r.video_id,
                    r.title,
                    r.username,
                    r.status,
                    r.uploaded_at,
                    r.registered_at,
                    r.video_url,
                    r.mylist_url,
                    r.created_at
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
        t_id = random.sample(range(0, 15), 5)
        for i in t_id:
            expect[i]["status"] = ""
            r = expect[i]
            res = controller.upsert(
                r["video_id"],
                r["title"],
                r["username"],
                r["status"],
                r["uploaded_at"],
                r["registered_at"],
                r["video_url"],
                r["mylist_url"],
                r["created_at"]
            )
            self.assertEqual(res, 1)
        actual = controller.select()
        expect = sorted(expect, key=lambda x: x["id"])
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

    def test_upsert_from_list(self):
        """MylistInfoにListからまとめて受け取りUPSERTする機能のテスト
        """
        controller = self.controller

        # INSERT
        expect = []
        records = []
        id_num = 1
        for i in range(0, 3):
            for j in range(0, 5):
                r = self._make_video_sample(j, i)
                d = r.to_dict()
                del d["id"]
                records.append(d)

                d = r.to_dict()
                d["id"] = id_num
                id_num = id_num + 1
                expect.append(d)

        res = controller.upsert_from_list(records)
        self.assertEqual(res, 0)

        actual = controller.select()
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

        res = controller.upsert_from_list(records)
        self.assertEqual(res, 1)

        actual = controller.select()
        expect = sorted(expect, key=lambda x: x["id"])
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

    def test_update_status(self):
        """MylistInfoの特定のレコードについてstatusを更新する機能のテスト
        """
        controller = self.controller
        expect = []
        records = []
        id_num = 1
        for i in range(0, 3):
            for j in range(0, 5):
                r = self._make_video_sample(j, i)
                d = r.to_dict()
                del d["id"]
                records.append(d)

                d = r.to_dict()
                d["id"] = id_num
                id_num = id_num + 1
                expect.append(d)
        res = controller.upsert_from_list(records)
        self.assertEqual(res, 0)

        # UPDATE
        # idをランダムに選定し、statusを更新する
        t_id = random.sample(range(0, 15), 5)
        for i in t_id:
            expect[i]["status"] = ""
            r = expect[i]
            res = controller.update_status(r["video_id"], r["mylist_url"], "")
            self.assertEqual(res, 0)
        actual = controller.select()
        expect = sorted(expect, key=lambda x: x["id"])
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないレコードを指定する
        res = controller.update_status("sm99999999", "https://www.nicovideo.jp/watch/sm11111111", "")
        self.assertEqual(res, 1)

        # video_idの形式が不正
        res = controller.update_status("nm99999999", "https://www.nicovideo.jp/watch/sm11111111", "")
        self.assertEqual(res, -1)

        # statusが不正
        r = expect[0]
        res = controller.update_status(r["video_id"], r["mylist_url"], "不正なステータス")
        self.assertEqual(res, -1)

    def test_update_status_in_mylist(self):
        """MylistInfoについて特定のマイリストに含まれるレコードのstatusをすべて更新する機能のテスト
        """
        controller = self.controller
        expect = []
        records = []
        id_num = 1
        for i in range(0, 3):
            for j in range(0, 5):
                r = self._make_video_sample(j, i)
                d = r.to_dict()
                del d["id"]
                records.append(d)

                d = r.to_dict()
                d["id"] = id_num
                id_num = id_num + 1
                expect.append(d)
        res = controller.upsert_from_list(records)
        self.assertEqual(res, 0)

        # UPDATE
        # 特定のマイリストに含まれるレコードのstatusを更新する
        mylist_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(mylist_info) - 1)
        mylist_url = mylist_info[t_id]
        res = controller.update_status_in_mylist(mylist_url, "")
        self.assertEqual(res, 0)

        for r in expect:
            if r["mylist_url"] == mylist_url:
                r["status"] = ""
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないマイリストを指定する
        res = controller.update_status_in_mylist("https://www.nicovideo.jp/user/99999999/video")
        self.assertEqual(res, 1)

        # statusが不正
        r = expect[0]
        res = controller.update_status_in_mylist(mylist_url, "不正なステータス")
        self.assertEqual(res, -1)

    def test_update_username_in_mylist(self):
        """MylistInfoについて特定のマイリストに含まれるレコードのusernameをすべて更新する機能のテスト
        """
        controller = self.controller
        expect = []
        records = []
        id_num = 1
        for i in range(0, 3):
            for j in range(0, 5):
                r = self._make_video_sample(j, i)
                d = r.to_dict()
                del d["id"]
                records.append(d)

                d = r.to_dict()
                d["id"] = id_num
                id_num = id_num + 1
                expect.append(d)
        res = controller.upsert_from_list(records)
        self.assertEqual(res, 0)

        # UPDATE
        # 特定のマイリストに含まれるレコードのusernameを更新する
        mylist_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(mylist_info) - 1)
        mylist_url = mylist_info[t_id]
        username = "新しい投稿者"
        res = controller.update_username_in_mylist(mylist_url, username)
        self.assertEqual(res, 0)

        for r in expect:
            if r["mylist_url"] == mylist_url:
                r["username"] = username
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないマイリストを指定する
        res = controller.update_username_in_mylist("https://www.nicovideo.jp/user/99999999/video", username)
        self.assertEqual(res, 1)

    def test_delete_in_mylist(self):
        """MylistInfoについて特定のマイリストに含まれるレコードをすべて削除する機能のテスト
        """
        controller = self.controller
        expect = self._load_table()

        # DELETE
        # 特定のマイリストに含まれるレコードを削除する
        mylist_info = self._get_mylist_url_list()
        t_id = random.randint(0, len(mylist_info) - 1)
        mylist_url = mylist_info[t_id]
        res = controller.delete_in_mylist(mylist_url)
        self.assertEqual(res, 0)

        expect = [e for e in expect if e["mylist_url"] != mylist_url]
        expect = sorted(expect, key=lambda x: x["id"])

        actual = controller.select()
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないマイリストを指定する
        res = controller.delete_in_mylist("https://www.nicovideo.jp/user/99999999/video")
        self.assertEqual(res, 1)

    def test_Select(self):
        """MylistInfoからSELECTする機能のテスト
        """
        controller = self.controller
        expect = self._load_table()

        actual = controller.select()
        expect = sorted(expect, key=lambda x: x["id"])
        actual = sorted(actual, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

    def test_select_from_video_id(self):
        """MylistInfoからvideo_idを条件としてSELECTする機能のテスト
        """
        controller = self.controller
        expect = self._load_table()

        video_info = self._get_video_list()
        video_id_info = [v[0] for v in video_info]

        # SELECT条件となるvideo_idを選定する
        # 特定のマイリストに含まれるレコードを削除する
        t_id = random.randint(0, len(video_id_info) - 1)
        video_id = video_id_info[t_id]
        actual = controller.select_from_video_id(video_id)
        self.assertTrue(len(actual) > 0)
        actual = sorted(actual, key=lambda x: x["id"])

        expect = [e for e in expect if e["video_id"] == video_id]
        expect = sorted(expect, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないvideo_idを指定する
        actual = controller.select_from_video_id("sm99999999")
        self.assertEqual(actual, [])

    def test_select_from_id_url(self):
        """MylistInfoからvideo_idとmylist_urlを条件としてSELECTする機能のテスト
        """
        controller = self.controller
        expect = self._load_table()

        # SELECT条件となるvideo_idを選定する
        video_info = self._get_video_list()
        video_id_info = [v[0] for v in video_info]
        t_id = random.randint(0, len(video_id_info) - 1)
        video_id = video_id_info[t_id]

        # SELECT条件となるmylist_urlを選定する
        mylist_info = self._get_mylist_url_list()
        m_id = random.randint(0, len(mylist_info) - 1)
        mylist_url = mylist_info[m_id]

        # 正常系
        actual = controller.select_from_id_url(video_id, mylist_url)
        self.assertTrue(len(actual) == 1)
        expect = [e for e in expect if e["video_id"] == video_id and e["mylist_url"] == mylist_url]
        self.assertEqual(expect, actual)

        # 異常系
        # 存在しないvideo_idを指定する
        error_video_id = "sm99999999"
        actual = controller.select_from_id_url(error_video_id, mylist_url)
        self.assertEqual(actual, [])

        # 存在しないmylist_urlを指定する
        error_mylist_url = "https://www.nicovideo.jp/user/99999999/mylist/99999999"
        actual = controller.select_from_id_url(video_id, error_mylist_url)
        self.assertEqual(actual, [])

        # どちらも存在しない指定
        actual = controller.select_from_id_url(error_video_id, error_mylist_url)
        self.assertEqual(actual, [])

    def test_select_from_video_url(self):
        """MylistInfoからvideo_urlを条件としてSELECTする機能のテスト
        """
        controller = self.controller
        expect = self._load_table()

        video_info = self._get_video_list()
        video_url_info = [v[6] for v in video_info]

        # SELECT条件となるvideo_urlを選定する
        t_id = random.randint(0, len(video_url_info) - 1)
        video_url = video_url_info[t_id]
        actual = controller.select_from_video_url(video_url)
        self.assertTrue(len(actual) > 0)
        actual = sorted(actual, key=lambda x: x["id"])

        expect = [e for e in expect if e["video_url"] == video_url]
        expect = sorted(expect, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないvideo_urlを指定する
        actual = controller.select_from_video_id("https://www.nicovideo.jp/watch/sm99999999")
        self.assertEqual(actual, [])

    def test_select_from_mylist_url(self):
        """MylistInfoからmylist_urlを条件としてSELECTする機能のテスト
        """
        controller = self.controller
        expect = self._load_table()

        # SELECT条件となるmylist_urlを選定する
        mylist_info = self._get_mylist_url_list()
        m_id = random.randint(0, len(mylist_info) - 1)
        mylist_url = mylist_info[m_id]

        actual = controller.select_from_mylist_url(mylist_url)
        self.assertTrue(len(actual) > 0)
        actual = sorted(actual, key=lambda x: x["id"])

        expect = [e for e in expect if e["mylist_url"] == mylist_url]
        expect = sorted(expect, key=lambda x: x["id"])
        self.assertEqual(expect, actual)

        # 存在しないmylist_urlを指定する
        error_mylist_url = "https://www.nicovideo.jp/user/99999999/mylist/99999999"
        actual = controller.select_from_mylist_url(error_mylist_url)
        self.assertEqual(actual, [])

    def test_select_from_username(self):
        """MylistInfoからusernameを条件としてSELECTする機能のテスト
        """
        controller = self.controller
        expect_records = self._load_table()

        username_list = [
            "投稿者1",
            "投稿者2",
        ]
        for username in username_list:
            actual = controller.select_from_username(username)
            self.assertTrue(len(actual) > 0)
            actual = sorted(actual, key=lambda x: x["id"])

            expect = [e for e in expect_records if e["username"] == username]
            expect = sorted(expect, key=lambda x: x["id"])
            self.assertEqual(expect, actual)

        actual = controller.select_from_username("存在しない投稿者")
        self.assertEqual(actual, [])


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
