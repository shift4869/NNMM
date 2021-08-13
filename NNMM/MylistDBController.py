# coding: utf-8
import re
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM.DBControllerBase import DBControllerBase
from NNMM.Model import *


DEBUG = False


class MylistDBController(DBControllerBase):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        super().__init__(db_fullpath)

    def GetListname(self, url, username, old_showname) -> str:
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
        if re.search(pattern, url):
            return f"{username}さんの投稿動画"

        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, url):
            # TODO::マイリスト名の一部のみしか反映できていない
            res_str = re.sub("-(.*)さんのマイリスト", f"-{username}さんのマイリスト", old_showname)
            return res_str
        return ""

    def Upsert(self, id, username, mylistname, type, showname, url, created_at, updated_at, updated_interval, is_include_new):
        """MylistにUPSERTする

        Notes:
            追加しようとしているレコードが既存テーブルに存在しなければINSERT
            存在しているならばUPDATE(DELETE->INSERT)
            一致しているかの判定はurlが一致している場合、とする

        Args:
            username (str): 投稿者名
            mylistname (str): マイリスト名
            type (str): マイリストのタイプ({"uploaded", "mylist", "series"})
            showname (str): マイリストの一意名({username}_{type})
                            typeが"uploaded"の場合："{username}さんの投稿動画"
            url (str): マイリストURL
            created_at (str): 作成日時
            updated_at (str): 更新日時
            updated_interval (str): 最低更新間隔
            is_include_new (boolean): 未視聴動画を含むかどうか

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        res = -1

        r = Mylist(id, username, mylistname, type, showname, url, created_at, updated_at, updated_interval, is_include_new)

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
        session.close()

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
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()

        # 存在しない場合はエラー
        if not record:
            session.close()
            return -1

        # 更新前と更新後のstatusが同じ場合は何もせずに終了
        if record.is_include_new == is_include_new:
            session.close()
            return 0

        # 更新する
        record.is_include_new = is_include_new

        session.commit()
        session.close()

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
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()

        # 存在しない場合はエラー
        if not record:
            session.close()
            return -1

        # 更新する
        record.updated_at = updated_at

        session.commit()
        session.close()

        return 0

    def UpdateUsername(self, mylist_url, now_username):
        """Mylistの特定のレコードについてusernameを更新する

        Note:
            "update Mylist set username = {now_username} where url = {mylist_url}"
            shownameも更新する

        Args:
            mylist_url (str): マイリストURL
            now_username (str): 変更後のusername

        Returns:
            int: usernameを更新した場合0, その他失敗時-1
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        # 対象レコード
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()
        if not record:
            session.close()
            return -1
        record.username = now_username
        record.showname = self.GetListname(mylist_url, now_username, record.showname)

        session.commit()
        session.close()
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
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

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
        session.close()
        return res

    def DeleteFromURL(self, mylist_url):
        # DELETE対象をSELECT
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()

        # 存在しない場合はエラー
        if not record:
            session.close()
            return 1

        # DELETEする
        session.delete(record)

        session.commit()
        session.close()
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
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        res = session.query(Mylist).order_by(asc(Mylist.id)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromShowname(self, showname):
        """Mylistからshownameを条件としてSELECTする

        Note:
            "select * from Mylist where showname = {}".format(showname)

        Args:
            showname (str): 取得対象のマイリスト一意名

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        res = session.query(Mylist).filter_by(showname=showname).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
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
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        res = session.query(Mylist).filter_by(url=url).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict


if __name__ == "__main__":
    DEBUG = True
    db_fullpath = Path("NNMM_DB.db")
    mylist_db = MylistDBController(db_fullpath=str(db_fullpath))

    # td_format = "%Y/%m/%d %H:%M"
    # dts_format = "%Y-%m-%d %H:%M:%S"
    # dst = datetime.now().strftime(dts_format)
    url = "https://www.nicovideo.jp/user/12899156/video"
    # mylist_db.Upsert(1, "willow8713", "uploaded", "willow8713さんの投稿動画", url, dst, dst, true)

    # url = "https://www.nicovideo.jp/user/1594318/video"
    # mylist_db.Upsert(2, "moco78", "uploaded", "moco78さんの投稿動画", url, dst, dst, true)

    records = mylist_db.Select()
    mylist_db.UpdateIncludeFlag(url, False)
    pass
