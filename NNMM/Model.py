# coding: utf-8
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()


class MylistInfo(Base):
    """マイリスト情報モデル

        [id] INTEGER NOT NULL UNIQUE,
        [movie_id] TEXT NOT NULL UNIQUE,
        [title] TEXT NOT NULL,
        [username] TEXT NOT NULL,
        [status] TEXT,
        [uploaded_at] TEXT,
        [url] TEXT NOT NULL,
        [created_at] TEXT,
        PRIMARY KEY([id])
    """

    __tablename__ = "MylistInfo"

    id = Column(Integer, primary_key=True, autoincrement=True)
    movie_id = Column(String(256), nullable=False, unique=True)
    title = Column(String(256), nullable=False)
    username = Column(String(512), nullable=False)
    status = Column(String(512))
    uploaded_at = Column(String(256))
    url = Column(String(512), nullable=False)
    created_at = Column(String(256))

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        self.status = "未視聴"

    def __init__(self, movie_id, title, username, status, uploaded_at, url, created_at):
        # self.id = id
        self.movie_id = movie_id
        self.title = title
        self.username = username
        self.status = status
        self.uploaded_at = uploaded_at
        self.url = url
        self.created_at = created_at

    def __repr__(self):
        return "<MylistInfo(id='{}', movie_id='{}')>".format(self.id, self.movie_id)

    def __eq__(self, other):
        return isinstance(other, MylistInfo) and other.movie_id == self.movie_id

    def toDict(self):
        return {
            "id": self.id,
            "movie_id": self.movie_id,
            "title": self.title,
            "username": self.username,
            "status": self.status,
            "uploaded_at": self.uploaded_at,
            "url": self.url,
            "created_at": self.created_at,
        }


class Mylist(Base):
    """マイリストモデル

        [id] INTEGER NOT NULL UNIQUE,
        [username] TEXT NOT NULL,
        [type] TEXT,
        [listname] TEXT NOT NULL UNIQUE,
        [url] TEXT NOT NULL UNIQUE,
        [created_at] TEXT,
        [is_include_new] BOOLEAN DEFAULT 'True',
        PRIMARY KEY([id])
    """

    __tablename__ = "Mylist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(256), nullable=False)
    type = Column(String(256))
    listname = Column(String(256), nullable=False, unique=True)
    url = Column(String(512), nullable=False, unique=True)
    created_at = Column(String(256))
    is_include_new = Column(Boolean, server_default=text("True"))

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)

    def __init__(self, username, type, listname, url, created_at, is_include_new):
        # self.id = id
        self.username = username
        self.type = type
        self.listname = listname
        self.url = url
        self.created_at = created_at
        self.is_include_new = is_include_new

    def __repr__(self):
        return "<Mylist(id='{}', username='{}')>".format(self.id, self.username)

    def __eq__(self, other):
        return isinstance(other, Mylist) and other.url == self.url

    def toDict(self):
        return {
            "id": self.id,
            "username": self.username,
            "type": self.type,
            "listname": self.listname,
            "url": self.url,
            "created_at": self.created_at,
            "is_include_new": self.is_include_new,
        }


if __name__ == "__main__":
    engine = create_engine("sqlite:///NNMM_DB.db", echo=True)
    Base.metadata.create_all(engine)

    session = Session(engine)

    result = session.query(Mylist).all()[:10]
    for f in result:
        print(f)

    session.close()
