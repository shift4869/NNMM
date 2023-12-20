from dataclasses import dataclass
from typing import Self

from NNMM.process.update_mylist.value_objects.mylist_dict import MylistDict


@dataclass(frozen=True)
class TypedMylist():
    id: str
    username: str
    mylistname: str
    type: str
    showname: str
    url: str
    created_at: str
    updated_at: str
    checked_at: str
    check_interval: str
    is_include_new: str

    @classmethod
    def create(cls, mylist_dict: MylistDict) -> Self:
        mylist_dict._dict["id"],
        mylist_dict._dict["username"],
        mylist_dict._dict["mylistname"],
        mylist_dict._dict["type"],
        mylist_dict._dict["showname"],
        mylist_dict._dict["url"],
        mylist_dict._dict["created_at"],
        mylist_dict._dict["updated_at"],
        mylist_dict._dict["checked_at"],
        mylist_dict._dict["check_interval"],
        mylist_dict._dict["is_include_new"]

        pass


if __name__ == "__main__":
    pass

