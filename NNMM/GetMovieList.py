# coding: utf-8
import configparser
import logging.config
import re
import urllib.parse
from logging import INFO, getLogger
from pathlib import Path
from time import sleep

import emoji
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession

logger = getLogger("root")
logger.setLevel(INFO)


def GetMovieList(url: str) -> list[str]:
    """マイリストや投稿動画ページアドレスから掲載されている動画のURLを取得する

    Args:
        url (str): マイリストまたは投稿動画ページのアドレス

    Returns:
        movie_list (str): 動画URLリスト
    """
    # セッション開始
    session = HTMLSession()
    r = session.get(url)

    movie_list = []
    test_count = 0
    MAX_TEXT_NUM = 5
    while True:
        # ブラウザエンジンでHTMLを生成
        # 初回起動時はchromiumインストールのために時間がかかる
        r.html.render()

        # すべてのリンクを抽出
        # 生成に失敗した場合、動画リンクが取得できないため失敗時は繰り返す（最大{MAX_TEXT_NUM}回）
        all_links_set = r.html.links
        all_links_list = list(all_links_set)  # setをlistにキャストするとvalueのみのリストになる
        pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+$"  # ニコニコ動画URLの形式
        movie_list = [s for s in all_links_list if re.search(pattern, s)]
        if movie_list or (test_count > MAX_TEXT_NUM):
            break

        test_count = test_count + 1
        sleep(5)

    # print(movie_list)

    return movie_list


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    CONFIG_FILE_NAME = "./config/config.ini"
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME, encoding="utf8")
    
    url = "https://www.nicovideo.jp/user/12899156/video"
    movie_list = GetMovieList(url)

    pass
