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
from time import sleep

import pyppeteer
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
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]
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

    # 投稿者IDとマイリストID取得
    userid = ""
    mylistid = ""
    try:
        if url_type == "uploaded":
            pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/video"
            userid = re.findall(pattern, url)[0]
            # mylistidは空白のまま
        elif url_type == "mylist":
            pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)"
            userid, mylistid = re.findall(pattern, url)[0]
    except IndexError as e:
        logger.error("url parse failed.")
        logger.error(traceback.format_exc())
        return []

    # マイリストのURLならRSSが取得できるURLに加工
    request_url = url
    if url_type == "mylist":
        # "https://www.nicovideo.jp/mylist/[0-9]+/?rss=2.0" 形式でないとそのマイリストのRSSが取得できない
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        request_url = re.sub("/user/[0-9]+", "", request_url)  # /user/{userid} 部分を削除

    # RSS取得
    loop = asyncio.get_event_loop()
    soup = None
    test_count = 0
    MAX_TEST_NUM = 5
    while True:
        # 失敗時は繰り返す（最大{MAX_TEST_NUM}回）
        try:
            # response = await loop.run_in_executor(None, requests.get, url + "?rss=atom")
            response = await loop.run_in_executor(None, requests.get, request_url + "?rss=2.0")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml-xml")
        except Exception as e:
            logger.error(traceback.format_exc())
            pass

        if soup:
            break  # 取得成功

        if test_count > MAX_TEST_NUM:
            break  # 取得失敗
        test_count = test_count + 1
        sleep(3)

    # {MAX_TEST_NUM}回requests.getしても失敗した場合はエラー
    if (test_count > MAX_TEST_NUM) or (soup is None):
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
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]
    mylist_url = url

    # 投稿者収集
    username = ""
    try:
        if url_type == "uploaded":
            # 投稿動画の場合はタイトルからユーザー名を取得
            title_lx = soup.find_all("title")
            pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
            username = re.findall(pattern, title_lx[0].text)[0]
        elif url_type == "mylist":
            # マイリストの場合は作成者からユーザー名を取得
            creator_lx = soup.find_all("dc:creator")
            username = creator_lx[0].text
    except (IndexError, TypeError) as e:
        logger.error("getting username failed.")
        logger.error(traceback.format_exc())
        return []

    # マイリスト名収集
    showname = ""
    myshowname = ""
    try:
        if url_type == "uploaded":
            # 投稿動画の場合はマイリスト名がないのでユーザー名と合わせて便宜上の名前に設定
            myshowname = "投稿動画"
            showname = f"{username}さんの投稿動画"
        elif url_type == "mylist":
            # マイリストの場合はタイトルから取得
            title_lx = soup.find_all("title")
            pattern = "^マイリスト (.*)‐ニコニコ動画$"
            myshowname = re.findall(pattern, title_lx[0].text)[0]
            showname = f"「{myshowname}」-{username}さんのマイリスト"
    except (IndexError, TypeError) as e:
        logger.error("getting showname failed.")
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
    except Exception as e:
        logger.error("RSS file save failed , but continue process.")
        logger.error(traceback.format_exc())
        pass  # 仮に書き込みに失敗しても以降の処理は続行する

    # td_format: RSSに記載されている日付形式
    # dts_format: NNMMで扱う日付形式
    td_format = "%a, %d %b %Y %H:%M:%S %z"
    dts_format = "%Y-%m-%d %H:%M:%S"

    # 一つのentryから動画ID, 動画タイトル, 投稿日時, 動画URLを抽出する関数
    def GetItemInfo(item_lx) -> tuple[str, str, str, str]:
        # 動画ID, 動画タイトル, 投稿日時, 動画URL
        video_id = ""
        title = ""
        uploaded = ""
        video_url = ""

        try:
            title = item_lx.find("title").text

            link_lx = item_lx.find("link")
            pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+"
            if re.findall(pattern, link_lx.text):
                # クエリ除去してURL部分のみ保持
                video_url = urllib.parse.urlunparse(
                    urllib.parse.urlparse(link_lx.text)._replace(query=None)
                )

            pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
            video_id = re.findall(pattern, video_url)[0]

            pubDate_lx = item_lx.find("pubDate")
            uploaded = datetime.strptime(pubDate_lx.text, td_format).strftime(dts_format)
        except (IndexError, TypeError) as e:
            logger.error("item parse failed.")
            logger.error(traceback.format_exc())
            return ("", "", "", "")
        except ValueError as e:
            logger.error("item date parse failed.")
            logger.error(traceback.format_exc())
            return ("", "", "", "")

        return (video_id, title, uploaded, video_url)

    # 動画エントリ取得
    res = []
    now_date = datetime.now()
    items_lx = soup.find_all("item")
    for i, item in enumerate(items_lx):
        # 動画エントリパース
        video_id, title, uploaded, video_url = GetItemInfo(item)

        # パース結果チェック
        if (video_id == "") or (title == "") or (uploaded == "") or (video_url == ""):
            continue

        # 投稿日時が未来日の場合、登録しない（投稿予約など）
        if now_date < datetime.strptime(uploaded, dts_format):
            continue

        # 出力インターフェイスチェック
        value_list = [i + 1, video_id, title, username, "", uploaded, video_url, mylist_url, showname, myshowname]
        if len(table_cols) != len(value_list):
            continue

        # 登録
        res.append(dict(zip(table_cols, value_list)))

    # 重複削除
    seen = []
    res = [x for x in res if x["video_id"] not in seen and not seen.append(x["video_id"])]

    return res


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    ConfigMain.ProcessConfigBase.SetConfig()

    # url = "https://www.nicovideo.jp/user/37896001/video"
    # url = "https://www.nicovideo.jp/user/12899156/mylist/39194985"
    # url = "https://www.nicovideo.jp/user/12899156/mylist/67376990"
    url = "https://www.nicovideo.jp/user/6063658/mylist/72036443"

    loop = asyncio.new_event_loop()
    video_list = loop.run_until_complete(GetMyListInfoFromRss(url))
    pprint.pprint(video_list)

    pass
