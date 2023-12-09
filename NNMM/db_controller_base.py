import pickle
import re
from abc import ABCMeta, abstractmethod
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from NNMM.model import Base

DEBUG = False


class DBControllerBase(metaclass=ABCMeta):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        self.dbname = db_fullpath
        self.db_url = f"sqlite:///{self.dbname}"

        self.engine = create_engine(
            self.db_url,
            echo=False,
            poolclass=StaticPool,
            # pool_recycle=5,
            connect_args={
                "timeout": 30,
                "check_same_thread": False,
            }
        )
        Base.metadata.create_all(self.engine)

    @abstractmethod
    def select(self):
        """FavoriteからSELECTする

        Note:
            "select * from Favorite order by created_at desc"

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        return []


if __name__ == "__main__":
    import NNMM.mylist_info_db_controller
    DEBUG = True
    db_fullpath = Path("NNMM_DB.db")
    db_cont = NNMM.mylist_info_db_controller(db_fullpath=str(db_fullpath))
    pass
