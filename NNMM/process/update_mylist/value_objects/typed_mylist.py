from dataclasses import dataclass
from typing import Self

from NNMM.process.update_mylist.value_objects.check_interval import CheckInterval
from NNMM.process.update_mylist.value_objects.checked_at import CheckedAt
from NNMM.process.update_mylist.value_objects.created_at import CreatedAt
from NNMM.process.update_mylist.value_objects.mylist_row_index import MylistRowIndex
from NNMM.process.update_mylist.value_objects.updated_at import UpdatedAt
from NNMM.util import IncludeNewStatus, MylistType
from NNMM.video_info_fetcher.value_objects.mylist_url import MylistURL
from NNMM.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory
from NNMM.video_info_fetcher.value_objects.myshowname import Myshowname
from NNMM.video_info_fetcher.value_objects.showname import Showname
from NNMM.video_info_fetcher.value_objects.username import Username


@dataclass(frozen=True)
class TypedMylist:
    id: MylistRowIndex
    username: Username
    mylistname: Myshowname
    type: MylistType
    showname: Showname
    url: MylistURL
    created_at: CreatedAt
    updated_at: UpdatedAt
    checked_at: CheckedAt
    check_interval: CheckInterval
    is_include_new: IncludeNewStatus

    def __post_init__(self) -> None:
        if not isinstance(self.id, MylistRowIndex):
            raise ValueError("id must be MylistRowIndex.")
        if not isinstance(self.username, Username):
            raise ValueError("username must be Username.")
        if not isinstance(self.mylistname, Myshowname):
            raise ValueError("mylistname must be Myshowname.")
        if not isinstance(self.type, MylistType):
            raise ValueError("type must be MylistType.")
        if not isinstance(self.showname, Showname):
            raise ValueError("showname must be Showname.")
        if not isinstance(self.url, MylistURL):
            raise ValueError("url must be MylistURL.")
        if not isinstance(self.created_at, CreatedAt):
            raise ValueError("created_at must be CreatedAt.")
        if not isinstance(self.updated_at, UpdatedAt):
            raise ValueError("updated_at must be UpdatedAt.")
        if not isinstance(self.checked_at, CheckedAt):
            raise ValueError("checked_at must be CheckedAt.")
        if not isinstance(self.check_interval, CheckInterval):
            raise ValueError("check_interval must be CheckInterval.")
        if not isinstance(self.is_include_new, IncludeNewStatus):
            raise ValueError("is_include_new must be IncludeNewStatus.")

    @classmethod
    def create(cls, mylist_dict: dict) -> Self:
        row_id = MylistRowIndex(int(mylist_dict["id"]))
        username = Username(mylist_dict["username"])
        mylistname = Myshowname(mylist_dict["mylistname"])
        mylist_type = MylistType(mylist_dict["type"])
        showname = Showname(mylist_dict["showname"])
        created_at = CreatedAt(mylist_dict["created_at"])
        updated_at = UpdatedAt(mylist_dict["updated_at"])
        checked_at = CheckedAt(mylist_dict["checked_at"])
        check_interval = CheckInterval.create(mylist_dict["check_interval"])
        is_include_new = IncludeNewStatus(mylist_dict["is_include_new"])

        mylist_url = MylistURLFactory.create(mylist_dict["url"])

        return TypedMylist(
            row_id,
            username,
            mylistname,
            mylist_type,
            showname,
            mylist_url,
            created_at,
            updated_at,
            checked_at,
            check_interval,
            is_include_new,
        )


if __name__ == "__main__":
    mylist_dict = {
        "id": 1,
        "username": "username_1",
        "mylistname": "投稿動画",
        "type": "uploaded",
        "showname": "投稿者1さんの投稿動画",
        "url": "https://www.nicovideo.jp/user/10000001/video",
        "created_at": "2023-12-22 12:34:56",
        "updated_at": "2023-12-22 12:34:56",
        "checked_at": "2023-12-22 12:34:56",
        "check_interval": "15分",
        "is_include_new": True,
    }
    typed_mylist = TypedMylist.create(mylist_dict)
    print(typed_mylist)
