# coding: utf-8
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM.DBControllerBase import DBControllerBase
from NNMM.Model import *


DEBUG = False


class MylistInfoDBController(DBControllerBase):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        super().__init__(db_fullpath)

    def Upsert(self, movie_id, title, username, status, uploaded_at, url, created_at):
        """MylistInfoにUPSERTする

        Notes:
            追加しようとしているレコードが既存テーブルに存在しなければINSERT
            存在しているならばUPDATE(DELETE->INSERT)
            一致しているかの判定はurlが一致している場合、とする

        Args:
            movie_id (str): 動画ID(smxxxxxxxx)
            title (str): 動画タイトル
            username (str): 投稿者名
            status (str): 視聴状況({"未視聴", "視聴済"})
            uploaded_at (str): 動画投稿日時
            url (str): 動画URL
            created_at (str): 作成日時

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        res = -1

        r = MylistInfo(movie_id, title, username, status, uploaded_at, url, created_at)

        try:
            q = session.query(MylistInfo).filter(or_(MylistInfo.movie_id == r.movie_id))
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
            一致しているかの判定はurlが一致している場合、とする

        Args:
            以下のArgsをキーとするrecordのlistを引数としてとる
            records = list(dict)
                dictb Keys
                    movie_id (str): 動画ID(smxxxxxxxx)
                    title (str): 動画タイトル
                    username (str): 投稿者名
                    status (str): 視聴状況({"未視聴", "視聴済"})
                    uploaded_at (str): 動画投稿日時
                    url (str): 動画URL
                    created_at (str): 作成日時

        Returns:
            int: 0(成功,新規追加), 1(成功,更新), other(失敗)
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        res = -1

        for record in records:
            movie_id = record.get("movie_id")
            title = record.get("title")
            username = record.get("username")
            status = record.get("status")
            uploaded_at = record.get("uploaded_at")
            url = record.get("url")
            created_at = record.get("created_at")

            r = MylistInfo(movie_id, title, username, status, uploaded_at, url, created_at)

            try:
                q = session.query(MylistInfo).filter(or_(MylistInfo.movie_id == r.movie_id))
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

        # res = session.query(MylistInfo).order_by(asc(MylistInfo.created_at)).limit(limit).all()
        res = session.query(MylistInfo).order_by(asc(MylistInfo.created_at)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromMovieID(self, movie_id):
        """MylistInfoからmovie_idを条件としてSELECTする

        Note:
            "select * from MylistInfo where movie_id = {}".format(movie_id)

        Args:
            movie_id (str): 取得対象の動画ID

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(MylistInfo).filter_by(movie_id=movie_id).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict

    def SelectFromURL(self, url):
        """MylistInfoからurlを条件としてSELECTする

        Note:
            "select * from MylistInfo where url = {}".format(url)

        Args:
            url (str): 取得対象のマイリストurl

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()

        res = session.query(MylistInfo).filter_by(url=url).all()
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

        res = session.query(MylistInfo).filter_by(username=username).order_by(desc(MylistInfo.movie_id)).all()
        res_dict = [r.toDict() for r in res]  # 辞書リストに変換

        session.close()
        return res_dict


if __name__ == "__main__":
    DEBUG = True
    db_fullpath = Path("NNMM_DB.db")
    db_cont = MylistInfoDBController(db_fullpath=str(db_fullpath))

    records = db_cont.Select()
    pass
