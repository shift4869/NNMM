# coding: utf-8
from dataclasses import dataclass
from pprint import pprint
from typing import ClassVar

from NNMM.VideoInfoFetcher.ValueObjects.RegisteredAt import RegisteredAt
from NNMM.VideoInfoFetcher.ValueObjects.Title import Title
from NNMM.VideoInfoFetcher.ValueObjects.Videoid import Videoid
from NNMM.VideoInfoFetcher.ValueObjects.VideoURL import VideoURL


@dataclass(frozen=True)
class ItemInfo():
    """rssから取得される動画情報の1エントリをまとめたデータクラス

    Notes:
        RSSParser参照

    Raises:
        TypeError: 初期化時の引数の型が不正な場合

    Returns:
        ItemInfo: rssから取得される動画情報の1エントリ分の情報をまとめたもの
    """
    video_id: ClassVar[Videoid]  # 動画ID sm12345678
    title: Title                 # 動画タイトル テスト動画
    registered_at: RegisteredAt  # 登録日時 %Y-%m-%d %H:%M:%S
    video_url: VideoURL          # 動画URL https://www.nicovideo.jp/watch/sm12345678

    def __post_init__(self) -> None:
        """初期化後処理

        Notes:
            バリデーションとvideo_id の設定を行う
        """
        self._is_valid()
        object.__setattr__(self, "video_id", self.video_url.video_id)

    def _is_valid(self) -> bool:
        """バリデーション

        Notes:
            それぞれの要素のデータクラスにて正当性は担保されているので
            ItemInfo では特にチェックしない
        """
        return True

    def to_dict(self) -> dict:
        """データクラスの項目を辞書として取得する

        Notes:
            値は各ValueObject が設定される

        Returns:
            dict: {データクラスの項目: 対応するValueObject}
        """
        return self.__dict__

    @property
    def result(self) -> dict:
        """データクラスの項目をまとめた辞書を返す

        Notes:
            to_dict()参照

        Returns:
            dict: {データクラスの項目: 対応するValueObject}
        """
        return self.to_dict()


if __name__ == "__main__":
    title = Title("テスト動画")
    registered_at = RegisteredAt("2022-05-06 00:01:01")
    video_url = VideoURL.create("https://www.nicovideo.jp/watch/sm12345678")

    fvi = ItemInfo(title, registered_at, video_url)
    pprint(fvi.to_dict())
