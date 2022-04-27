# coding: utf-8
import re
import time
import traceback
from pathlib import Path

import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM.DBControllerBase import DBControllerBase
from NNMM.Model import *


DEBUG = False


class MylistInfoDBController(DBControllerBase):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        super().__init__(db_fullpath)

    def Upsert(self, video_id: str, title: str, username: str, status: str,
               uploaded_at: str, registered_at: str, video_url: str, mylist_url: str, created_at: str) -> int:
        """MylistInfoにUPSERTする

        Notes:
            追加しようとしているレコードが既存テーブルに存在しなければINSERT
            存在しているならばUPDATE(DELETE->INSERT)
            一致しているかの判定はvideo_urlとmylist_urlの組が一致している場合、とする

        Args:
            video_id (str): 動画ID(smxxxxxxxx)
            title (str): 動画タイトル
            username (str): 投稿者名
            status (str): 視聴状況({"未視聴", "視聴済"})
            uploaded_at (str): 投稿日時
            registered_at (str): 登録日時
            video_url (str): 動画URL
            mylist_url (str): 所属マイリストURL
            created_at (str): 作成日時

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        res = -1

        r = MylistInfo(video_id, title, username, status, uploaded_at, registered_at, video_url, mylist_url, created_at)

        try:
            q = session.query(MylistInfo).filter(and_(MylistInfo.video_id == r.video_id, MylistInfo.mylist_url == r.mylist_url))
            p = q.one()
        except sqlalchemy.orm.exc.NoResultFound:
            # INSERT
            session.add(r)
            res = 0
        else:
            # UPDATE
            p.video_id = r.video_id
            p.title = r.title
            p.username = r.username
            p.status = r.status
            p.uploaded_at = r.uploaded_at
            p.registered_at = r.registered_at
            p.video_url = r.video_url
            p.mylist_url = r.mylist_url
            p.created_at = r.created_at
            res = 1

        session.commit()
        session.close()

        return res

    def UpsertFromList(self, records: list[dict]) -> int:
        """MylistInfoにUPSERTする

        Notes:
            追加しようとしているレコードが既存テーブルに存在しなければINSERT
            存在しているならばUPDATE(DELETE->INSERT)
            一致しているかの判定はvideo_idとmylist_urlの組が一致している場合、とする

        Args:
            以下をキーとするrecordのlistを引数としてとる
            records = list(dict)
                dict Keys
                    video_id (str): 動画ID(smxxxxxxxx)
                    title (str): 動画タイトル
                    username (str): 投稿者名
                    status (str): 視聴状況({"未視聴", "視聴済"})
                    uploaded_at (str): 投稿日時
                    registered_at (str): 登録日時
                    video_url (str): 動画URL
                    mylist_url (str): 所属マイリストURL
                    created_at (str): 作成日時

        Returns:
            int: 0(成功,すべて新規追加の場合), 1(成功,1つでも更新したレコードがある場合), other(失敗)
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        r_res = []

        # レコード登録
        success = False
        try:
            for record in records:
                video_id = record.get("video_id")
                title = record.get("title")
                username = record.get("username")
                status = record.get("status")
                uploaded_at = record.get("uploaded_at")
                registered_at = record.get("registered_at")
                video_url = record.get("video_url")
                mylist_url = record.get("mylist_url")
                created_at = record.get("created_at")

                r = MylistInfo(video_id, title, username, status, uploaded_at, registered_at, video_url, mylist_url, created_at)

                try:
                    q = session.query(MylistInfo).filter(and_(MylistInfo.video_id == r.video_id, MylistInfo.mylist_url == r.mylist_url))
                    p = q.with_for_update().one()
                except sqlalchemy.orm.exc.NoResultFound:
                    # INSERT
                    session.add(r)
                    r_res.append(0)
                else:
                    # UPDATE
                    p.video_id = r.video_id
                    p.title = r.title
                    p.username = r.username
                    p.status = r.status
                    p.uploaded_at = r.uploaded_at
                    p.registered_at = r.registered_at
                    p.video_url = r.video_url
                    p.mylist_url = r.mylist_url
                    p.created_at = r.created_at
                    r_res.append(1)

            session.commit()
            success = true
        except Exception as e:
            # commitに失敗した場合は何もしないで終了させる
            # TODO::何かうまい処理を考える
            time.sleep(1)
            print(traceback.format_exc())
            pass

        session.close()

        if len(r_res) == 0:
            return -1

        res = 1 if r_res.count(1) > 0 else 0
        return res

    def UpdateStatus(self, video_id: str, mylist_url: str, status: str = "") -> int:
        """MylistInfoの特定のレコードについてstatusを更新する

        Note:
            "update MylistInfo set status = {} where video_id = {} and mylist_url = {}"

        Args:
            video_id (str): 動画ID(smxxxxxxxx)
            mylist_url (str): 所属マイリストURL
            status (str): 変更後の視聴状況({"未視聴", ""})

        Returns:
            int: statusを更新した場合0, 対象レコードが存在しなかった場合1, その他失敗時-1
        """
        # 入力値チェック
        if status not in ["未視聴", ""]:
            return -1

        pattern = "sm[0-9]+"
        if not re.search(pattern, video_id):
            return -1

        # UPDATE対象をSELECT
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        record = session.query(MylistInfo).filter(
            and_(MylistInfo.video_id == video_id, MylistInfo.mylist_url == mylist_url)
        ).with_for_update().first()

        # 存在しない場合はエラー
        if not record:
            session.close()
            return 1

        # 更新前と更新後のstatusが同じ場合は何もせずに終了
        if record.status == status:
            session.close()
            return 0

        # 更新する
        record.status = status

        session.commit()
        session.close()

        return 0

    def UpdateStatusInMylist(self, mylist_url: str, status: str = "") -> int:
        """MylistInfoについて特定のマイリストに含まれるレコードのstatusをすべて更新する

        Note:
            "update MylistInfo set status = {status} where mylist_url = {mylist_url}"

        Args:
            mylist_url (str): 所属マイリストURL
            status (str): 変更後の視聴状況({"未視聴", ""})

        Returns:
            int: statusをすべて更新した場合0, 対象レコードが存在しなかった場合1, その他失敗時-1
        """
        # 入力値チェック
        if status not in ["未視聴", ""]:
            return -1

        # UPDATE対象をSELECT
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        records = session.query(MylistInfo).filter(
            MylistInfo.mylist_url == mylist_url
        ).with_for_update()

        # 1件も存在しない場合はエラー
        if not records.first():
            session.close()
            return 1

        for record in records:
            # 更新前と更新後のstatusが同じ場合は何もしない
            if record.status == status:
                continue

            # 更新する
            record.status = status

        session.commit()
        session.close()

        return 0

    def UpdateUsernameInMylist(self, mylist_url: str, username: str) -> int:
        """MylistInfoについて特定のマイリストに含まれるレコードのusernameをすべて更新する

        Note:
            "update MylistInfo set username = {username} where mylist_url = {mylist_url}"

        Args:
            mylist_url (str): マイリストURL
            username (str): 変更後のusername

        Returns:
            int: usernameを更新した場合0, 対象レコードが存在しなかった場合1, その他失敗時-1
        """
        # UPDATE対象をSELECT
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        records = session.query(MylistInfo).filter(
            MylistInfo.mylist_url == mylist_url
        ).with_for_update()

        # 1件も存在しない場合はエラー
        if not records.first():
            session.close()
            return 1

        for record in records:
            record.username = username

        session.commit()
        session.close()

        return 0

    def DeleteFromMylistURL(self, mylist_url: str) -> int:
        """MylistInfoについて特定のマイリストに含まれるレコードをすべて削除する

        Note:
            "delete from MylistInfo where mylist_url = {mylist_url}"

        Args:
            mylist_url (str): 削除対象のマイリストURL

        Returns:
            int: 削除成功した場合0, 1件も対象レコードが存在しなかった場合1, その他失敗時-1
        """
        # DELETE対象をSELECT
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        records = session.query(MylistInfo).filter(MylistInfo.mylist_url == mylist_url).with_for_update()

        # 存在しない場合はエラー
        if not records.first():
            session.close()
            return 1

        # DELETEする
        session.query(MylistInfo).filter(MylistInfo.mylist_url == mylist_url).with_for_update().delete()

        session.commit()
        session.close()
        return 0

    def Select(self) -> list[dict]:
        """MylistInfoからSELECTする

        Note:
            "select * from MylistInfo order by created_at asc"

        Args:
            limit (int): 取得レコード数上限

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        res = session.query(MylistInfo).order_by(asc(MylistInfo.created_at)).with_for_update().all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

        session.close()
        return res_dict

    def SelectFromVideoID(self, video_id: str) -> list[dict]:
        """MylistInfoからvideo_idを条件としてSELECTする

        Note:
            "select * from MylistInfo where video_id = {}".format(video_id)
            複数マイリストの同じ動画がそれぞれ登録されていた場合、複数SELECTされ得る

        Args:
            video_id (str): 取得対象の動画ID

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        res = session.query(MylistInfo).filter_by(video_id=video_id).with_for_update().all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

        session.close()
        return res_dict

    def SelectFromIDURL(self, video_id: str, mylist_url: str) -> list[dict]:
        """MylistInfoからvideo_idとmylist_urlを条件としてSELECTする

        Note:
            f"select * from MylistInfo where video_id = {video_id} and mylist_url = {mylist_url}"
            (video_id, mylist_url)をキーとするためSelectされるレコードはユニークである想定

        Args:
            video_id (str): 取得対象の動画ID
            mylist_url (str): 取得対象の所属マイリストURL

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        res = session.query(MylistInfo).filter(
            and_(MylistInfo.video_id == video_id, MylistInfo.mylist_url == mylist_url)
        ).with_for_update().all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromVideoURL(self, video_url: str) -> list[dict]:
        """MylistInfoからvideo_urlを条件としてSELECTする

        Note:
            "select * from MylistInfo where video_url = {}".format(video_url)

        Args:
            video_url (str): 取得対象のマイリストvideo_url

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        res = session.query(MylistInfo).filter_by(video_url=video_url).with_for_update().all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

        session.close()
        return res_dict

    def SelectFromMylistURL(self, mylist_url: str) -> list[dict]:
        """MylistInfoからmylist_urlを条件としてSELECTする

        Note:
            "select * from MylistInfo where mylist_url = {}".format(mylist_url)

        Args:
            mylist_url (str): 取得対象の所属マイリストURL

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        # res = session.query(MylistInfo).filter_by(mylist_url=mylist_url).order_by(desc(MylistInfo.video_id)).all()
        res = session.query(MylistInfo).filter_by(mylist_url=mylist_url).with_for_update().all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

        session.close()
        return res_dict

    def SelectFromUsername(self, username: str) -> list[dict]:
        """MylistInfoからusernameを条件としてSELECTする

        Note:
            "select * from MylistInfo where username = {}".format(username)

        Args:
            username (str): 取得対象のusername

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        res = session.query(MylistInfo).filter_by(username=username).with_for_update().all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

        session.close()
        return res_dict


if __name__ == "__main__":
    db_fullpath = Path("test.db")
    mylist_info_db = MylistInfoDBController(db_fullpath=str(db_fullpath))

    if db_fullpath.is_file():
        db_fullpath.unlink()
    pass
