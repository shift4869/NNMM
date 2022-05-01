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

import requests
from bs4 import BeautifulSoup
from requests_html import AsyncHTMLSession

from NNMM import ConfigMain, GuiFunction


logger = getLogger("root")
logger.setLevel(INFO)


async def GetMyListInfoFromRss(url: str) -> list[dict]:
    """投稿動画ページアドレスからRSSを通して動画の情報を取得する

    Notes:
        table_colsをキーとする情報を辞書で返す
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
        RSSは取得が速い代わりに最大30件までしか情報を取得できない

    Args:
        url (str): 投稿動画ページのアドレス

    Returns:
        video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照, エラー時 空リスト
    """
    # 入力チェック
    url_type = GuiFunction.GetURLType(url)
    if url_type not in ["uploaded", "mylist"]:
        logger.error("url_type is invalid , not target url.")
        return []

    # マイリストのURLならRSSが取得できるURLに加工
    request_url = url
    if url_type == "mylist":
        # "https://www.nicovideo.jp/mylist/[0-9]+/?rss=2.0" 形式でないとそのマイリストのRSSが取得できない
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        request_url = re.sub("/user/[0-9]+", "", request_url)  # /user/{userid} 部分を削除

    # RSS取得
    soup, response = await GetSoupInstance(request_url)
    if not soup:
        logger.error("RSS request failed.")
        return []

    # RSS一時保存（DEBUG用）
    # config = ConfigMain.ProcessConfigBase.GetConfig()
    # rd_str = config["general"].get("rss_save_path", "")
    # rd_path = Path(rd_str)
    # rd_path.mkdir(exist_ok=True, parents=True)
    # with (rd_path / "current.xml").open("w", encoding="utf-8") as fout:
    #     fout.write(response.text)

    # ループ脱出後はRSS取得が正常に行えたことが保証されている
    # 動画情報を集める
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
    mylist_url = url

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
    try:
        soup_d = await AnalysisSoup(url_type, url, soup)
    except Exception:
        logger.error(traceback.format_exc())
        return []

    video_id_list = soup_d.get("video_id_list")

    # 動画IDについてAPIを通して情報を取得する
    # res = {
    #     "video_id_list": video_id_list,     # 動画IDリスト [sm12345678]
    #     "title_list": title_list,           # 動画タイトルリスト [テスト動画]
    #     "uploaded_at_list": uploaded_at_list,     # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
    #     "video_url_list": video_url_list,   # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
    #     "username_list": username_list,     # 投稿者リスト [投稿者1]
    # }
    try:
        api_d = await GetUsernameFromApi(video_id_list)
    except Exception:
        logger.error(traceback.format_exc())
        return []

    # バリデーション
    if soup_d.get("title_list") != api_d.get("title_list"):
        logger.error("video title from html and from api is different.")
        return []
    if soup_d.get("video_url_list") != api_d.get("video_url_list"):
        logger.error("video url from html and from api is different.")
        return []

    # 動画情報をそれぞれ格納
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
            if url_type != "uploaded":
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
        logger.error(traceback.format_exc())
        return []

    # config取得
    config = ConfigMain.ProcessConfigBase.GetConfig()
    if not config:
        logger.error("config read failed.")
        return []

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

    res = []
    now_date = datetime.now()
    try:
        for video_id, title, uploaded_at, registered_at, username, video_url in zip(video_id_list, title_list, uploaded_at_list, registered_at_list, username_list, video_url_list):
            # 登録日時が未来日の場合、登録しない（投稿予約など）
            if now_date < datetime.strptime(registered_at, dst_df):
                continue

            # 出力インターフェイスチェック
            value_list = [-1, video_id, title, username, "", uploaded_at, registered_at, video_url, mylist_url, showname, myshowname]
            if len(table_cols) != len(value_list):
                continue

            # 登録
            res.append(dict(zip(table_cols, value_list)))
    except Exception:
        logger.error(traceback.format_exc())
        return []

    # 重複削除
    seen = []
    res = [x for x in res if x["video_id"] not in seen and not seen.append(x["video_id"])]

    # No.を付記する
    for i, _ in enumerate(res):
        res[i]["no"] = i + 1

    return res


async def GetSoupInstance(request_url: str, suffix: str = "?rss=2.0") -> tuple[BeautifulSoup, requests.Response]:
    """ページ取得してBeautifulSoupインスタンスを取得する

    Notes:
        request_urlの末尾に suffix = "?rss=2.0" を付与してRSS取得を試みる
        接続は MAX_RETRY_NUM = 5 回試行する
        この回数リトライしてもページ取得できなかった場合、返り値がNoneになる

    Args:
        request_url (str): 以下のいずれか
                            投稿動画ページのアドレス "^https://www.nicovideo.jp/user/[0-9]+/video$"
                            マイリストのアドレス "^https://www.nicovideo.jp/mylist/[0-9]+$"

    Returns:
        soup (BeautifulSoup): BeautifulSoupインスタンス, 失敗時None
        response (HTMLResponse): ページ取得結果のレスポンス, 失敗時None
    """
    MAX_RETRY_NUM = 5
    loop = asyncio.get_event_loop()
    soup = None
    response = None
    for _ in range(MAX_RETRY_NUM):
        try:
            # response = await loop.run_in_executor(None, requests.get, url + "?rss=atom")
            response = await loop.run_in_executor(None, requests.get, request_url + suffix)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml-xml")

            if soup:
                break  # 取得成功

            await asyncio.sleep(1)
        except Exception:
            logger.error(traceback.format_exc())
    else:
        # 取得失敗
        soup = None
        response = None
    return (soup, response)


def GetItemInfo(item_lx) -> tuple[str, str, str, str]:
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


async def AnalysisSoup(url_type: str, url: str, soup: BeautifulSoup) -> dict:
    """RSSを解析する

    Notes:
        url_typeから投稿動画ページかマイリストページかを識別して処理を分ける
        解析結果のdictの値の正当性はチェックしない

    Args:
        url_type (str): URLタイプ
        url (str): リクエストURL
        soup (BeautifulSoup): BeautifulSoupインスタンス

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
    if url_type == "uploaded":
        res = await AnalysisUploadedPage(url, soup)
    elif url_type == "mylist":
        res = await AnalysisMylistPage(url, soup)

    if not res:
        raise ValueError("html analysis failed.")

    return res


async def AnalysisUploadedPage(url, soup) -> dict:
    """投稿動画ページのRSSを解析する

    Args:
        url (str): リクエストURL
        soup (BeautifulSoup): BeautifulSoupインスタンス

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
    userid = re.findall(pattern, url)[0]
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
        video_id, title, registered_at, video_url = GetItemInfo(item)

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


async def AnalysisMylistPage(url, soup) -> dict:
    """マイリストページのRSSを解析する

    Notes:
        動画投稿者リストを取得するために動画IDリストを用いて動画情報APIに問い合わせている

    Args:
        url (str): リクエストURL
        soup (BeautifulSoup): BeautifulSoupインスタンス

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
    userid, mylistid = re.findall(pattern, url)[0]

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
        video_id, title, registered_at, video_url = GetItemInfo(item)

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


async def GetUsernameFromApi(video_id_list: list[str]) -> dict:
    """動画IDから投稿者名を取得する

    Notes:
        video_id_listで渡された動画IDリストについてそれぞれAPIを通して投稿者を取得する
        うまく投稿者名が取得出来なかった場合は default_name を割り当てる
        動画情報API："https://ext.nicovideo.jp/api/getthumbinfo/{動画ID}"

    Args:
        video_id_list (list[str]): 動画IDリスト

    Returns:
        dict: 解析結果をまとめた辞書
            {
                "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
                "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
                "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                "username_list": username_list,             # 投稿者リスト [投稿者1]
            }
    """
    MAX_RETRY_NUM = 5
    session = AsyncHTMLSession()

    base_url = "https://ext.nicovideo.jp/api/getthumbinfo/"
    src_df = "%Y-%m-%dT%H:%M:%S%z"
    dst_df = "%Y-%m-%d %H:%M:%S"

    title_list = []
    uploaded_at_list = []
    video_url_list = []
    username_list = []
    for video_id in video_id_list:
        url = base_url + video_id
        response = None

        for _ in range(MAX_RETRY_NUM):
            try:
                response = await session.get(url)
                response.raise_for_status()

                if (response is not None) and (response.html.lxml is not None):
                    break

                await asyncio.sleep(1)
            except Exception:
                logger.error(traceback.format_exc())
        else:
            response = None

        if response:
            thumb_lx = response.html.lxml.findall("thumb")[0]

            # 動画タイトル
            title_lx = thumb_lx.findall("title")
            title = title_lx[0].text
            title_list.append(title)

            # 投稿日時
            uploaded_at_lx = thumb_lx.findall("first_retrieve")
            uploaded_at = datetime.strptime(uploaded_at_lx[0].text, src_df).strftime(dst_df)
            uploaded_at_list.append(uploaded_at)

            # 動画URL
            video_url_lx = thumb_lx.findall("watch_url")
            video_url = video_url_lx[0].text
            video_url_list.append(video_url)

            # 投稿者
            username_lx = thumb_lx.findall("user_nickname")
            username = username_lx[0].text
            username_list.append(username)

    await session.close()

    num = len(video_id_list)
    if not (len(title_list) == num and len(uploaded_at_list) == num and len(video_url_list) == num and len(username_list) == num):
        raise ValueError

    res = {
        "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
        "title_list": title_list,               # 動画タイトルリスト [テスト動画]
        "uploaded_at_list": uploaded_at_list,   # 登録日時リスト [%Y-%m-%d %H:%M:%S]
        "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
        "username_list": username_list,         # 投稿者リスト [投稿者1]
    }
    return res


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    ConfigMain.ProcessConfigBase.SetConfig()

    # url = "https://www.nicovideo.jp/user/37896001/video"  # 投稿動画
    # url = "https://www.nicovideo.jp/user/12899156/mylist/39194985"  # 中量マイリスト
    # url = "https://www.nicovideo.jp/user/12899156/mylist/67376990"  # 少量マイリスト
    url = "https://www.nicovideo.jp/user/6063658/mylist/72036443"  # テスト用マイリスト
    # url = "https://www.nicovideo.jp/user/12899156/mylist/99999999"  # 存在しないマイリスト

    loop = asyncio.new_event_loop()
    video_list = loop.run_until_complete(GetMyListInfoFromRss(url))
    pprint.pprint(video_list)

    pass