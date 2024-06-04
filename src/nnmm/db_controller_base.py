from abc import ABCMeta, abstractmethod
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from nnmm.model import Base


class DBControllerBase(metaclass=ABCMeta):
    def __init__(self, db_fullpath="NNMM_DB.db"):
        self.dbname = db_fullpath
        self.db_url = f"sqlite:///{self.dbname}"

        self.engine = create_engine(
            self.db_url,
            echo=False,
            poolclass=StaticPool,
            connect_args={
                "timeout": 30,
                "check_same_thread": False,
            },
        )
        Base.metadata.create_all(self.engine)

    @abstractmethod
    def select(self) -> list[dict]:
        """MylistからSELECTする

        Note:
            "select * from Mylist order by created_at desc"

        Returns:
            dict[]: SELECTしたレコードの辞書リスト
        """
        raise NotImplementedError


if __name__ == "__main__":
    import nnmm.mylist_info_db_controller

    db_fullpath = Path(":memory:")
    db_cont = nnmm.mylist_info_db_controller(db_fullpath=str(db_fullpath))
    pass
