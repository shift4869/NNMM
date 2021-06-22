# coding: utf-8
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import *
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM.DBControllerBase import DBControllerBase
from NNMM.Model import *


DEBUG = False


class MylistInfoDBController(DBControllerBase):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        super().__init__(db_fullpath)

    def Upsert(self, video_id, title, username, status, uploaded_at, video_url, mylist_url, created_at):
        """MylistInfoにUPSERTする

        Notes:
            追加しようとしているレコードが既存テーブルに存在しなければINSERT
            存在しているならばUPDATE(DELETE->INSERT)
            一致しているかの判定はvideo_urlが一致している場合、とする

        Args:
            video_id (str): 動画ID(smxxxxxxxx)
            title (str): 動画タイトル
            username (str): 投稿者名
            status (str): 視聴状況({"未視聴", "視聴済"})
            uploaded_at (str): 動画投稿日時
            video_url (str): 動画URL
            mylist_url (str): 所属マイリストURL
            created_at (str): 作成日時

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        res = -1

        r = MylistInfo(video_id, title, username, status, uploaded_at, video_url, mylist_url, created_at)

        try:
            q = session.query(MylistInfo).filter(or_(MylistInfo.video_id == r.video_id))
            ex = q.one()
        except NoResultFound:
            # INSERT
            session.add(r)
            res = 0
        else:
            # UPDATEは実質DELETE->INSERTと同じとする
            session.delete(ex)
            session.commit()
            session.add(r)
            res = 1

        session.commit()
        session.close()

        return res

    def UpsertFromList(self, records):
        """MylistInfoにUPSERTする

        Notes:
            追加しようとしているレコードが既存テーブルに存在しなければINSERT
            存在しているならばUPDATE(DELETE->INSERT)
            一致しているかの判定はvideo_urlが一致している場合、とする

        Args:
            以下のArgsをキーとするrecordのlistを引数としてとる
            records = list(dict)
                dict Keys
                    video_id (str): 動画ID(smxxxxxxxx)
                    title (str): 動画タイトル
                    username (str): 投稿者名
                    status (str): 視聴状況({"未視聴", "視聴済"})
                    uploaded_at (str): 動画投稿日時
                    video_url (str): 動画URL
                    mylist_url (str): 所属マイリストURL
                    created_at (str): 作成日時

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        res = -1

        for record in records:
            video_id = record.get("video_id")
            title = record.get("title")
            username = record.get("username")
            status = record.get("status")
            uploaded_at = record.get("uploaded_at")
            video_url = record.get("video_url")
            mylist_url = record.get("mylist_url")
            created_at = record.get("created_at")

            r = MylistInfo(video_id, title, username, status, uploaded_at, video_url, mylist_url, created_at)

            try:
                q = session.query(MylistInfo).filter(or_(MylistInfo.video_id == r.video_id))
                ex = q.one()
            except NoResultFound:
                pass
            else:
                # UPDATEは実質DELETE->INSERTと同じとする
                session.delete(ex)
                res = 1

        session.commit()

        for record in records:
            video_id = record.get("video_id")
            title = record.get("title")
            username = record.get("username")
            status = record.get("status")
            uploaded_at = record.get("uploaded_at")
            video_url = record.get("video_url")
            mylist_url = record.get("mylist_url")
            created_at = record.get("created_at")

            r = MylistInfo(video_id, title, username, status, uploaded_at, video_url, mylist_url, created_at)

            try:
                q = session.query(MylistInfo).filter(or_(MylistInfo.video_id == r.video_id))
                ex = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                res = 0
            else:
                res = -1
                raise SQLAlchemyError

        session.commit()
        session.close()

        return res

    def UpdateStatus(self, video_id, mylist_url, status=""):
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
        Session = sessionmaker(bind=self.engine)
        session = Session()
        record = session.query(MylistInfo).filter(
            and_(MylistInfo.video_id == video_id, MylistInfo.mylist_url == mylist_url)
        ).first()

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

    def UpdateStatusInMylist(self, mylist_url, status=""):
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
        Session = sessionmaker(bind=self.engine)
        session = Session()
        records = session.query(MylistInfo).filter(
            MylistInfo.mylist_url == mylist_url
        )

        # 1件も存在しない場合はエラー
        if not records:
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

    def UpdateUsernameInMylist(self, mylist_url, username):
        """MylistInfoについて特定のマイリストに含まれるレコードのusernameをすべて更新する

        Note:
            "update MylistInfo set username = {username} where mylist_url = {mylist_url}"
            listnameも更新する

        Args:
            mylist_url (str): マイリストURL
            username (str): 変更後のusername

        Returns:
            int: usernameを更新した場合0, 対象レコードが存在しなかった場合1, その他失敗時-1
        """
        # UPDATE対象をSELECT
        Session = sessionmaker(bind=self.engine)
        session = Session()
        records = session.query(MylistInfo).filter(
            MylistInfo.mylist_url == mylist_url
        )

        # 1件も存在しない場合はエラー
        if not records:
            session.close()
            return 1

        for record in records:
            record.username = username

        session.commit()
        session.close()

        return 0

    def DeleteFromMylistURL(self, mylist_url):
        # DELETE対象をSELECT
        Session = sessionmaker(bind=self.engine)
        session = Session()
        records = session.query(MylistInfo).filter(MylistInfo.mylist_url == mylist_url).first()

        # 存在しない場合はエラー
        if not records:
            session.close()
            return 1

        # DELETEする
        session.query(MylistInfo).filter(MylistInfo.mylist_url == mylist_url).delete()

        session.commit()
        session.close()
        return 0

    def Select(self):
        """MylistInfoからSELECTする

        Note:
            "select * from MylistInfo order by created_at asc"

        Args:
            limit (int): 取得レコード数上限

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(MylistInfo).order_by(asc(MylistInfo.created_at)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromVideoID(self, video_id):
        """MylistInfoからvideo_idを条件としてSELECTする

        Note:
            "select * from MylistInfo where video_id = {}".format(video_id)

        Args:
            video_id (str): 取得対象の動画ID

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(MylistInfo).filter_by(video_id=video_id).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromVideoURL(self, video_url):
        """MylistInfoからvideo_urlを条件としてSELECTする

        Note:
            "select * from MylistInfo where video_url = {}".format(video_url)

        Args:
            video_url (str): 取得対象のマイリストvideo_url

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(MylistInfo).filter_by(video_url=video_url).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromMylistURL(self, mylist_url):
        """MylistInfoからmylist_urlを条件としてSELECTする

        Note:
            "select * from MylistInfo where mylist_url = {}".format(mylist_url)

        Args:
            mylist_url (str): 取得対象の所属マイリストURL

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(MylistInfo).filter_by(mylist_url=mylist_url).order_by(desc(MylistInfo.video_id)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromUsername(self, username):
        """MylistInfoからusernameを条件としてSELECTする

        Note:
            "select * from MylistInfo where username = {}".format(username)

        Args:
            username (str): 取得対象のusername

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(MylistInfo).filter_by(username=username).order_by(desc(MylistInfo.video_id)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict


if __name__ == "__main__":
    DEBUG = True
    db_fullpath = Path("NNMM_DB.db")
    mylist_info_db = MylistInfoDBController(db_fullpath=str(db_fullpath))

    records = mylist_info_db.Select()
    video_id = "sm38859846"
    mylist_url = "https://www.nicovideo.jp/user/12899156/video"
    res = mylist_info_db.UpdateStatus(video_id, mylist_url, "")
    pass
