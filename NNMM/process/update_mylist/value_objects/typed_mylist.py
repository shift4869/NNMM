from dataclasses import dataclass

from NNMM.model import Mylist


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


if __name__ == "__main__":
    pass

