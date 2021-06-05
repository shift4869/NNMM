# coding: utf-8
import configparser
import enum
import logging.config
import re
import urllib.parse
from logging import INFO, getLogger
from pathlib import Path
from time import sleep
from PySimpleGUI.PySimpleGUI import Table

import emoji
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession

logger = getLogger("root")
logger.setLevel(INFO)


def GetMyListInfo(url: str) -> list[dict]:
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

    # セッション開始
    session = HTMLSession()
    response = session.get(url)

    movie_list = []
    test_count = 0
    MAX_TEST_NUM = 5
    while True:
        # ブラウザエンジンでHTMLを生成
        # 初回起動時はchromiumインストールのために時間がかかる
        response.html.render()

        # すべてのリンクを抽出
        # 生成に失敗した場合、動画リンクが取得できないため失敗時は繰り返す（最大{MAX_TEST_NUM}回）
        all_links_set = response.html.links
        all_links_list = list(all_links_set)  # setをlistにキャストするとvalueのみのリストになる
        pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+$"  # ニコニコ動画URLの形式
        movie_list = [s for s in all_links_list if re.search(pattern, s)]
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
    table_cols = ["no", "id", "title", "username", "status", "uploaded", "url"]

    # 動画リンク抽出は降順でないため、ソートする（ロード順？）
    movie_list.sort(reverse=True)  # 降順ソート

    # 動画名収集
    # 全角スペースは\u3000(unicode-escape)となっている
    # lx = r.html.lxml.find_class("NC-MediaObject-main")
    title_lx = response.html.lxml.find_class("NC-MediaObjectTitle")
    title_list = [str(t.text) for t in title_lx]

    # 投稿日時収集
    uploaded_lx = response.html.lxml.find_class("NC-VideoMediaObject-metaAdditionalRegisteredAt")
    uploaded_list = [str(t.text) for t in uploaded_lx]

    # 動画ID収集
    pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"  # ニコニコ動画URLの形式
    movie_id_list = [re.findall(pattern, s)[0] for s in movie_list]

    # 投稿者収集
    # ひとまず投稿動画の投稿者のみ（単一）
    username_lx = response.html.lxml.find_class("UserDetailsHeader-nickname")
    username = username_lx[0].text

    # 結合
    res = []
    # 収集した情報の数はそれぞれ一致するはず
    if len(movie_list) != len(title_list) or len(title_list) != len(uploaded_list) or len(uploaded_list) != len(movie_id_list):
        return []
    for id, title, uploaded, movie_url in zip(movie_id_list, title_list, uploaded_list, movie_list):
        value_list = [-1, id, title, username, "", uploaded, movie_url]
        res.append(dict(zip(table_cols, value_list)))

    # 降順ソート（順番に積み上げているので自然と降順になっているはずだが一応）
    # No.も付記する
    res.sort(key=lambda t: t["id"], reverse=True)
    for i, r in enumerate(res):
        res[i]["no"] = i + 1
    return res


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    CONFIG_FILE_NAME = "./config/config.ini"
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME, encoding="utf8")
    
    url = "https://www.nicovideo.jp/user/12899156/video"
    movie_list = GetMyListInfo(url)
    print(movie_list)

    pass
