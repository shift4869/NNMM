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
        """受け取った dict が MylistInfo の属性をキーとして含むかを調べる

        Raises:
            ValueError: dict のキーが MylistInfo の属性と一致しなかった場合

        Returns:
            bool: dict のキーと MylistInfo の属性が一致した場合True
        """
        valid_key = MylistInfo.__table__.c.keys()
        instance_key = list(self._dict.keys())
        if instance_key != valid_key:
            raise ValueError("_dict.keys() is invalid key.")
        return True

    def __getitem__(self, item) -> Any:
        return self._dict.__getitem__(item)

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
        """MylistInfo を表す dict のクラスを作成する

        Args:
            video_dict (dict): MylistInfo を表す dict のリスト

        Returns:
            Self: VideoDict インスタンス
        """
        return cls(video_dict)


if __name__ == "__main__":
    pass
