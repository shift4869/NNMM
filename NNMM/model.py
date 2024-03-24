from sqlalchemy import Boolean, Column, Integer, String, create_engine, text
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()


class MylistInfo(Base):
    """マイリスト情報モデル

    [id] INTEGER NOT NULL UNIQUE,
    [video_id] TEXT NOT NULL,
    [title] TEXT NOT NULL,
    [username] TEXT NOT NULL,
    [status] TEXT,
    [uploaded_at] TEXT,
    [registered_at] TEXT,
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
    registered_at = Column(String(256))
    video_url = Column(String(512), nullable=False)
    mylist_url = Column(String(512), nullable=False)
    created_at = Column(String(256))

    def __init__(
        self, video_id, title, username, status, uploaded_at, registered_at, video_url, mylist_url, created_at
    ):
        # self.id = id
        self.video_id = video_id
        self.title = title
        self.username = username
        self.status = status
        self.uploaded_at = uploaded_at
        self.registered_at = registered_at
        self.video_url = video_url
        self.mylist_url = mylist_url
        self.created_at = created_at

    def __repr__(self):
        return "<MylistInfo(id='{}', video_id='{}')>".format(self.id, self.video_id)

    def __eq__(self, other):
        return (
            isinstance(other, MylistInfo) and other.video_id == self.video_id and other.mylist_url == self.mylist_url
        )

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "title": self.title,
            "username": self.username,
            "status": self.status,
            "uploaded_at": self.uploaded_at,
            "registered_at": self.registered_at,
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
    checked_at = Column(String(256))
    check_interval = Column(String(256))
    check_failed_count = Column(Integer)
    is_include_new = Column(Boolean, server_default=text("True"))

    def __init__(
        self,
        id,
        username,
        mylistname,
        type,
        showname,
        url,
        created_at,
        updated_at,
        checked_at,
        check_interval,
        check_failed_count,
        is_include_new,
    ):
        self.id = id
        self.username = username
        self.mylistname = mylistname
        self.type = type
        self.showname = showname
        self.url = url
        self.created_at = created_at
        self.updated_at = updated_at
        self.checked_at = checked_at
        self.check_interval = check_interval
        self.check_failed_count = check_failed_count
        self.is_include_new = is_include_new

    def __repr__(self):
        return "<Mylist(id='{}', username='{}')>".format(self.id, self.username)

    def __eq__(self, other):
        return isinstance(other, Mylist) and other.url == self.url

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "mylistname": self.mylistname,
            "type": self.type,
            "showname": self.showname,
            "url": self.url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "checked_at": self.checked_at,
            "check_interval": self.check_interval,
            "check_failed_count": self.check_failed_count,
            "is_include_new": self.is_include_new,
        }


if __name__ == "__main__":
    engine = create_engine("sqlite:///test_NNMM_DB.db", echo=True)
    Base.metadata.create_all(engine)

    session = Session(engine)
    session.query(Mylist).delete()

    mylist_data_list = [
        (
            "shift4869",
            "投稿動画",
            "uploaded",
            "shift4869さんの投稿動画",
            "https://www.nicovideo.jp/user/6063658/video",
            "2022-05-01 12:33:21",
            "2022-05-01 12:33:21",
            "2022-05-01 12:33:21",
            "15分",
            0,
            False,
        ),
        (
            "しも",
            "テスト用マイリスト",
            "mylist",
            "「テスト用マイリスト」-shift4869さんのマイリスト",
            "https://www.nicovideo.jp/user/6063658/mylist/72036443",
            "2022-05-01 13:48:17",
            "2022-05-01 13:48:17",
            "2022-07-05 17:17:17",
            "15分",
            0,
            True,
        ),
        (
            "しも",
            "テスト用マイリスト1",
            "mylist",
            "「テスト用マイリスト1」-vita_shiftさんのマイリスト",
            "https://www.nicovideo.jp/user/31784111/mylist/73116396",
            "2022-05-01 22:49:57",
            "2022-05-01 22:49:57",
            "2022-08-06 22:35:46",
            "15分",
            0,
            False,
        ),
        (
            "しも",
            "テスト用マイリスト2",
            "mylist",
            "「テスト用マイリスト2」-vita_shiftさんのマイリスト",
            "https://www.nicovideo.jp/user/31784111/mylist/73116402",
            "2022-05-01 22:49:38",
            "2022-05-01 22:49:38",
            "2022-07-05 17:17:18",
            "15分",
            0,
            False,
        ),
        (
            "しも",
            "テスト用マイリスト3",
            "mylist",
            "「テスト用マイリスト3」-vita_shiftさんのマイリスト",
            "https://www.nicovideo.jp/user/31784111/mylist/73116403",
            "2022-05-14 21:06:47",
            "2022-05-14 21:06:47",
            "2022-07-05 17:17:18",
            "15分",
            0,
            False,
        ),
    ]

    for i, data in enumerate(mylist_data_list):
        mylist_record = Mylist(
            id=i,
            username=data[0],
            mylistname=data[1],
            type=data[2],
            showname=data[3],
            url=data[4],
            created_at=data[5],
            updated_at=data[6],
            checked_at=data[7],
            check_interval=data[8],
            check_failed_count=data[9],
            is_include_new=data[10],
        )
        session.add(mylist_record)
    session.commit()

    result = session.query(Mylist).all()[:10]
    for f in result:
        print(f)

    session.query(MylistInfo).delete()
    video_data_list = [
        (
            "sm2959233",
            "ニコニコ動画流星群",
            "しも",
            "未視聴",
            "2008-04-11 05:05:52",
            "2022-05-01 13:10:40",
            "https://www.nicovideo.jp/watch/sm2959233",
            "https://www.nicovideo.jp/user/6063658/mylist/72036443",
            "2022-07-05 17:17:17",
        ),
        (
            "sm500873",
            "組曲『ニコニコ動画』 ",
            "しも",
            "未視聴",
            "2007-06-23 18:27:06",
            "2022-03-01 02:05:39",
            "https://www.nicovideo.jp/watch/sm500873",
            "https://www.nicovideo.jp/user/6063658/mylist/72036443",
            "2022-07-05 17:17:17",
        ),
        (
            "sm9",
            "新・豪血寺一族 -煩悩解放 - レッツゴー！陰陽師",
            "中の",
            "未視聴",
            "2007-03-06 00:33:00",
            "2022-02-27 18:04:39",
            "https://www.nicovideo.jp/watch/sm9",
            "https://www.nicovideo.jp/user/6063658/mylist/72036443",
            "2022-07-05 17:17:17",
        ),
        (
            "sm7233711",
            "七色のニコニコ動画",
            "しも",
            "",
            "2009-06-03 07:05:06",
            "2022-05-01 22:46:26",
            "https://www.nicovideo.jp/watch/sm7233711",
            "https://www.nicovideo.jp/user/31784111/mylist/73116402",
            "2022-07-05 17:17:17",
        ),
        (
            "sm500873",
            "組曲『ニコニコ動画』 ",
            "しも",
            "",
            "2007-06-23 18:27:06",
            "2022-05-01 22:45:39",
            "https://www.nicovideo.jp/watch/sm500873",
            "https://www.nicovideo.jp/user/31784111/mylist/73116402",
            "2022-07-05 17:17:17",
        ),
        (
            "sm9",
            "新・豪血寺一族 -煩悩解放 - レッツゴー！陰陽師",
            "中の",
            "",
            "2007-03-06 00:33:00",
            "2022-05-01 22:45:08",
            "https://www.nicovideo.jp/watch/sm9",
            "https://www.nicovideo.jp/user/31784111/mylist/73116402",
            "2022-07-05 17:17:17",
        ),
        (
            "sm2959233",
            "ニコニコ動画流星群",
            "しも",
            "",
            "2008-04-11 05:05:52",
            "2022-05-01 22:45:50",
            "https://www.nicovideo.jp/watch/sm2959233",
            "https://www.nicovideo.jp/user/31784111/mylist/73116396",
            "2022-08-06 22:35:45",
        ),
        (
            "sm500873",
            "組曲『ニコニコ動画』 ",
            "しも",
            "",
            "2007-06-23 18:27:06",
            "2022-05-01 22:45:34",
            "https://www.nicovideo.jp/watch/sm500873",
            "https://www.nicovideo.jp/user/31784111/mylist/73116396",
            "2022-08-06 22:35:45",
        ),
        (
            "sm9",
            "新・豪血寺一族 -煩悩解放 - レッツゴー！陰陽師",
            "中の",
            "",
            "2007-03-06 00:33:00",
            "2022-05-01 22:45:03",
            "https://www.nicovideo.jp/watch/sm9",
            "https://www.nicovideo.jp/user/31784111/mylist/73116396",
            "2022-08-06 22:35:45",
        ),
        (
            "sm7233711",
            "七色のニコニコ動画",
            "しも",
            "",
            "2009-06-03 07:05:06",
            "2022-05-01 22:46:30",
            "https://www.nicovideo.jp/watch/sm7233711",
            "https://www.nicovideo.jp/user/31784111/mylist/73116403",
            "2022-07-05 17:17:17",
        ),
        (
            "sm2959233",
            "ニコニコ動画流星群",
            "しも",
            "",
            "2008-04-11 05:05:52",
            "2022-05-01 22:45:56",
            "https://www.nicovideo.jp/watch/sm2959233",
            "https://www.nicovideo.jp/user/31784111/mylist/73116403",
            "2022-07-05 17:17:17",
        ),
        (
            "sm9",
            "新・豪血寺一族 -煩悩解放 - レッツゴー！陰陽師",
            "中の",
            "",
            "2007-03-06 00:33:00",
            "2022-05-01 22:45:14",
            "https://www.nicovideo.jp/watch/sm9",
            "https://www.nicovideo.jp/user/31784111/mylist/73116403",
            "2022-07-05 17:17:17",
        ),
    ]

    for i, data in enumerate(video_data_list):
        video_record = MylistInfo(
            video_id=data[0],
            title=data[1],
            username=data[2],
            status=data[3],
            uploaded_at=data[4],
            registered_at=data[5],
            video_url=data[6],
            mylist_url=data[7],
            created_at=data[8],
        )
        session.add(video_record)
    session.commit()

    result = session.query(MylistInfo).all()[:10]
    for f in result:
        print(f)

    session.close()
