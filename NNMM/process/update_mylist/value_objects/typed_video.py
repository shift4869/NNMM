from dataclasses import dataclass

from NNMM.model import MylistInfo


@dataclass(frozen=False)
class TypedVideo():
    id: str
    video_id: str
    title: str
    username: str
    status: str
    uploaded_at: str
    registered_at: str
    video_url: str
    mylist_url: str
    created_at: str


if __name__ == "__main__":
    pass

