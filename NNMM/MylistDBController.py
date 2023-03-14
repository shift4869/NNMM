# coding: utf-8
import re
from pathlib import Path

import sqlalchemy
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM.DBControllerBase import DBControllerBase
from NNMM.Model import *

DEBUG = False


class MylistDBController(DBControllerBase):
    def __init__(self, db_fullpath: str = "NNMM_DB.db"):
        super().__init__(db_fullpath)

    def GetListname(self, url: str, username: str, old_showname: str) -> str:
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
        if re.search(pattern, url):
            return f"{username}さんの投稿動画"

        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        if re.search(pattern, url):
            # TODO::マイリスト名の一部のみしか反映できていない
            res_str = re.sub("-(.*)さんのマイリスト", f"-{username}さんのマイリスト", old_showname)
            return res_str
        return ""

    def Upsert(self, id: int, username: str, mylistname: str, type: str, showname: str, url: str,
               created_at: str, updated_at: str, checked_at: str, check_interval: str, is_include_new: bool) -> int:
        """MylistにUPSERTする

        Notes:
            追加しようとしているレコードが既存テーブルに存在しなければINSERT
            存在しているならばUPDATE(DELETE->INSERT)
            一致しているかの判定はurlが一致している場合、とする
            UPDATEの場合、idは更新しない

        Args:
            id (int): ID
            username (str): 投稿者名
            mylistname (str): マイリスト名
            type (str): マイリストのタイプ({"uploaded", "mylist", "series"})
            showname (str): マイリストの一意名({username}_{type})
                            typeが"uploaded"の場合："{username}さんの投稿動画"
                            typeが"mylist"の場合："「{mylistname}」-{username}さんのマイリスト"
            url (str): マイリストURL
            created_at (str): 作成日時("%Y-%m-%d %H:%M:%S")
            updated_at (str): 更新日時("%Y-%m-%d %H:%M:%S")
            checked_at (str): 更新確認日時("%Y-%m-%d %H:%M:%S")
            check_interval (str): 最低更新間隔
            is_include_new (boolean): 未視聴動画を含むかどうか

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), -1(失敗)
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        res = -1

        r = Mylist(id, username, mylistname, type, showname, url, created_at, updated_at, checked_at, check_interval, is_include_new)

        try:
            q = session.query(Mylist).filter(or_(Mylist.url == r.url)).with_for_update()
            p = q.one()
        except sqlalchemy.orm.exc.NoResultFound:
            # INSERT
            session.add(r)
            res = 0
        else:
            # UPDATE
            # id以外を更新する
            p.username = r.username
            p.mylistname = r.mylistname
            p.type = r.type
            p.showname = r.showname
            p.url = r.url
            p.created_at = r.created_at
            p.updated_at = r.updated_at
            p.checked_at = r.checked_at
            p.check_interval = r.check_interval
            p.is_include_new = r.is_include_new
            res = 1

        session.commit()
        session.close()

        return res

    def UpdateIncludeFlag(self, mylist_url: str, is_include_new: bool = False) -> int:
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
        record = session.query(Mylist).filter(Mylist.url == mylist_url).with_for_update().first()

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

    def UpdateUpdatedAt(self, mylist_url: str, updated_at: str) -> int:
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
        record = session.query(Mylist).filter(Mylist.url == mylist_url).with_for_update().first()

        # 存在しない場合はエラー
        if not record:
            session.close()
            return -1

        # 更新する
        record.updated_at = updated_at

        session.commit()
        session.close()

        return 0

    def UpdateCheckedAt(self, mylist_url: str, checked_at: str) -> int:
        """Mylistの特定のレコードについて更新確認日時を更新する

        Note:
            "update Mylist set checked_at = {} where mylist_url = {}"

        Args:
            mylist_url (str): マイリストURL
            checked_at (str): 変更後の更新確認日時："%Y-%m-%d %H:%M:%S" 形式

        Returns:
            int: 更新確認日時を更新した場合0, その他失敗時-1
        """
        # UPDATE対象をSELECT
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        record = session.query(Mylist).filter(Mylist.url == mylist_url).with_for_update().first()

        # 存在しない場合はエラー
        if not record:
            session.close()
            return -1

        # 更新する
        record.checked_at = checked_at

        session.commit()
        session.close()

        return 0

    def UpdateUsername(self, mylist_url: str, now_username: str) -> int:
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
        record = session.query(Mylist).filter(Mylist.url == mylist_url).with_for_update().first()
        if not record:
            session.close()
            return -1
        record.username = now_username
        record.showname = self.GetListname(mylist_url, now_username, record.showname)

        session.commit()
        session.close()
        return 0

    def SwapId(self, src_id: int, dst_id: int) -> tuple[dict, dict]:
        """idを交換する

        Note:
            idはプライマリキーなので一度連番でないものを割り当ててから交換する

        Args:
            src_id (int): 交換元レコードのid
            dst_id (int): 交換先レコードのid

        Returns:
            (Mylist, Mylist): 交換後のレコード(交換元レコード, 交換先レコード)、エラー時(None, None)
        """
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        # 交換元と交換先が同じだった場合は処理を行わない(エラー扱い)
        if src_id == dst_id:
            session.close()
            return (None, None)

        # 交換元レコード
        src_record = session.query(Mylist).filter(Mylist.id == src_id).first()
        # 交換先レコード
        dst_record = session.query(Mylist).filter(Mylist.id == dst_id).first()

        # 交換元か交換先のレコードがどちらかでも存在していなかった場合はエラー
        # idが[0, Mylistの総レコード数]の範囲外にある場合もこの条件に当てはまる
        if (src_record is None) or (dst_record is None):
            session.close()
            return (None, None)

        # 一旦idを重複しないものに変更する（マイナス）
        src_record.id = -src_id
        dst_record.id = -dst_id
        session.commit()

        # idを交換する
        src_record.id = dst_id
        dst_record.id = src_id

        # 返り値作成
        res = (src_record.to_dict(), dst_record.to_dict())

        # セッション終了
        session.commit()
        session.close()
        return res

    def DeleteFromURL(self, mylist_url: str) -> int:
        """Mylistのレコードを削除する

        Note:
            "delete from Mylist where mylist_url = {}"

        Args:
            mylist_url (str): 削除対象のマイリストURL

        Returns:
            int: 削除成功時0, その他失敗時-1
        """
        # DELETE対象をSELECT
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        record = session.query(Mylist).filter(Mylist.url == mylist_url).first()

        # 存在しない場合はエラー
        if not record:
            session.close()
            return -1

        # DELETEする
        session.delete(record)

        session.commit()
        session.close()
        return 0

    def select(self) -> list[dict]:
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
        res_dict = [r.to_dict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromShowname(self, showname: str) -> list[dict]:
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
        res_dict = [r.to_dict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromURL(self, url: str) -> list[dict]:
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
        res_dict = [r.to_dict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict


if __name__ == "__main__":
    db_fullpath = Path("test.db")
    mylist_db = MylistDBController(db_fullpath=str(db_fullpath))

    if db_fullpath.is_file():
        db_fullpath.unlink()
    pass
