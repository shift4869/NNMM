from nnmm.video_info_fetcher.value_objects.mylist_url import MylistURL
from nnmm.video_info_fetcher.value_objects.series_url import SeriesURL
from nnmm.video_info_fetcher.value_objects.uploaded_url import UploadedURL
from nnmm.video_info_fetcher.value_objects.url import URL
from nnmm.video_info_fetcher.value_objects.user_mylist_url import UserMylistURL


class MylistURLFactory:
    _class_list: list[MylistURL] = [UploadedURL, UserMylistURL, SeriesURL]

    def __init__(self) -> None:
        class_name = self.__class__.__name__
        raise ValueError(f"{class_name} cannot make instance, use classmethod {class_name}.create().")

    @classmethod
    def create(cls, url: str | URL) -> MylistURL:
        if isinstance(url, URL):
            url = url.original_url
        for c in cls._class_list:
            if not hasattr(c, "is_valid_mylist_url"):
                continue
            if c.is_valid_mylist_url(url):
                return c.create(url)
        raise ValueError(f"{url} is not MylistURL.")


if __name__ == "__main__":
    urls = [
        "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        "https://www.nicovideo.jp/user/37896001/video?ref=pc_mypage_nicorepo",  # 投稿動画(クエリつき)
        "https://不正なURLアドレス/user/6063658/mylist/72036443",  # 不正なURLアドレス
    ]

    for url in urls:
        try:
            u = MylistURLFactory.create(url)
            print(u)
        except Exception:
            print("Not Target URL : " + url)
