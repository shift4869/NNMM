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


class MylistInfoDBCM(DBControllerBase):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        super().__init__(db_fullpath)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def __del__(self):
        self.session.commit()
        self.session.close()

    def Upsert(self, video_id, title, username, status, uploaded_at, video_url, mylist_url, created_at):
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
            uploaded_at (str): 動画投稿日時
            video_url (str): 動画URL
            mylist_url (str): 所属マイリストURL
            created_at (str): 作成日時

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        session = self.session
        res = -1

        r = MylistInfo(video_id, title, username, status, uploaded_at, video_url, mylist_url, created_at)

        try:
            q = session.query(MylistInfo).filter(and_(MylistInfo.video_id == r.video_id, MylistInfo.mylist_url == r.mylist_url))
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

        return res

    def UpsertFromList(self, records):
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
                    uploaded_at (str): 動画投稿日時
                    video_url (str): 動画URL
                    mylist_url (str): 所属マイリストURL
                    created_at (str): 作成日時

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        session = self.session
        res = -1

        # 既に存在しているレコードは削除しておく
        for record in records:
            video_id = record.get("video_id")
            mylist_url = record.get("mylist_url")

            try:
                q = session.query(MylistInfo).filter(and_(MylistInfo.video_id == video_id, MylistInfo.mylist_url == mylist_url))
                ex = q.one()
            except NoResultFound:
                pass
            else:
                # UPDATEは実質DELETE->INSERTと同じとする
                session.delete(ex)
                res = 1

        session.commit()

        # レコード登録
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
                q = session.query(MylistInfo).filter(and_(MylistInfo.video_id == r.video_id, MylistInfo.mylist_url == r.mylist_url))
                ex = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                res = 0
            else:
                res = -1
                raise SQLAlchemyError

        session.commit()

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
        session = self.session
        record = session.query(MylistInfo).filter(
            and_(MylistInfo.video_id == video_id, MylistInfo.mylist_url == mylist_url)
        ).first()

        # 存在しない場合はエラー
        if not record:
            return 1

        # 更新前と更新後のstatusが同じ場合は何もせずに終了
        if record.status == status:
            return 0

        # 更新する
        record.status = status

        session.commit()

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
        session = self.session
        records = session.query(MylistInfo).filter(
            MylistInfo.mylist_url == mylist_url
        )

        # 1件も存在しない場合はエラー
        if not records:
            return 1

        for record in records:
            # 更新前と更新後のstatusが同じ場合は何もしない
            if record.status == status:
                continue

            # 更新する
            record.status = status

        session.commit()

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
        session = self.session
        records = session.query(MylistInfo).filter(
            MylistInfo.mylist_url == mylist_url
        )

        # 1件も存在しない場合はエラー
        if not records:
            return 1

        for record in records:
            record.username = username

        session.commit()

        return 0

    def DeleteFromMylistURL(self, mylist_url):
        # DELETE対象をSELECT
        session = self.session
        records = session.query(MylistInfo).filter(MylistInfo.mylist_url == mylist_url).first()

        # 存在しない場合はエラー
        if not records:
            return 1

        # DELETEする
        session.query(MylistInfo).filter(MylistInfo.mylist_url == mylist_url).delete()

        session.commit()
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
        session = self.session

        res = session.query(MylistInfo).order_by(asc(MylistInfo.created_at)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

        return res_dict

    def SelectFromVideoID(self, video_id):
        """MylistInfoからvideo_idを条件としてSELECTする

        Note:
            "select * from MylistInfo where video_id = {}".format(video_id)
            複数マイリストの同じ動画がそれぞれ登録されていた場合、複数SELECTされ得る

        Args:
            video_id (str): 取得対象の動画ID

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        session = self.session

        res = session.query(MylistInfo).filter_by(video_id=video_id).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

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
        session = self.session

        res = session.query(MylistInfo).filter_by(video_url=video_url).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

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
        session = self.session

        # res = session.query(MylistInfo).filter_by(mylist_url=mylist_url).order_by(desc(MylistInfo.video_id)).all()
        res = session.query(MylistInfo).filter_by(mylist_url=mylist_url).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

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
        session = self.session

        res = session.query(MylistInfo).filter_by(username=username).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        # 動画IDでソート
        res_dict.sort(key=lambda x: int(str(x["video_id"]).replace("sm", "")), reverse=True)

        return res_dict


class MylistDBCM(DBControllerBase):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        super().__init__(db_fullpath)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def __del__(self):
        self.session.commit()
        self.session.close()

    def GetListname(self, url, username, old_listname) -> str:
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
        if re.search(pattern, url):
            return f"{username}さんの投稿動画"

        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, url):
            # TODO::マイリスト名の一部のみしか反映できていない
            res_str = re.sub("-(.*)さんのマイリスト", f"-{username}さんのマイリスト", old_listname)
            return res_str
        return ""

    def Upsert(self, id, username, type, listname, url, created_at, updated_at, is_include_new):
        """MylistにUPSERTする

        Notes:
            追加しようとしているレコードが既存テーブルに存在しなければINSERT
            存在しているならばUPDATE(DELETE->INSERT)
            一致しているかの判定はurlが一致している場合、とする

        Args:
            username (str): 投稿者名
            type (str): マイリストのタイプ({"uploaded", "mylist", "series"})
            listname (str): マイリストの一意名({username}_{type})
                            typeが"uploaded"の場合："{username}さんの投稿動画"
            url (str): マイリストURL
            created_at (str): 作成日時
            updated_at (str): 更新日時
            is_include_new (boolean): 未視聴動画を含むかどうか

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        session = self.session
        res = -1

        r = Mylist(id, username, type, listname, url, created_at, updated_at, is_include_new)

        try:
            q = session.query(Mylist).filter(or_(Mylist.url == r.url))
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

        return res

    def UpdateIncludeFlag(self, mylist_url, is_include_new=False):
        """Mylistの特定のレコードについて新着フラグを更新する

        Note:
            "update Mylist set is_include_new = {} where mylist_url = {}"

        Args:
            mylist_url (str): マイリストURL
            is_include_new (boolean): 変更後の新着フラグ

        Returns:
            int: 新着フラグを更新した場合0, その他失敗時-1
        """
        # UPDATE対象をSELECT
        session = self.session
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()

        # 存在しない場合はエラー
        if not record:
            return -1

        # 更新前と更新後のstatusが同じ場合は何もせずに終了
        if record.is_include_new == is_include_new:
            return 0

        # 更新する
        record.is_include_new = is_include_new

        session.commit()

        return 0

    def UpdateUpdatedAt(self, mylist_url, updated_at):
        """Mylistの特定のレコードについて更新日時を更新する

        Note:
            "update Mylist set updated_at = {} where mylist_url = {}"

        Args:
            mylist_url (str): マイリストURL
            updated_at (str): 変更後の更新日時："%Y-%m-%d %H:%M:%S" 形式

        Returns:
            int: 更新日時を更新した場合0, その他失敗時-1
        """
        # UPDATE対象をSELECT
        session = self.session
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()

        # 存在しない場合はエラー
        if not record:
            return -1

        # 更新する
        record.updated_at = updated_at

        session.commit()

        return 0

    def UpdateUsername(self, mylist_url, now_username):
        """Mylistの特定のレコードについてusernameを更新する

        Note:
            "update Mylist set username = {now_username} where url = {mylist_url}"
            listnameも更新する

        Args:
            mylist_url (str): マイリストURL
            now_username (str): 変更後のusername

        Returns:
            int: usernameを更新した場合0, その他失敗時-1
        """
        session = self.session

        # 対象レコード
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()
        if not record:
            return -1
        record.username = now_username
        record.listname = self.GetListname(mylist_url, now_username, record.listname)

        session.commit()
        return 0

    def SwapId(self, src_id, dst_id):
        """idを交換する

        Note:
            idはプライマリキーなので一度連番でないものを割り当ててから交換する

        Args:
            src_id (int): 交換元レコードのid
            dst_id (int): 交換先レコードのid

        Returns:
            (Mylist, Mylist): 交換後のレコード（交換元レコード, 交換先レコード）
        """
        session = self.session

        # 交換元レコード
        src_record = session.query(Mylist).filter(Mylist.id == src_id).first()
        # 交換先レコード
        dst_record = session.query(Mylist).filter(Mylist.id == dst_id).first()

        # 一旦idを重複しないものに変更する（マイナス）
        src_record.id = -src_id
        dst_record.id = -dst_id
        session.commit()

        # idを交換する
        src_record.id = dst_id
        dst_record.id = src_id

        # 返り値作成
        res = (src_record.toDict(), dst_record.toDict())

        # セッション終了
        session.commit()
        return res

    def DeleteFromURL(self, mylist_url):
        # DELETE対象をSELECT
        session = self.session
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()

        # 存在しない場合はエラー
        if not record:
            return 1

        # DELETEする
        session.delete(record)

        session.commit()
        return 0

    def Select(self):
        """MylistからSELECTする

        Note:
            "select * from Mylist order by created_at asc"

        Args:
            limit (int): 取得レコード数上限

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        session = self.session

        # res = session.query(Mylist).order_by(asc(Mylist.created_at)).limit(limit).all()
        res = session.query(Mylist).order_by(asc(Mylist.id)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        return res_dict

    def SelectFromListname(self, listname):
        """Mylistからlistnameを条件としてSELECTする

        Note:
            "select * from Mylist where listname = {}".format(listname)

        Args:
            listname (str): 取得対象のマイリスト一意名

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        session = self.session

        res = session.query(Mylist).filter_by(listname=listname).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        return res_dict

    def SelectFromURL(self, url):
        """Mylistからurlを条件としてSELECTする

        Note:
            "select * from Mylist where url = {}".format(url)

        Args:
            url (str): 取得対象のマイリストurl

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        session = self.session

        res = session.query(Mylist).filter_by(url=url).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        return res_dict


if __name__ == "__main__":
    DEBUG = True
    db_fullpath = Path("NNMM_DB.db")
    mylist_info_db = MylistInfoDBCM(db_fullpath=str(db_fullpath))

    records = mylist_info_db.Select()
    video_id = "sm38859846"
    mylist_url = "https://www.nicovideo.jp/user/12899156/video"
    res = mylist_info_db.UpdateStatus(video_id, mylist_url, "")
    pass
