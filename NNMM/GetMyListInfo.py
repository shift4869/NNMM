# coding: utf-8
import configparser
import enum
import logging.config
import re
import urllib.parse
from datetime import date, datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path
from time import sleep
from PySimpleGUI.PySimpleGUI import Table

import asyncio
import emoji
import pyppeteer
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession, AsyncHTMLSession

logger = getLogger("root")
logger.setLevel(INFO)


async def AsyncGetMyListInfoLightWeight(url: str) -> list[dict]:
    # 入力チェック
    pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
    f1 = re.search(pattern, url)
    if not f1:
        return []

    loop = asyncio.get_event_loop()
    soup = None
    test_count = 0
    MAX_TEST_NUM = 5
    while True:
        # 失敗時は繰り返す（最大{MAX_TEST_NUM}回）
        try:
            response = await loop.run_in_executor(None, requests.get, url + "?rss=atom")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml-xml")
        except Exception:
            pass

        if soup:
            break  # 取得成功

        if test_count > MAX_TEST_NUM:
            break  # 取得失敗
        test_count = test_count + 1
        sleep(5)

    # {MAX_TEST_NUM}回requests.getしても失敗した場合はエラー
    if (test_count > MAX_TEST_NUM) or (soup is None):
        return []

    # ループ脱出後はレンダリングが正常に行えたことが保証されている
    # 動画情報を集める
    table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url"]

    # 投稿者収集
    # ひとまず投稿動画の投稿者のみ（単一）
    username = ""
    title_lx = soup.find_all("title")
    pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
    username = re.findall(pattern, title_lx[0].text)[0]

    # 一つのentryから動画ID, 動画名, 投稿日時, URLを抽出する関数
    def GetEntryInfo(entry_lx) -> tuple[str, str, str, str]:
        # 動画ID, 動画名, 投稿日時, URL
        video_id = ""
        title = ""
        uploaded = ""
        video_url = ""

        title = entry_lx.find("title").text

        link_lx = entry_lx.find("link")
        pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+"
        if re.findall(pattern, link_lx.get("href")):
            # クエリ除去してURL部分のみ保持
            video_url = urllib.parse.urlunparse(
                urllib.parse.urlparse(link_lx.get("href"))._replace(query=None)
            )

        pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"
        video_id = re.findall(pattern, video_url)[0]

        published_lx = entry_lx.find("published")
        td_format = "%Y-%m-%dT%H:%M:%S%z"
        dts_format = "%Y-%m-%d %H:%M:%S"
        uploaded = datetime.strptime(published_lx.text, td_format).strftime(dts_format)

        return (video_id, title, uploaded, video_url)

    res = []
    entries_lx = soup.find_all("entry")
    for entry in entries_lx:
        video_id, title, uploaded, video_url = GetEntryInfo(entry)

        value_list = [-1, video_id, title, username, "", uploaded, video_url]
        res.append(dict(zip(table_cols, value_list)))

    return res


async def AsyncGetMyListInfo(url: str) -> list[dict]:
    """投稿動画ページアドレスから掲載されている動画の情報を取得する

    Notes:
        以下をキーとする情報を辞書で返す
        table_cols = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "URL"]

    Args:
        url (str): 投稿動画ページのアドレス

    Returns:
        movie_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照
    """
    # 入力チェック
    pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
    f1 = re.search(pattern, url)
    if not f1:
        return []

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    # セッション開始
    session = AsyncHTMLSession()
    browser = await pyppeteer.launch({
        'ignoreHTTPSErrors': True,
        'headless': True,
        'handleSIGINT': False,
        'handleSIGTERM': False,
        'handleSIGHUP': False
    })
    session._browser = browser

    movie_list = []
    test_count = 0
    MAX_TEST_NUM = 5
    while True:
        # ブラウザエンジンでHTMLを生成
        # 初回起動時はchromiumインストールのために時間がかかる
        try:
            response = await session.get(url)
            await response.html.arender()

            # すべてのリンクを抽出
            # 生成に失敗した場合、動画リンクが取得できないため失敗時は繰り返す（最大{MAX_TEST_NUM}回）
            all_links_set = response.html.links
            all_links_list = list(all_links_set)  # setをlistにキャストするとvalueのみのリストになる
            pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+$"  # ニコニコ動画URLの形式
            movie_list = [s for s in all_links_list if re.search(pattern, s)]
        except Exception:
            pass

        if movie_list or (test_count > MAX_TEST_NUM):
            break
        test_count = test_count + 1
        sleep(5)

    # {MAX_TEST_NUM}回レンダリングしても失敗した場合はエラー
    if test_count > MAX_TEST_NUM:
        return []

    # ループ脱出後はレンダリングが正常に行えたことが保証されている
    # 動画情報を集める
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "URL"]
    table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url"]

    # 動画リンク抽出は降順でないため、ソートする（ロード順？）
    movie_list.sort(reverse=True)  # 降順ソート

    # 動画名収集
    # 全角スペースは\u3000(unicode-escape)となっている
    # lx = r.html.lxml.find_class("NC-MediaObject-main")
    title_lx = response.html.lxml.find_class("NC-MediaObjectTitle")
    title_list = [str(t.text) for t in title_lx]

    # 投稿日時収集
    td_format = "%Y/%m/%d %H:%M"
    dts_format = "%Y-%m-%d %H:%M:00"
    uploaded_lx = response.html.lxml.find_class("NC-VideoMediaObject-metaAdditionalRegisteredAt")
    uploaded_list = []
    for t in uploaded_lx:
        tca = str(t.text)
        if "前" in tca or "今" in tca:
            uploaded_list.append(tca)
        else:
            dst = datetime.strptime(tca, td_format)
            uploaded_list.append(dst.strftime(dts_format))

    # 動画ID収集
    pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"  # ニコニコ動画URLの形式
    video_id_list = [re.findall(pattern, s)[0] for s in movie_list]

    # 投稿者収集
    # ひとまず投稿動画の投稿者のみ（単一）
    username_lx = response.html.lxml.find_class("UserDetailsHeader-nickname")
    username = username_lx[0].text

    # 結合
    res = []
    # 収集した情報の数はそれぞれ一致するはずだが最小のものに合わせる
    list_num_min = min(len(movie_list), len(title_list), len(uploaded_list), len(video_id_list))
    movie_list = movie_list[:list_num_min]
    title_list = title_list[:list_num_min]
    uploaded_list = uploaded_list[:list_num_min]
    video_id_list = video_id_list[:list_num_min]
    if len(movie_list) != len(title_list) or len(title_list) != len(uploaded_list) or len(uploaded_list) != len(video_id_list):
        return []
    for id, title, uploaded, video_url in zip(video_id_list, title_list, uploaded_list, movie_list):
        value_list = [-1, id, title, username, "", uploaded, video_url]
        res.append(dict(zip(table_cols, value_list)))

    # 降順ソート（順番に積み上げているので自然と降順になっているはずだが一応）
    # No.も付記する
    res.sort(key=lambda t: t["video_id"], reverse=True)
    for i, r in enumerate(res):
        res[i]["no"] = i + 1

    await session.close()

    return res


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    CONFIG_FILE_NAME = "./config/config.ini"
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME, encoding="utf8")
    
    url = "https://www.nicovideo.jp/user/12899156/video"
    # movie_list = GetMyListInfoLightWeight(url)
    loop = asyncio.new_event_loop()
    movie_list = loop.run_until_complete(AsyncGetMyListInfoLightWeight(url))
    print(movie_list)

    pass
