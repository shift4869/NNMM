# coding: utf-8
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

    def Upsert(self, username, type, listname, url, created_at, is_include_new):
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
            is_include_new (boolean): 未視聴動画を含むかどうか

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        res = -1

        r = Mylist(username, type, listname, url, created_at, is_include_new)

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

    def Select(self):
        """MylistからSELECTする

        Note:
            "select * from Mylist order by created_at asc"

        Args:
            limit (int): 取得レコード数上限

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        # res = session.query(Mylist).order_by(asc(Mylist.created_at)).limit(limit).all()
        res = session.query(Mylist).order_by(asc(Mylist.created_at)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
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
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(Mylist).filter_by(listname=listname).all()
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
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(Mylist).filter_by(url=url).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict


if __name__ == "__main__":
    DEBUG = True
    db_fullpath = Path("NNMM_DB.db")
    db_cont = MylistDBController(db_fullpath=str(db_fullpath))

    td_format = "%Y/%m/%d %H:%M"
    dts_format = "%Y-%m-%d %H:%M:%S"
    dst = datetime.now().strftime(dts_format)
    url = "https://www.nicovideo.jp/user/12899156/video"
    db_cont.Upsert("willow8713", "uploaded", "willow8713さんの投稿動画", url, dst)

    url = "https://www.nicovideo.jp/user/1594318/video"
    db_cont.Upsert("moco78", "uploaded", "moco78さんの投稿動画", url, dst)

    records = db_cont.Select()
    pass
