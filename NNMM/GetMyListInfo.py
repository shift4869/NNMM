# coding: utf-8
import logging.config
import pprint
import re
import urllib.parse
from datetime import datetime
from logging import INFO, getLogger
from pathlib import Path
from time import sleep

import asyncio
import pyppeteer
import requests
from bs4 import BeautifulSoup
from requests_html import AsyncHTMLSession

from NNMM import ConfigMain, GuiFunction


logger = getLogger("root")
logger.setLevel(INFO)


async def AsyncGetMyListInfoLightWeight(url: str) -> list[dict]:
    """投稿動画ページアドレスからRSSを通して動画の情報を取得する

    Notes:
        table_colsをキーとする情報を辞書で返す
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]
        RSSは取得が速い代わりに最大30件までしか情報を取得できない

    Args:
        url (str): 投稿動画ページのアドレス

    Returns:
        video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照
    """
    # 入力チェック
    url_type = GuiFunction.GetURLType(url)
    if url_type == "":
        return []

    # 投稿者IDとマイリストID取得
    userid = ""
    mylistid = ""
    if url_type == "uploaded":
        pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/video"
        userid = re.findall(pattern, url)[0]
        # mylistidは空白のまま
    elif url_type == "mylist":
        pattern = "^http[s]*://www.nicovideo.jp/user/([0-9]+)/mylist/([0-9]+)"
        userid, mylistid = re.findall(pattern, url)[0]

    # マイリストのURLならRSSが取得できるURLに加工
    request_url = url
    if url_type == "mylist":
        pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
        request_url = re.sub("/user/[0-9]+", "", request_url)  # /user/{userid} 部分を削除
        # "https://www.nicovideo.jp/mylist/[0-9]+/?rss=2.0" 形式でないとそのマイリストのRSSが取得できない

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
        except Exception:
            pass

        if soup:
            break  # 取得成功

        if test_count > MAX_TEST_NUM:
            break  # 取得失敗
        test_count = test_count + 1
        sleep(3)

    # {MAX_TEST_NUM}回requests.getしても失敗した場合はエラー
    if (test_count > MAX_TEST_NUM) or (soup is None):
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
    if url_type == "uploaded":
        # 投稿動画の場合はタイトルからユーザー名を取得
        title_lx = soup.find_all("title")
        pattern = "^(.*)さんの投稿動画‐ニコニコ動画$"
        username = re.findall(pattern, title_lx[0].text)[0]
    elif url_type == "mylist":
        # マイリストの場合は作成者からユーザー名を取得
        creator_lx = soup.find_all("dc:creator")
        username = creator_lx[0].text

    # マイリスト名収集
    showname = ""
    myshowname = ""
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

    # RSS保存
    config = ConfigMain.ProcessConfigBase.GetConfig()
    rd_str = config["general"].get("rss_save_path", "")
    rd_path = Path(rd_str)
    rd_path.mkdir(exist_ok=True, parents=True)
    rss_file_name = f"{userid}.xml"
    if mylistid != "":
        rss_file_name = f"{userid}_{mylistid}.xml"
    with (rd_path / rss_file_name).open("w", encoding="utf-8") as fout:
        fout.write(response.text)

    # td_format = "%Y-%m-%dT%H:%M:%S%z"
    td_format = "%a, %d %b %Y %H:%M:%S %z"
    dts_format = "%Y-%m-%d %H:%M:%S"

    # 一つのentryから動画ID, 動画名, 投稿日時, URLを抽出する関数
    def GetItemInfo(item_lx) -> tuple[str, str, str, str]:
        # 動画ID, 動画名, 投稿日時, URL
        video_id = ""
        title = ""
        uploaded = ""
        video_url = ""

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

        return (video_id, title, uploaded, video_url)

    # 動画エントリ取得
    res = []
    now_date = datetime.now()
    items_lx = soup.find_all("item")
    for item in items_lx:
        video_id, title, uploaded, video_url = GetItemInfo(item)

        # 投稿日時が未来日の場合、登録しない（投稿予約など）
        if now_date < datetime.strptime(uploaded, dts_format):
            continue

        value_list = [-1, video_id, title, username, "", uploaded, video_url, mylist_url, showname, myshowname]
        res.append(dict(zip(table_cols, value_list)))
   
    # 重複処理
    seen = []
    res = [x for x in res if x["video_id"] not in seen and not seen.append(x["video_id"])]

    return res


async def AsyncGetMyListInfo(url: str) -> list[dict]:
    """投稿動画ページアドレスから掲載されている動画の情報を取得する

    Notes:
        table_colsをキーとする情報を辞書で返す
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]
        実際に内部ブラウザでページを開き、
        レンダリングして最終的に表示されたページから動画情報をスクレイピングする
        レンダリングに時間がかかる代わりに最大100件まで取得できる

    Args:
        url (str): 投稿動画ページのアドレス

    Returns:
        video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照
    """
    # 入力チェック
    url_type = GuiFunction.GetURLType(url)
    if url_type == "":
        return

    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)

    # セッション開始
    session = AsyncHTMLSession()
    browser = await pyppeteer.launch({
        "ignoreHTTPSErrors": True,
        "headless": True,
        "handleSIGINT": False,
        "handleSIGTERM": False,
        "handleSIGHUP": False
    })
    session._browser = browser

    video_list = []
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
            video_list = [s for s in all_links_list if re.search(pattern, s)]
        except Exception:
            pass

        if video_list or (test_count > MAX_TEST_NUM):
            break
        test_count = test_count + 1
        sleep(3)

    # {MAX_TEST_NUM}回レンダリングしても失敗した場合はエラー
    if test_count > MAX_TEST_NUM:
        return []

    # ループ脱出後はレンダリングが正常に行えたことが保証されている
    # 動画情報を集める
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]
    mylist_url = url

    # 動画リンク抽出は降順でないため、ソートする（ロード順？）
    video_list.sort(reverse=True)  # 降順ソート

    # 動画名収集
    # 全角スペースは\u3000(unicode-escape)となっている
    # lx = r.html.lxml.find_class("NC-MediaObject-main")
    title_lx = response.html.lxml.find_class("NC-MediaObjectTitle")
    title_list = [str(t.text) for t in title_lx]

    # 投稿日時収集
    td_format = "%Y/%m/%d %H:%M"
    dts_format = "%Y-%m-%d %H:%M:00"
    # uploaded_lx = response.html.lxml.find_class("NC-VideoMediaObject-metaAdditionalRegisteredAt")
    uploaded_lx = response.html.lxml.find_class("NC-VideoRegisteredAtText-text")
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
    video_id_list = [re.findall(pattern, s)[0] for s in video_list]

    # 投稿者収集
    # ひとまず投稿動画の投稿者のみ（単一）
    username_lx = response.html.lxml.find_class("UserDetailsHeader-nickname")
    username = username_lx[0].text

    # マイリスト名収集
    showname = ""
    myshowname = ""
    if url_type == "uploaded":
        showname = f"{username}さんの投稿動画"
        myshowname = "投稿動画"
    elif url_type == "mylist":
        myshowname_lx = response.html.lxml.find_class("MylistHeader-name")
        myshowname = myshowname_lx[0].text
        showname = f"「{myshowname}」-{username}さんのマイリスト"

    # 結合
    res = []
    # 収集した情報の数はそれぞれ一致するはずだが最小のものに合わせる
    list_num_min = min(len(video_list), len(title_list), len(uploaded_list), len(video_id_list))
    video_list = video_list[:list_num_min]
    title_list = title_list[:list_num_min]
    uploaded_list = uploaded_list[:list_num_min]
    video_id_list = video_id_list[:list_num_min]
    if len(video_list) != len(title_list) or len(title_list) != len(uploaded_list) or len(uploaded_list) != len(video_id_list):
        return []
    for id, title, uploaded, video_url in zip(video_id_list, title_list, uploaded_list, video_list):
        value_list = [-1, id, title, username, "", uploaded, video_url, mylist_url, showname, myshowname]
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
    ConfigMain.ProcessConfigBase.SetConfig()

    # url = "https://www.nicovideo.jp/user/37896001/video"
    # url = "https://www.nicovideo.jp/user/12899156/mylist/39194985"
    url = "https://www.nicovideo.jp/user/12899156/mylist/67376990"

    loop = asyncio.new_event_loop()
    video_list = loop.run_until_complete(AsyncGetMyListInfoLightWeight(url))
    pprint.pprint(video_list)

    pass
