# coding: utf-8
import asyncio
import logging.config
import pprint
import re
import traceback
from datetime import datetime, timedelta
from logging import INFO, getLogger
from urllib.error import HTTPError

from requests_html import HtmlElement

from NNMM import ConfigMain, GuiFunction, VideoInfoFetcherBase


logger = getLogger("root")
logger.setLevel(INFO)


class VideoInfoHtmlFetcher(VideoInfoFetcherBase.VideoInfoFetcherBase):

    def __init__(self, url: str):
        super().__init__(url, "html")

        # 探索対象のクラスタグ定数
        self.TCT_TITLE = "NC-MediaObjectTitle"
        self.TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
        self.TCT_USERNAME = "UserDetailsHeader-nickname"
        self.TCT_REGISTERED = "MylistItemAddition-addedAt"
        self.TCT_MYSHOWNAME = "MylistHeader-name"

        # エラーメッセージ定数
        self.MSG_TITLE = f"title parse failed. '{self.TCT_TITLE}' is not found."
        self.MSG_UPLOADED1 = f"uploaded_at parse failed. '{self.TCT_UPLOADED}' is not found."
        self.MSG_UPLOADED2 = "uploaded_at date parse failed."
        self.MSG_REGISTERED1 = f"registered_at parse failed. '{self.TCT_REGISTERED}' is not found."
        self.MSG_REGISTERED2 = "registered_at date parse failed."
        self.MSG_USERNAME = f"username parse failed. '{self.TCT_USERNAME}' is not found."
        self.MSG_MYSHOWNAME = f"myshowname parse failed. '{self.TCT_MYSHOWNAME}' is not found."

    def _translate_pagedate(self, td_str: str) -> str:
        """動画掲載ページにある日時を解釈する関数

        Note:
            次のいずれかが想定されている
            ["たった今","n分前","n時間前"]

        Args:
            td_str (str): 上記の想定文字列

        Returns:
            str: 成功時 "%Y-%m-%d %H:%M:00"、失敗時 空文字列
        """
        dst_df = "%Y-%m-%d %H:%M:%S"
        try:
            now_date = datetime.now()
            if "今" in td_str:
                return now_date.strftime(dst_df)

            if "分前" in td_str:
                pattern = "^([0-9]+)分前$"
                if re.findall(pattern, td_str):
                    minutes = int(re.findall(pattern, td_str)[0])
                    dst_date = now_date + timedelta(minutes=-minutes)
                    return dst_date.strftime(dst_df)

            if "時間前" in td_str:
                pattern = "^([0-9]+)時間前$"
                if re.findall(pattern, td_str):
                    hours = int(re.findall(pattern, td_str)[0])
                    dst_date = now_date + timedelta(hours=-hours)
                    return dst_date.strftime(dst_df)
        except Exception:
            pass
        return ""

    async def _analysis_uploaded_page(self, lxml: HtmlElement) -> dict:
        """投稿動画ページのhtmlを解析する

        Args:
            lxml (HtmlElement): 投稿動画ページのhtml

        Returns:
            dict: 解析結果をまとめた辞書
                {
                    "showname": showname,                       # マイリスト表示名 「投稿者1さんの投稿動画」
                    "myshowname": myshowname,                   # マイリスト名 「投稿動画」
                    "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                    "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                    "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
                }

        Raises:
            AttributeError: html解析失敗時
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """

        # 動画名収集
        # 全角スペースは\u3000(unicode-escape)となっている
        title_list = []
        title_lx = lxml.find_class(self.TCT_TITLE)
        if title_lx == []:
            raise AttributeError(self.MSG_TITLE)
        title_list = [str(t.text) for t in title_lx]

        # 投稿日時収集
        # src_df: HTMLページに記載されている日付形式
        # dst_df: NNMMで扱う日付形式
        src_df = "%Y/%m/%d %H:%M"
        dst_df = "%Y-%m-%d %H:%M:00"
        uploaded_at_list = []
        try:
            uploaded_at_lx = lxml.find_class(self.TCT_UPLOADED)
            if uploaded_at_lx == []:
                raise AttributeError(self.MSG_UPLOADED1)

            for t in uploaded_at_lx:
                tca = str(t.text)
                if "前" in tca or "今" in tca:
                    tca = self._translate_pagedate(tca)
                    if tca != "":
                        uploaded_at_list.append(tca)
                    else:
                        raise ValueError
                else:
                    dst = datetime.strptime(tca, src_df)
                    uploaded_at_list.append(dst.strftime(dst_df))
        except ValueError:
            raise ValueError(self.MSG_UPLOADED2)

        # 登録日時収集
        # 投稿動画は登録日時は投稿日時と一致する
        registered_at_list = uploaded_at_list

        # 投稿者収集
        username_lx = lxml.find_class(self.TCT_USERNAME)
        if username_lx == []:
            raise AttributeError(self.MSG_USERNAME)
        username = username_lx[0].text

        # マイリスト名収集
        showname = f"{username}さんの投稿動画"
        myshowname = "投稿動画"

        res = {
            "showname": showname,                       # マイリスト表示名 「投稿者1さんの投稿動画」
            "myshowname": myshowname,                   # マイリスト名 「投稿動画」
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        }
        return res

    async def _analysis_mylist_page(self, lxml: HtmlElement) -> dict:
        """マイリストページのhtmlを解析する

        Args:
            lxml (HtmlElement): マイリストページのhtml

        Returns:
            dict: 解析結果をまとめた辞書
                {
                    "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
                    "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
                    "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                    "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                    "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
                }

        Raises:
            AttributeError: html解析失敗時
            ValueError: datetime.strptime 投稿日時解釈失敗時
        """
        # 動画名収集
        # 全角スペースは\u3000(unicode-escape)となっている
        title_list = []
        title_lx = lxml.find_class(self.TCT_TITLE)
        if title_lx == []:
            raise AttributeError(self.MSG_TITLE)
        title_list = [str(t.text) for t in title_lx]

        # 投稿日時収集
        # src_df: HTMLページに記載されている日付形式
        # dst_df: NNMMで扱う日付形式
        src_df = "%Y/%m/%d %H:%M"
        dst_df = "%Y-%m-%d %H:%M:00"
        uploaded_at_list = []
        try:
            uploaded_at_lx = lxml.find_class(self.TCT_UPLOADED)
            if uploaded_at_lx == []:
                raise AttributeError(self.MSG_UPLOADED1)

            for t in uploaded_at_lx:
                tca = str(t.text)
                if "前" in tca or "今" in tca:
                    tca = self._translate_pagedate(tca)
                    if tca != "":
                        uploaded_at_list.append(tca)
                    else:
                        raise ValueError
                else:
                    dst = datetime.strptime(tca, src_df)
                    uploaded_at_list.append(dst.strftime(dst_df))
        except ValueError:
            raise ValueError(self.MSG_UPLOADED2)

        # 登録日時収集
        registered_at_list = []
        try:
            registered_at_lx = lxml.find_class(self.TCT_REGISTERED)
            if registered_at_lx == []:
                raise AttributeError(self.MSG_REGISTERED1)

            for t in registered_at_lx:
                tca = str(t.text).replace(" マイリスト登録", "")
                if "前" in tca or "今" in tca:
                    tca = self._translate_pagedate(tca)
                    if tca != "":
                        registered_at_list.append(tca)
                    else:
                        raise ValueError
                else:
                    dst = datetime.strptime(tca, src_df)
                    registered_at_list.append(dst.strftime(dst_df))
        except ValueError:
            raise ValueError(self.MSG_REGISTERED2)

        # マイリスト作成者名収集
        username_lx = lxml.find_class(self.TCT_USERNAME)
        if username_lx == []:
            raise AttributeError(self.MSG_USERNAME)
        username = username_lx[0].text  # マイリスト作成者は元のhtmlに含まれている

        # マイリスト名収集
        showname = ""
        myshowname = ""
        myshowname_lx = lxml.find_class(self.TCT_MYSHOWNAME)
        if myshowname_lx == []:
            raise AttributeError(self.MSG_MYSHOWNAME)
        myshowname = myshowname_lx[0].text
        showname = f"「{myshowname}」-{username}さんのマイリスト"

        res = {
            "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
            "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
            "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
            "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
            "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        }
        return res

    async def _analysis_html(self, lxml: HtmlElement) -> dict:
        """htmlを解析する

        Notes:
            self.url_typeから投稿動画ページかマイリストページかを識別して処理を分ける

        Args:
            lxml (HtmlElement): 解析対象のhtml

        Returns:
            dict: 解析結果をまとめた辞書
                {
                    "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
                    "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
                    "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                    "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                    "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
                }

        Raises:
            AttributeError: html解析失敗時
            ValueError: url_typeが不正, または datetime.strptime 投稿日時解釈失敗時
        """
        res = None
        if self.url_type == "uploaded":
            res = await self._analysis_uploaded_page(lxml)
        elif self.url_type == "mylist":
            res = await self._analysis_mylist_page(lxml)

        if not res:
            raise ValueError("html analysis failed.")

        return res

    async def _fetch_videoinfo_from_html(self) -> list[dict]:
        """投稿動画/マイリストページアドレスから掲載されている動画の情報を取得する

        Notes:
            self.RESULT_DICT_COLS をキーとする情報を辞書で返す
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
            table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
            実際に内部ブラウザでページを開き、
            レンダリングして最終的に表示されたページから動画情報をスクレイピングする
            レンダリングに時間がかかる代わりに最大100件まで取得できる

        Returns:
            video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照, エラー時 空リスト
        """
        # ページ取得
        session, response = await self._get_session_response(self.request_url, True, "html.parser", None)
        await session.close()
        if not response:
            raise ValueError("html request failed.")

        # すべての動画リンクを抽出
        # setであるresponse.html.linksを使うと順序の情報が保存できないためタグを見る
        # all_links_set = response.html.links
        video_url_list = []
        pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+$"  # ニコニコ動画URLの形式
        video_link_lx = response.html.lxml.find_class("NC-MediaObject-main")
        for video_link in video_link_lx:
            a = video_link.find("a")
            if re.search(pattern, a.attrib["href"]):
                video_url_list.append(a.attrib["href"])

        # 動画リンクが1つもない場合は空リストを返して終了
        if video_url_list == []:
            logger.warning("HTML pages request is success , but video info is nothing.")
            return []

        # 動画リンク抽出は降順でないため、ソートする（ロード順？）
        # video_list.sort(reverse=True)  # 降順ソート

        # 動画ID収集
        pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"  # ニコニコ動画URLの形式
        video_id_list = [re.findall(pattern, s)[0] for s in video_url_list]

        # 取得ページと動画IDから必要な情報を収集する
        # res = {
        #     "showname": showname,                       # マイリスト表示名 「まとめマイリスト」-投稿者1さんのマイリスト
        #     "myshowname": myshowname,                   # マイリスト名 「まとめマイリスト」
        #     "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
        #     "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
        #     "registered_at_list": registered_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        # }
        html_d = await self._analysis_html(response.html.lxml)

        # 動画IDについてAPIを通して情報を取得する
        # res = {
        #     "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
        #     "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
        #     "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
        #     "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        #     "username_list": username_list,             # 投稿者リスト [投稿者1]
        # }
        api_d = await self._get_videoinfo_from_api(video_id_list)

        # バリデーション
        if html_d.get("title_list") != api_d.get("title_list"):
            raise ValueError("video title from html and from api is different.")
        # uploaded_at はapi_dの方が精度が良いため一致はしない
        # if html_d.get("uploaded_at_list") != api_d.get("uploaded_at_list"):
        #     raise ValueError("uploaded_at from html and from api is different.")
        if video_url_list != api_d.get("video_url_list"):
            raise ValueError("video url from html and from api is different.")

        # 動画情報をそれぞれ格納
        mylist_url = self.url
        video_d = dict(html_d, **api_d)
        showname = video_d.get("showname")
        myshowname = video_d.get("myshowname")
        video_id_list = video_d.get("video_id_list")
        title_list = video_d.get("title_list")
        uploaded_at_list = video_d.get("uploaded_at_list")
        registered_at_list = video_d.get("registered_at_list")
        video_url_list = video_d.get("video_url_list")
        username_list = video_d.get("username_list")

        # バリデーション
        # {
        #     "showname": showname,                      # マイリスト表示名 「{myshowname}」-{username}さんのマイリスト
        #     "myshowname": myshowname,                  # マイリスト名 「まとめマイリスト」
        #     "video_id_list": video_id_list,            # 動画IDリスト [sm12345678]
        #     "title_list": title_list,                  # 動画タイトルリスト [テスト動画]
        #     "uploaded_at_list": uploaded_at_list,      # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
        #     "registered_at_list": registered_at_list,  # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        #     "video_url_list": video_url_list,          # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        #     "username_list": username_list,            # 投稿者リスト [投稿者1]
        # }
        dst_df = "%Y-%m-%d %H:%M:%S"
        try:
            if not (isinstance(showname, str) and isinstance(myshowname, str)):
                raise ValueError
            if not (showname != "" and myshowname != ""):
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
            if not (len(title_list) == num and len(uploaded_at_list) == num and len(video_url_list) == num and len(username_list) == num):
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

        # 結合
        res = []
        for video_id, title, uploaded_at, registered_at, username, video_url in zip(video_id_list, title_list, uploaded_at_list, registered_at_list, username_list, video_url_list):
            # 出力インターフェイスチェック
            value_list = [-1, video_id, title, username, "", uploaded_at, registered_at, video_url, mylist_url, showname, myshowname]
            if len(self.RESULT_DICT_COLS) != len(value_list):
                continue

            # 登録
            res.append(dict(zip(self.RESULT_DICT_COLS, value_list)))

        # No.を付記する
        for i, _ in enumerate(res):
            res[i]["no"] = i + 1

        return res

    async def _fetch_videoinfo(self) -> list[dict]:
        return await self._fetch_videoinfo_from_html()


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
        video_list = loop.run_until_complete(VideoInfoHtmlFetcher.fetch_videoinfo(url))
        pprint.pprint(video_list)

    pass
