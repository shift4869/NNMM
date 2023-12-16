import copy
import random
import sys
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta
from pathlib import Path

import freezegun
import orjson
from mock import mock_open, patch

from NNMM.model import Mylist, MylistInfo
from NNMM.mylist_db_controller import MylistDBController
from NNMM.util import MylistType, Result, find_values, get_mylist_type, get_now_datetime, interval_translate, is_mylist_include_new_video, load_mylist, popup_get_text, save_mylist

TEST_DB_PATH = ":memory:"
CSV_PATH = "./tests/result.csv"

class TestUtil(unittest.TestCase):
    def tearDown(self):
        Path(CSV_PATH).unlink(missing_ok=True)

    def _get_mylist_info_list(self) -> list[tuple]:
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

    def _get_mylist_url_list(self) -> list[str]:
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
        ml = self._get_mylist_info_list()[id]
        mylist_url = self._get_mylist_url_list()[id]
        r = Mylist(ml[0], ml[1], ml[2], ml[3], ml[4], mylist_url, ml[5], ml[6], ml[7], ml[8], ml[9])
        return r

    def _get_video_info_list(self) -> list[tuple]:
        """動画情報セットを返す（mylist_url以外）
        """
        video_info = [
            ("sm11111111", "動画タイトル1", "投稿者1", "未視聴", "2021-05-29 22:00:11", "2021-05-29 22:01:11", "https://www.nicovideo.jp/watch/sm11111111", "2021-10-16 00:00:11"),
            ("sm22222222", "動画タイトル2", "投稿者1", "未視聴", "2021-05-29 22:00:22", "2021-05-29 22:02:22", "https://www.nicovideo.jp/watch/sm22222222", "2021-10-16 00:00:22"),
            ("sm33333333", "動画タイトル3", "投稿者1", "未視聴", "2021-05-29 22:00:33", "2021-05-29 22:03:33", "https://www.nicovideo.jp/watch/sm33333333", "2021-10-16 00:00:33"),
            ("sm44444444", "動画タイトル4", "投稿者2", "未視聴", "2021-05-29 22:00:44", "2021-05-29 22:04:44", "https://www.nicovideo.jp/watch/sm44444444", "2021-10-16 00:00:44"),
            ("sm55555555", "動画タイトル5", "投稿者2", "未視聴", "2021-05-29 22:00:55", "2021-05-29 22:05:55", "https://www.nicovideo.jp/watch/sm55555555", "2021-10-16 00:00:55"),
        ]
        return video_info

    def _make_mylist_info_sample(self, id: int, mylist_id: int) -> MylistInfo:
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
        v = self._get_video_info_list()[id]
        mylist_url = self._get_mylist_url_list()[mylist_id]
        r = MylistInfo(v[0], v[1], v[2], v[3], v[4], v[5], v[6], mylist_url, v[7])
        return r

    def test_Result(self):
        self.assertEqual(True, hasattr(Result, "success"))
        self.assertEqual(True, hasattr(Result, "failed"))

    def test_find_values(self):
        cache_filepath = Path("./tests/cache/test_notes_with_reactions.json")
        sample_dict = orjson.loads(
            cache_filepath.read_bytes()
        ).get("result")

        # 辞書とキーのみ指定
        actual = find_values(sample_dict, "username")
        expect = [
            "user1_username",
            "user2_username",
            "user1_username",
            "user3_username",
            "user1_username",
            "user4_username",
        ]
        self.assertEqual(expect, actual)

        # ホワイトリスト指定
        actual = find_values(sample_dict, "username", False, ["user"])
        expect = [
            "user1_username",
            "user1_username",
            "user1_username",
        ]
        self.assertEqual(expect, actual)

        # ブラックリスト指定
        actual = find_values(sample_dict, "username", False, [], ["note"])
        expect = [
            "user1_username",
            "user1_username",
            "user1_username",
        ]
        self.assertEqual(expect, actual)

        # ホワイトリスト指定複数
        actual = find_values(sample_dict, "name", False, ["note", "files"])
        expect = [
            "1300000001.jpg.webp",
            "1300000002.jpg.webp",
            "1300000003.jpg.webp",
            "1300000004.jpg.webp",
            "2300000001.png",
        ]
        self.assertEqual(expect, actual)

        # ブラックリスト複数指定
        actual = find_values(sample_dict, "createdAt", False, [], ["user", "note"])
        expect = [
            "2023-09-10T03:55:55.054Z",
            "2023-09-10T03:55:57.643Z",
            "2023-09-10T03:56:04.691Z",
        ]
        self.assertEqual(expect, actual)

        # 一意に確定する想定
        actual = find_values(sample_dict[0], "username", True, ["user"])
        expect = "user1_username"
        self.assertEqual(expect, actual)

        # 直下を調べる
        actual = find_values(sample_dict[0], "id", True, [""])
        expect = sample_dict[0]["id"]
        self.assertEqual(expect, actual)

        # 存在しないキーを指定
        actual = find_values(sample_dict, "invalid_key")
        expect = []
        self.assertEqual(expect, actual)

        # 空辞書を探索
        actual = find_values({}, "username")
        expect = []
        self.assertEqual(expect, actual)

        # 空リストを探索
        actual = find_values([], "username")
        expect = []
        self.assertEqual(expect, actual)

        # 文字列を指定
        actual = find_values("invalid_object", "username")
        expect = []
        self.assertEqual(expect, actual)

        # 一意に確定する想定の指定だが、複数見つかった場合
        with self.assertRaises(ValueError):
            actual = find_values(sample_dict, "username", True)

        # 一意に確定する想定の指定だが、見つからなかった場合
        with self.assertRaises(ValueError):
            actual = find_values(sample_dict, "invalid_key", True)

    def test_save_mylist(self):
        """save_mylistのテスト
        """
        with ExitStack() as stack:
            mockio = stack.enter_context(patch("pathlib.Path.open", mock_open()))
            m_cont = MylistDBController(TEST_DB_PATH)

            MAX_RECORD_NUM = 5
            records = []
            expect = []
            id_num = 1
            for i in range(0, MAX_RECORD_NUM):
                r = self._make_mylist_sample(i)
                m_cont.upsert(
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
                d = r.to_dict()
                d["id"] = id_num
                id_num = id_num + 1
                records.append(d)

            res = save_mylist(m_cont, CSV_PATH)
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

    def test_load_mylist(self):
        """load_mylistのテスト
        """
        with ExitStack() as stack:
            m_cont = MylistDBController(TEST_DB_PATH)
            MAX_RECORD_NUM = 5
            records = []
            expect = []
            id_num = 1
            for i in range(0, MAX_RECORD_NUM):
                r = self._make_mylist_sample(i)
                m_cont.upsert(
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
                d = r.to_dict()
                d["id"] = id_num
                id_num = id_num + 1
                records.append(d)

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
                m_cont.delete_from_mylist_url(r["url"])
            self.assertEqual(m_cont.select(), [])

            # ロード呼び出し
            res = load_mylist(m_cont, CSV_PATH)
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
            actual = m_cont.select()
            self.assertEqual(expect, actual)

    def test_get_mylist_type(self):
        """マイリストのタイプを返す機能のテスト
        """
        # 正常系
        # 投稿動画ページのURL
        url = "https://www.nicovideo.jp/user/11111111/video"
        actual = get_mylist_type(url)
        expect = MylistType.uploaded
        self.assertEqual(expect, actual)

        # マイリストURL
        url = "https://www.nicovideo.jp/user/11111111/mylist/00000011"
        actual = get_mylist_type(url)
        expect = MylistType.mylist
        self.assertEqual(expect, actual)

        # 異常系
        # マイリストのURLだがリダイレクト元のURL
        url = "https://www.nicovideo.jp/mylist/00000011"
        actual = get_mylist_type(url)
        self.assertEqual(None, actual)

        # 全く関係ないURL
        url = "https://www.google.co.jp/"
        actual = get_mylist_type(url)
        self.assertEqual(None, actual)

        # ニコニコの別サービスのURL
        url = "https://seiga.nicovideo.jp/seiga/im11111111"
        actual = get_mylist_type(url)
        self.assertEqual(None, actual)

    def test_get_now_datetime(self):
        """タイムスタンプを返す機能のテスト
        """
        src_df = "%Y/%m/%d %H:%M"
        dst_df = "%Y-%m-%d %H:%M:%S"
        f_now = "2021-10-22 01:00:00"
        with freezegun.freeze_time(f_now):
            # 正常系
            actual = get_now_datetime()
            expect = f_now
            self.assertEqual(expect, actual)

            # 異常系
            actual = get_now_datetime()
            expect = datetime.strptime(f_now, dst_df) + timedelta(minutes=1)
            expect = expect.strftime(dst_df)
            self.assertNotEqual(expect, actual)

    def test_is_mylist_include_new_video(self):
        """テーブルリスト内を走査する機能のテスト
        """
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        STATUS_INDEX = 4
        video_id_t = "sm100000{:02}"
        video_name_t = "動画タイトル_{:02}"
        video_url_t = "https://www.nicovideo.jp/watch/sm100000{:02}"
        mylist_url = "https://www.nicovideo.jp/user/11111111/mylist/10000011"
        username = "投稿者1"
        uploaded_t = "21-10-23 01:00:{:02}"
        myshowname = "投稿者1のマイリスト1"
        showname = f"「{myshowname}」-{username}さんのマイリスト"

        def table_list_factory():
            # 実際はタプルのリストだが値を修正してテストするためにリストのリストとする
            t = [
                [i, video_id_t.format(i), video_name_t.format(i), username, "", uploaded_t.format(i),
                 video_url_t.format(i), mylist_url, myshowname, showname] for i in range(1, 10)
            ]
            return t

        # 正常系
        # 全て視聴済
        table_list = table_list_factory()
        actual = is_mylist_include_new_video(table_list)
        self.assertEqual(False, actual)

        # 未視聴を含む
        table_list = table_list_factory()
        t_id = random.sample(range(0, len(table_list) - 1), 2)
        for i in t_id:
            table_list[i][STATUS_INDEX] = "未視聴"
        actual = is_mylist_include_new_video(table_list)
        self.assertEqual(True, actual)

        # 空リストはFalse
        actual = is_mylist_include_new_video([])
        self.assertEqual(False, actual)

        # 異常系
        # 要素数が少ない
        with self.assertRaises(KeyError):
            table_list = table_list_factory()
            table_list = [t[:STATUS_INDEX] for t in table_list]
            actual = is_mylist_include_new_video(table_list)
            self.assertEqual(False, actual)

        # 状況ステータスの位置が異なる
        with self.assertRaises(KeyError):
            table_list = table_list_factory()
            table_list = [[t[-1]] + t[:-1] for t in table_list]
            actual = is_mylist_include_new_video(table_list)
            self.assertEqual(False, actual)
        pass

    def test_interval_translate(self):
        """インターバルを解釈する関数のテスト
        """
        # 正常系
        # 分
        e_val = random.randint(1, 59)
        interval_str = f"{e_val}分"
        actual = interval_translate(interval_str)
        expect = e_val
        self.assertEqual(expect, actual)

        # 時間
        e_val = random.randint(1, 23)
        interval_str = f"{e_val}時間"
        actual = interval_translate(interval_str)
        expect = e_val * 60
        self.assertEqual(expect, actual)

        # 日
        e_val = random.randint(1, 31)
        interval_str = f"{e_val}日"
        actual = interval_translate(interval_str)
        expect = e_val * 60 * 24
        self.assertEqual(expect, actual)

        # 週間
        e_val = random.randint(1, 5)
        interval_str = f"{e_val}週間"
        actual = interval_translate(interval_str)
        expect = e_val * 60 * 24 * 7
        self.assertEqual(expect, actual)

        # 月
        e_val = random.randint(1, 12)
        interval_str = f"{e_val}ヶ月"
        actual = interval_translate(interval_str)
        expect = e_val * 60 * 24 * 31
        self.assertEqual(expect, actual)

        # 異常系
        interval_str = "不正なinterval_str"
        actual = interval_translate(interval_str)
        expect = -1
        self.assertEqual(expect, actual)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
