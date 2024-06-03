from dataclasses import dataclass
from typing import Any, Self

from nnmm.process.update_mylist.value_objects.created_at import CreatedAt
from nnmm.process.update_mylist.value_objects.video_row_index import VideoRowIndex
from nnmm.process.value_objects.table_row import Status
from nnmm.video_info_fetcher.value_objects.mylist_url import MylistURL
from nnmm.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory
from nnmm.video_info_fetcher.value_objects.registered_at import RegisteredAt
from nnmm.video_info_fetcher.value_objects.title import Title
from nnmm.video_info_fetcher.value_objects.uploaded_at import UploadedAt
from nnmm.video_info_fetcher.value_objects.username import Username
from nnmm.video_info_fetcher.value_objects.video_url import VideoURL
from nnmm.video_info_fetcher.value_objects.videoid import Videoid


@dataclass(frozen=True)
class TypedVideo:
    id: VideoRowIndex
    video_id: Videoid
    title: Title
    username: Username
    status: Status
    uploaded_at: UploadedAt
    registered_at: RegisteredAt
    video_url: VideoURL
    mylist_url: MylistURL
    created_at: CreatedAt

    def __post_init__(self) -> None:
        if not isinstance(self.id, VideoRowIndex):
            raise ValueError("id must be VideoRowIndex.")
        if not isinstance(self.video_id, Videoid):
            raise ValueError("video_id must be Videoid.")
        if not isinstance(self.title, Title):
            raise ValueError("title must be Title.")
        if not isinstance(self.username, Username):
            raise ValueError("username must be Username.")
        if not isinstance(self.status, Status):
            raise ValueError("status must be Status.")
        if not isinstance(self.uploaded_at, UploadedAt):
            raise ValueError("uploaded_at must be UploadedAt.")
        if not isinstance(self.registered_at, RegisteredAt):
            raise ValueError("registered_at must be RegisteredAt.")
        if not isinstance(self.video_url, VideoURL):
            raise ValueError("video_url must be VideoURL.")
        if not isinstance(self.mylist_url, MylistURL):
            raise ValueError("mylist_url must be MylistURL.")
        if not isinstance(self.created_at, CreatedAt):
            raise ValueError("created_at must be CreatedAt.")

    def replace_from_typed_value(self, **kargs: dict[str, Any]) -> Self:
        def type_check(key, value, class_):
            if not isinstance(value, class_):
                raise ValueError(f"{key} must be {class_.__name__}.")

        for key, value in kargs.items():
            match key:
                case "id":
                    type_check(key, value, VideoRowIndex)
                    kargs[key] = str(int(value))
                case "video_id":
                    type_check(key, value, Videoid)
                    kargs[key] = str(value.id)
                case "title":
                    type_check(key, value, Title)
                    kargs[key] = str(value.name)
                case "username":
                    type_check(key, value, Username)
                    kargs[key] = str(value.name)
                case "status":
                    type_check(key, value, Status)
                    kargs[key] = str(value.value)
                case "uploaded_at":
                    type_check(key, value, UploadedAt)
                    kargs[key] = str(value.dt_str)
                case "registered_at":
                    type_check(key, value, RegisteredAt)
                    kargs[key] = str(value.dt_str)
                case "video_url":
                    type_check(key, value, VideoURL)
                    kargs[key] = str(value.non_query_url)
                case "mylist_url":
                    type_check(key, value, MylistURL)
                    kargs[key] = str(value.non_query_url)
                case "created_at":
                    type_check(key, value, CreatedAt)
                    kargs[key] = str(value.dt_str)
                case invalid_key:
                    raise ValueError(f"'{invalid_key}' is not TableRow's attribute.")
        return self.replace_from_str(**kargs)

    def replace_from_str(self, **kargs: dict[str, str]) -> Self:
        current_row_dict: dict[str, str] = self.to_dict()
        new_row_dict: dict[str, str] = current_row_dict | kargs
        return self.create(new_row_dict)

    def to_dict(self) -> dict[str, str]:
        return {
            "id": str(self.id.index),
            "video_id": self.video_id.id,
            "title": self.title.name,
            "username": self.username.name,
            "status": self.status.value,
            "uploaded_at": self.uploaded_at.dt_str,
            "registered_at": self.registered_at.dt_str,
            "video_url": self.video_url.non_query_url,
            "mylist_url": self.mylist_url.non_query_url,
            "created_at": self.created_at.dt_str,
        }

    @classmethod
    def create(cls, video_dict: dict[str, str]) -> Self:
        row_id = VideoRowIndex(int(video_dict["id"]))
        video_id = Videoid(video_dict["video_id"])
        title = Title(video_dict["title"])
        username = Username(video_dict["username"])
        status = Status(video_dict["status"])
        uploaded_at = UploadedAt(video_dict["uploaded_at"])
        registered_at = RegisteredAt(video_dict["registered_at"])
        video_url = VideoURL.create(video_dict["video_url"])
        created_at = CreatedAt(video_dict["created_at"])

        mylist_url = MylistURLFactory.create(video_dict["mylist_url"])

        return TypedVideo(
            row_id,
            video_id,
            title,
            username,
            status,
            uploaded_at,
            registered_at,
            video_url,
            mylist_url,
            created_at,
        )


if __name__ == "__main__":
    typed_video = TypedVideo.create({
        "id": 1,
        "video_id": "sm12345671",
        "title": "title_1",
        "username": "username_1",
        "status": "未視聴",
        "uploaded_at": "2023-12-22 12:34:51",
        "registered_at": "2023-12-22 12:34:51",
        "video_url": "https://www.nicovideo.jp/watch/sm12345671",
        "mylist_url": "https://www.nicovideo.jp/user/10000001/video",
        "created_at": "2023-12-22 12:34:51",
    })
    print(typed_video)
