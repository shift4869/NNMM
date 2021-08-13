# coding: utf-8
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()


class MylistInfo(Base):
    """マイリスト情報モデル

        [id] INTEGER NOT NULL UNIQUE,
        [video_id] TEXT NOT NULL,
        [title] TEXT NOT NULL,
        [username] TEXT NOT NULL,
        [status] TEXT,
        [uploaded_at] TEXT,
        [video_url] TEXT NOT NULL,
        [mylist_url] TEXT NOT NULL,
        [created_at] TEXT,
        PRIMARY KEY([id])
    """

    __tablename__ = "MylistInfo"

    id = Column(Integer, primary_key=True)
    video_id = Column(String(256), nullable=False)
    title = Column(String(256), nullable=False)
    username = Column(String(512), nullable=False)
    status = Column(String(512))
    uploaded_at = Column(String(256))
    video_url = Column(String(512), nullable=False)
    mylist_url = Column(String(512), nullable=False)
    created_at = Column(String(256))

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        self.status = "未視聴"

    def __init__(self, video_id, title, username, status, uploaded_at, video_url, mylist_url, created_at):
        # self.id = id
        self.video_id = video_id
        self.title = title
        self.username = username
        self.status = status
        self.uploaded_at = uploaded_at
        self.video_url = video_url
        self.mylist_url = mylist_url
        self.created_at = created_at

    def __repr__(self):
        return "<MylistInfo(id='{}', video_id='{}')>".format(self.id, self.video_id)

    def __eq__(self, other):
        return isinstance(other, MylistInfo) and other.video_id == self.video_id and other.mylist_url == self.mylist_url

    def toDict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "title": self.title,
            "username": self.username,
            "status": self.status,
            "uploaded_at": self.uploaded_at,
            "video_url": self.video_url,
            "mylist_url": self.mylist_url,
            "created_at": self.created_at,
        }


class Mylist(Base):
    """マイリストモデル

        [id] INTEGER NOT NULL UNIQUE,
        [username] TEXT NOT NULL,
        [type] TEXT,
        [showname] TEXT NOT NULL UNIQUE,
        [url] TEXT NOT NULL UNIQUE,
        [created_at] TEXT,
        [updated_at] TEXT,
        [is_include_new] BOOLEAN DEFAULT 'True',
        PRIMARY KEY([id])
    """

    __tablename__ = "Mylist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(256), nullable=False)
    mylistname = Column(String(256), nullable=False)
    type = Column(String(256))
    showname = Column(String(256), nullable=False, unique=True)
    url = Column(String(512), nullable=False, unique=True)
    created_at = Column(String(256))
    updated_at = Column(String(256))
    updated_interval = Column(String(256))
    is_include_new = Column(Boolean, server_default=text("True"))

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)

    def __init__(self, id, username, mylistname, type, showname, url, created_at, updated_at, updated_interval, is_include_new):
        self.id = id
        self.username = username
        self.mylistname = mylistname
        self.type = type
        self.showname = showname
        self.url = url
        self.created_at = created_at
        self.updated_at = updated_at
        self.updated_interval = updated_interval
        self.is_include_new = is_include_new

    def __repr__(self):
        return "<Mylist(id='{}', username='{}')>".format(self.id, self.username)

    def __eq__(self, other):
        return isinstance(other, Mylist) and other.url == self.url

    def toDict(self):
        return {
            "id": self.id,
            "username": self.username,
            "mylistname": self.mylistname,
            "type": self.type,
            "showname": self.showname,
            "url": self.url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "updated_interval": self.updated_interval,
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
