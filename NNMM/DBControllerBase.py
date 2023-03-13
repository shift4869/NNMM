# coding: utf-8
import pickle
import re
from abc import ABCMeta, abstractmethod
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.orm.exc import *

from NNMM.Model import *

DEBUG = False


class DBControllerBase(metaclass=ABCMeta):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        self.dbname = db_fullpath
        self.engine = create_engine(f"sqlite:///{self.dbname}", echo=False, pool_recycle=5, connect_args={"timeout": 30})
        Base.metadata.create_all(self.engine)

    @abstractmethod
    def Select(self):
        """FavoriteからSELECTする

        Note:
            "select * from Favorite order by created_at desc"

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        return []


if __name__ == "__main__":
    import NNMM.MylistInfoDBController
    DEBUG = True
    db_fullpath = Path("NNMM_DB.db")
    db_cont = NNMM.MylistInfoDBController(db_fullpath=str(db_fullpath))
    pass
