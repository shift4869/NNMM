from dataclasses import dataclass
from typing import Any, Self

from NNMM.model import MylistInfo
from NNMM.process.update_mylist.value_objects.typed_video import TypedVideo


@dataclass(frozen=True)
class VideoDict():
    _dict: dict

    def __post_init__(self) -> None:
        if not isinstance(self._dict, dict):
            raise ValueError("_dict must be dict.")
        self.is_valid()

    def is_valid(self) -> bool:
        valid_key = MylistInfo.__table__.c.keys()
        instance_key = list(self._dict.keys())
        if instance_key != valid_key:
            raise ValueError("_dict.keys() is invalid key.")
        return True

    def __getitem__(self, item) -> Any:
        return self._dict.__getitem__(item)

    def __setitem__(self, key, value) -> None:
        return self._dict.__setitem__(key, value)

    @property
    def video(self) -> MylistInfo:
        return MylistInfo(
            self._dict["id"],
            self._dict["video_id"],
            self._dict["title"],
            self._dict["username"],
            self._dict["status"],
            self._dict["uploaded_at"],
            self._dict["registered_at"],
            self._dict["video_url"],
            self._dict["mylist_url"],
            self._dict["created_at"],
        )

    def to_typed_video(self) -> TypedVideo:
        return TypedVideo(
            self._dict["id"],
            self._dict["video_id"],
            self._dict["title"],
            self._dict["username"],
            self._dict["status"],
            self._dict["uploaded_at"],
            self._dict["registered_at"],
            self._dict["video_url"],
            self._dict["mylist_url"],
            self._dict["created_at"],
        )

    @classmethod
    def create(cls, video_dict: dict) -> Self:
        return cls(video_dict)


if __name__ == "__main__":
    pass
