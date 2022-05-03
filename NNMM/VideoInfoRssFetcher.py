# coding: utf-8
import asyncio
import logging.config
import pprint
import re
import traceback
import urllib.parse
from datetime import datetime
from logging import INFO, getLogger
from pathlib import Path
from urllib.error import HTTPError

from bs4 import BeautifulSoup

from NNMM import ConfigMain, GuiFunction, VideoInfoFetcherBase


logger = getLogger("root")
logger.setLevel(INFO)


class VideoInfoRssFetcher(VideoInfoFetcherBase.VideoInfoFetcherBase):

    def __init__(self, url: str):
        super().__init__(url, "rss")

        self.RSS_URL_SUFFIX = "?rss=2.0"

    def _get_iteminfo(self, item_lx) -> tuple[str, str, str, str]:
        """一つのentryから動画ID, 動画タイトル, 投稿日時, 動画URLを抽出する

        Notes:
            投稿日時は "%Y-%m-%d %H:%M:%S" のフォーマットで返す
            抽出結果のチェックはしない

        Args:
            item_lx (bs4.element.Tag): soup.find_allで取得されたitemタグ

        Returns:
            tuple[str, str, str, str]: 動画ID, 動画タイトル, 登録日時, 動画URL

        Raises:
            AttributeError, TypeError: エントリパース失敗時
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """
        # src_df: RSSに記載されている日付形式
        # dst_df: NNMMで扱う日付形式
        src_df = "%a, %d %b %Y %H:%M:%S %z"
        dst_df = "%Y-%m-%d %H:%M:%S"

        title = item_lx.find("title").text

        link_lx = item_lx.find("link")
        video_url = link_lx.text
        pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+"
        if re.findall(pattern, video_url):
            # クエリ除去してURL部分のみ保持
            video_url = urllib.parse.urlunparse(
                urllib.parse.urlparse(video_url)._replace(query=None)
            )

        pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
        video_id = re.findall(pattern, video_url)[0]

        pubDate_lx = item_lx.find("pubDate")
        registered_at = datetime.strptime(pubDate_lx.text, src_df).strftime(dst_df)

        return (video_id, title, registered_at, video_url)

    async def _analysis_uploaded_page(self, soup: BeautifulSoup) -> dict:
        """投稿動画ページのRSSを解析する

        Args:
            soup (BeautifulSoup): 解析対象のxml

        Returns:
            dict: 解析結果をまとめた辞書
                {
                    "userid": userid,                           # ユーザーID 1234567
                    "mylistid": mylistid,                       # マイリストID 12345678
                    "showname": showname,                       # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
                    "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
                    "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
                    "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                    "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
                    "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                }

        Raises:
            IndexError, TypeError, ValueError: html解析失敗時
        """
        # 投稿者IDとマイリストID取得
        pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/video"
        userid = re.findall(pattern, self.url)[0]
        mylistid = ""  # 投稿動画の場合はmylistidは空白

        # タイトルからユーザー名を取得
        title_lx = soup.find_all("title")
        pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
        username = re.findall(pattern, title_lx[0].text)[0]

        # マイリスト名収集
        # 投稿動画の場合はマイリスト名がないのでユーザー名と合わせて便宜上の名前に設定
        myshowname = "投稿動画"
        showname = f"{username}さんの投稿動画"

        # 動画エントリ取得
        video_id_list = []
        title_list = []
        registered_at_list = []
        video_url_list = []
        items_lx = soup.find_all("item")
        for item in items_lx:
            # 動画エントリパース
            video_id, title, registered_at, video_url = self._get_iteminfo(item)

            # パース結果チェック
            if (video_id == "") or (title == "") or (registered_at == "") or (video_url == ""):
                continue

            # 格納
            video_id_list.append(video_id)
            title_list.append(title)
            registered_at_list.append(registered_at)
            video_url_list.append(video_url)

        # 返り値設定
        res = {
            "userid": userid,
            "mylistid": mylistid,
            "showname": showname,
            "myshowname": myshowname,
            "video_id_list": video_id_list,
            "title_list": title_list,
            "registered_at_list": registered_at_list,
            "video_url_list": video_url_list,
        }
        return res

    async def _analysis_mylist_page(self, soup: BeautifulSoup) -> dict:
        """マイリストページのRSSを解析する

        Notes:
            動画投稿者リストを取得するために動画IDリストを用いて動画情報APIに問い合わせている

        Args:
            soup (BeautifulSoup): 解析対象のxml

        Returns:
            dict: 解析結果をまとめた辞書
                {
                    "userid": userid,                           # ユーザーID 1234567
                    "mylistid": mylistid,                       # マイリストID 12345678
                    "showname": showname,                       # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
                    "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
                    "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
                    "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                    "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
                    "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                }

        Raises:
            IndexError, TypeError, ValueError: html解析失敗時
        """
        # マイリスト作成者のユーザーIDとマイリストIDを取得
        pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)"
        userid, mylistid = re.findall(pattern, self.url)[0]

        # 対象のマイリストを作成したユーザー名を取得
        creator_lx = soup.find_all("dc:creator")
        username = creator_lx[0].text

        # マイリスト名収集
        # マイリストの場合はタイトルから取得
        title_lx = soup.find_all("title")
        pattern = "^マイリスト (.*)‐ニコニコ動画$"
        myshowname = re.findall(pattern, title_lx[0].text)[0]
        showname = f"「{myshowname}」-{username}さんのマイリスト"

        # 動画エントリ取得
        video_id_list = []
        title_list = []
        registered_at_list = []
        video_url_list = []
        items_lx = soup.find_all("item")
        for item in items_lx:
            # 動画エントリパース
            video_id, title, registered_at, video_url = self._get_iteminfo(item)

            # パース結果チェック
            if (video_id == "") or (title == "") or (registered_at == "") or (video_url == ""):
                continue

            # 格納
            video_id_list.append(video_id)
            title_list.append(title)
            registered_at_list.append(registered_at)
            video_url_list.append(video_url)

        # 返り値設定
        res = {
            "userid": userid,
            "mylistid": mylistid,
            "showname": showname,
            "myshowname": myshowname,
            "video_id_list": video_id_list,
            "title_list": title_list,
            "registered_at_list": registered_at_list,
            "video_url_list": video_url_list,
        }
        return res

    async def _analysis_rss(self, soup: BeautifulSoup) -> dict:
        """RSSを解析する

        Notes:
            url_typeから投稿動画ページかマイリストページかを識別して処理を分ける
            解析結果のdictの値の正当性はチェックしない

        Args:
            soup (BeautifulSoup): 解析対象のxml

        Returns:
            dict: 解析結果をまとめた辞書
                {
                    "userid": userid,                           # ユーザーID 1234567
                    "mylistid": mylistid,                       # マイリストID 12345678
                    "showname": showname,                       # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
                    "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
                    "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
                    "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                    "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
                    "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                }

        Raises:
            IndexError, TypeError: html解析失敗時
            ValueError: url_typeが不正 または html解析失敗時
        """
        res = None
        if self.url_type == "uploaded":
            res = await self._analysis_uploaded_page(soup)
        elif self.url_type == "mylist":
            res = await self._analysis_mylist_page(soup)

        if not res:
            raise ValueError("rss analysis failed.")

        return res

    async def _fetch_videoinfo_from_rss(self) -> list[dict]:
        """投稿動画/マイリストページアドレスから掲載されている動画の情報を取得する

        Notes:
            self.RESULT_DICT_COLS をキーとする情報を辞書で返す
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
            table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
            RSSは取得が速い代わりに最大30件までしか情報を取得できない

        Returns:
            video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照, エラー時 空リスト
        """
        # RSS取得
        session, response = await self._get_session_response(self.request_url + self.RSS_URL_SUFFIX, False, "lxml-xml", None)
        await session.close()
        if not response:
            raise ValueError("rss request failed.")

        # RSS一時保存（DEBUG用）
        # config = ConfigMain.ProcessConfigBase.GetConfig()
        # rd_str = config["general"].get("rss_save_path", "")
        # rd_path = Path(rd_str)
        # rd_path.mkdir(exist_ok=True, parents=True)
        # with (rd_path / "current.xml").open("w", encoding="utf-8") as fout:
        #     fout.write(response.text)

        # RSSから必要な情報を収集する
        # res = {
        #     "userid": userid,                           # ユーザーID 1234567
        #     "mylistid": mylistid,                       # マイリストID 12345678
        #     "showname": showname,                       # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
        #     "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
        #     "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
        #     "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
        #     "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        #     "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        # }
        soup = BeautifulSoup(response.text, "lxml-xml")
        soup_d = await self._analysis_rss(soup)

        video_id_list = soup_d.get("video_id_list")

        # 動画IDについてAPIを通して情報を取得する
        # res = {
        #     "video_id_list": video_id_list,     # 動画IDリスト [sm12345678]
        #     "title_list": title_list,           # 動画タイトルリスト [テスト動画]
        #     "uploaded_at_list": uploaded_at_list,     # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
        #     "video_url_list": video_url_list,   # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        #     "username_list": username_list,     # 投稿者リスト [投稿者1]
        # }
        api_d = await self._get_videoinfo_from_api(video_id_list)

        # バリデーション
        if soup_d.get("title_list") != api_d.get("title_list"):
            raise ValueError("video title from rss and from api is different.")
        if soup_d.get("video_url_list") != api_d.get("video_url_list"):
            raise ValueError("video url from rss and from api is different.")

        # 動画情報をそれぞれ格納
        mylist_url = self.url
        video_d = dict(soup_d, **api_d)
        userid = video_d.get("userid")
        mylistid = video_d.get("mylistid")
        showname = video_d.get("showname")
        myshowname = video_d.get("myshowname")
        video_id_list = video_d.get("video_id_list")
        title_list = video_d.get("title_list")
        registered_at_list = video_d.get("registered_at_list")
        uploaded_at_list = video_d.get("uploaded_at_list")
        video_url_list = video_d.get("video_url_list")
        username_list = video_d.get("username_list")

        # src_df: RSSに記載されている日付形式
        # dst_df: NNMMで扱う日付形式
        src_df = "%a, %d %b %Y %H:%M:%S %z"
        dst_df = "%Y-%m-%d %H:%M:%S"

        # バリデーション
        # {
        #     "userid": userid,                         # ユーザーID 1234567
        #     "mylistid": mylistid,                     # マイリストID 12345678
        #     "showname": showname,                     # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
        #     "myshowname": myshowname,                 # マイリスト名 「まとめマイリスト」
        #     "video_id_list": video_id_list,           # 動画IDリスト [sm12345678]
        #     "title_list": title_list,                 # 動画タイトルリスト [テスト動画]
        #     "uploaded_at_list": uploaded_at_list,     # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
        #     "registered_at_list": registered_at_list, # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        #     "video_url_list": video_url_list,         # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        #     "username_list": username_list,           # 投稿者リスト [投稿者1]
        # }
        try:
            if not (isinstance(userid, str) and isinstance(mylistid, str) and isinstance(showname, str) and isinstance(myshowname, str)):
                raise ValueError
            if not (userid != "" and showname != "" and myshowname != ""):
                raise ValueError
            if not isinstance(video_id_list, list):
                raise ValueError
            if not isinstance(title_list, list):
                raise ValueError
            if not isinstance(uploaded_at_list, list):
                raise ValueError
            if not isinstance(registered_at_list, list):
                raise ValueError
            if not isinstance(video_url_list, list):
                raise ValueError
            if not isinstance(username_list, list):
                raise ValueError
            num = len(video_id_list)
            if not (len(title_list) == num and len(uploaded_at_list) == num and len(registered_at_list) == num and len(video_url_list) == num and len(username_list) == num):
                raise ValueError

            if not re.search("[0-9]+", userid):
                raise ValueError
            if mylistid == "":
                if self.url_type != "uploaded":
                    raise ValueError
            else:
                if not re.search("[0-9]+", mylistid):
                    raise ValueError

            for video_id, title, uploaded_at, registered_at, video_url, username in zip(video_id_list, title_list, uploaded_at_list, registered_at_list, video_url_list, username_list):
                if not re.search("sm[0-9]+", video_id):
                    raise ValueError
                if title == "":
                    raise ValueError
                dt = datetime.strptime(uploaded_at, dst_df)  # 日付形式が正しく変換されるかチェック
                dt = datetime.strptime(registered_at, dst_df)  # 日付形式が正しく変換されるかチェック
                if not re.search("https://www.nicovideo.jp/watch/sm[0-9]+", video_url):
                    raise ValueError
                if username == "":
                    raise ValueError
        except Exception:
            raise ValueError("validation failed.")

        # config取得
        config = ConfigMain.ProcessConfigBase.GetConfig()
        if not config:
            raise ValueError("config read failed.")

        # RSS保存
        rd_str = config["general"].get("rss_save_path", "")
        rd_path = Path(rd_str)
        rd_path.mkdir(exist_ok=True, parents=True)
        rss_file_name = f"{userid}.xml"
        if mylistid != "":
            rss_file_name = f"{userid}_{mylistid}.xml"
        try:
            with (rd_path / rss_file_name).open("w", encoding="utf-8") as fout:
                fout.write(response.text)
        except Exception:
            logger.error("RSS file save failed , but continue process.")
            logger.error(traceback.format_exc())
            pass  # 仮に書き込みに失敗しても以降の処理は続行する

        # 結合
        res = []
        now_date = datetime.now()
        for video_id, title, uploaded_at, registered_at, username, video_url in zip(video_id_list, title_list, uploaded_at_list, registered_at_list, username_list, video_url_list):
            # 登録日時が未来日の場合、登録しない（投稿予約など）
            if now_date < datetime.strptime(registered_at, dst_df):
                continue

            # 出力インターフェイスチェック
            value_list = [-1, video_id, title, username, "", uploaded_at, registered_at, video_url, mylist_url, showname, myshowname]
            if len(self.RESULT_DICT_COLS) != len(value_list):
                continue

            # 登録
            res.append(dict(zip(self.RESULT_DICT_COLS, value_list)))

        # 重複削除
        seen = []
        res = [x for x in res if x["video_id"] not in seen and not seen.append(x["video_id"])]

        # No.を付記する
        for i, _ in enumerate(res):
            res[i]["no"] = i + 1

        return res

    async def _fetch_videoinfo(self) -> list[dict]:
        return await self._fetch_videoinfo_from_rss()


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    ConfigMain.ProcessConfigBase.SetConfig()

    urls = [
        # "https://www.nicovideo.jp/user/37896001/video",  # 投稿動画
        # "https://www.nicovideo.jp/user/12899156/mylist/39194985",  # 中量マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/67376990",  # 少量マイリスト
        "https://www.nicovideo.jp/user/6063658/mylist/72036443",  # テスト用マイリスト
        # "https://www.nicovideo.jp/user/12899156/mylist/99999999",  # 存在しないマイリスト
    ]

    loop = asyncio.new_event_loop()
    for url in urls:
        video_list = loop.run_until_complete(VideoInfoRssFetcher.fetch_videoinfo(url))
        pprint.pprint(video_list)

    pass
