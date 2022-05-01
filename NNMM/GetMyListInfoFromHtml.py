# coding: utf-8
import asyncio
import logging.config
import pprint
import re
import traceback
from datetime import datetime, timedelta
from logging import INFO, getLogger

import pyppeteer
from lxml.html.soupparser import fromstring as soup_parse
from requests_html import AsyncHTMLSession, HTMLResponse, HtmlElement

from NNMM import ConfigMain, GuiFunction


logger = getLogger("root")
logger.setLevel(INFO)


async def GetMyListInfoFromHtml(url: str) -> list[dict]:
    """投稿動画/マイリストページアドレスから掲載されている動画の情報を取得する

    Notes:
        table_colsをキーとする情報を辞書で返す
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
        実際に内部ブラウザでページを開き、
        レンダリングして最終的に表示されたページから動画情報をスクレイピングする
        レンダリングに時間がかかる代わりに最大100件まで取得できる

    Args:
        url (str): 以下のいずれか
                    投稿動画ページのアドレス "^https://www.nicovideo.jp/user/[0-9]+/video$"
                    マイリストのアドレス "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"

    Returns:
        video_info_list (list[dict]): 動画情報をまとめた辞書リスト キーはNotesを参照, エラー時 空リスト
    """
    # 入力チェック
    url_type = GuiFunction.GetURLType(url)
    if url_type not in ["uploaded", "mylist"]:
        logger.error("url_type is invalid , url is not target url.")
        return []

    # ページ取得
    session, response = None, None
    try:
        session, response = await GetAsyncSessionResponse(url, True)
        await session.close()
        if not response:
            logger.error("HTML pages request failed.")
            return []
    except Exception:
        logger.error(traceback.format_exc())
        return []

    # すべての動画リンクを抽出
    # setであるresponse.html.linksを使うと順序の情報が保存できないためタグを見る
    # all_links_set = response.html.links
    # setをlistにキャストするとvalueのみのリストになる
    # all_links_list = list(all_links_set)
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

    # 動画情報を集める
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url", "showname", "mylistname"]
    mylist_url = url

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
    html_d = None
    try:
        html_d = await AnalysisHtml(url_type, response.html.lxml)
    except Exception:
        logger.error(traceback.format_exc())
        return []

    # 動画IDについてAPIを通して情報を取得する
    # res = {
    #     "video_id_list": video_id_list,             # 動画IDリスト [sm12345678]
    #     "title_list": title_list,                   # 動画タイトルリスト [テスト動画]
    #     "uploaded_at_list": uploaded_at_list,       # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
    #     "video_url_list": video_url_list,           # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
    #     "username_list": username_list,             # 投稿者リスト [投稿者1]
    # }
    api_d = None
    try:
        api_d = await GetUsernameFromApi(video_id_list)
    except Exception:
        logger.error(traceback.format_exc())
        return []

    # バリデーション
    if html_d.get("title_list") != api_d.get("title_list"):
        logger.error("video title from html and from api is different.")
        return []
    # uploaded_at はapi_dの方が精度が良いため一致はしない
    # if html_d.get("uploaded_at_list") != api_d.get("uploaded_at_list"):
    #     logger.error("uploaded_at from html and from api is different.")
    #     return []
    if video_url_list != api_d.get("video_url_list"):
        logger.error("video url from html and from api is different.")
        return []

    # 動画情報をそれぞれ格納
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
        logger.error(traceback.format_exc())
        return []

    # 結合
    res = []
    try:
        for video_id, title, uploaded_at, registered_at, username, video_url in zip(video_id_list, title_list, uploaded_at_list, registered_at_list, username_list, video_url_list):
            # 出力インターフェイスチェック
            value_list = [-1, video_id, title, username, "", uploaded_at, registered_at, video_url, mylist_url, showname, myshowname]
            if len(table_cols) != len(value_list):
                continue

            # 登録
            res.append(dict(zip(table_cols, value_list)))
    except Exception:
        logger.error(traceback.format_exc())
        return []

    # No.を付記する
    for i, _ in enumerate(res):
        res[i]["no"] = i + 1

    return res


async def GetAsyncSessionResponse(request_url: str, do_rendering: bool, session: AsyncHTMLSession = None) -> tuple[AsyncHTMLSession, HTMLResponse]:
    """非同期でページ取得する

    Notes:
        この関数で取得したAsyncHTMLSession は呼び出し側で
        await session.close() することを推奨
        接続は MAX_RETRY_NUM = 5 回試行する
        この回数リトライしてもページ取得できなかった場合、responseがNoneとなる

    Args:
        request_url (str): 取得対象ページURL
        do_rendering (bool): 動的にレンダリングするかどうか
        session (AsyncHTMLSession, optional): 使い回すセッションがあれば指定

    Returns:
        session (AsyncHTMLSession): 非同期セッション
        response (HTMLResponse): ページ取得結果のレスポンス
                                 リトライ回数超過時None
                                 正常時 response.html.lxml が非Noneであることが保証されたresponse
    """
    if not session:
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

    MAX_RETRY_NUM = 5
    response = None

    # 初回起動時はchromiumインストールのために時間がかかる
    for _ in range(MAX_RETRY_NUM):
        try:
            response = await session.get(request_url)
            response.raise_for_status()

            if do_rendering:
                await response.html.arender(sleep=2)
            response.raise_for_status()
            # response.html._lxml = soup_parse(response.text, features="lxml-xml")

            if (response is not None) and (response.html.lxml is not None):
                break

            await asyncio.sleep(1)
        except Exception:
            logger.error(traceback.format_exc())
    else:
        response = None

    return (session, response)


def TranslatePageDate(td_str: str) -> str:
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


async def AnalysisHtml(url_type: str, lxml: HtmlElement) -> dict:
    """htmlを解析する

    Notes:
        url_typeから投稿動画ページかマイリストページかを識別して処理を分ける

    Args:
        url_type (str): URLタイプ
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
    if url_type == "uploaded":
        res = await AnalysisUploadedPage(lxml)
    elif url_type == "mylist":
        res = await AnalysisMylistPage(lxml)

    if not res:
        raise ValueError("html analysis failed.")

    return res


async def AnalysisUploadedPage(lxml: HtmlElement) -> dict:
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
    # 探索対象のクラスタグ定数
    TCT_TITLE = "NC-MediaObjectTitle"
    TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
    TCT_USERNAME = "UserDetailsHeader-nickname"

    # エラーメッセージ定数
    MSG_TITLE = f"title parse failed. '{TCT_TITLE}' is not found."
    MSG_UPLOADED1 = f"uploaded_at parse failed. '{TCT_UPLOADED}' is not found."
    MSG_UPLOADED2 = "uploaded_at date parse failed."
    MSG_USERNAME = f"username parse failed. '{TCT_USERNAME}' is not found."

    # 動画名収集
    # 全角スペースは\u3000(unicode-escape)となっている
    title_list = []
    title_lx = lxml.find_class(TCT_TITLE)
    if title_lx == []:
        raise AttributeError(MSG_TITLE)
    title_list = [str(t.text) for t in title_lx]

    # 投稿日時収集
    # src_df: HTMLページに記載されている日付形式
    # dst_df: NNMMで扱う日付形式
    src_df = "%Y/%m/%d %H:%M"
    dst_df = "%Y-%m-%d %H:%M:00"
    uploaded_at_list = []
    try:
        uploaded_at_lx = lxml.find_class(TCT_UPLOADED)
        if uploaded_at_lx == []:
            raise AttributeError(MSG_UPLOADED1)

        for t in uploaded_at_lx:
            tca = str(t.text)
            if "前" in tca or "今" in tca:
                tca = TranslatePageDate(tca)
                if tca != "":
                    uploaded_at_list.append(tca)
                else:
                    raise ValueError
            else:
                dst = datetime.strptime(tca, src_df)
                uploaded_at_list.append(dst.strftime(dst_df))
    except ValueError:
        raise ValueError(MSG_UPLOADED2)

    # 登録日時収集
    # 投稿動画は登録日時は投稿日時と一致する
    registered_at_list = uploaded_at_list

    # 投稿者収集
    username_lx = lxml.find_class(TCT_USERNAME)
    if username_lx == []:
        raise AttributeError(MSG_USERNAME)
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


async def AnalysisMylistPage(lxml: HtmlElement) -> dict:
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
    # 探索対象のクラスタグ定数
    TCT_TITLE = "NC-MediaObjectTitle"
    TCT_UPLOADED = "NC-VideoRegisteredAtText-text"
    TCT_REGISTERED = "MylistItemAddition-addedAt"
    TCT_USERNAME = "UserDetailsHeader-nickname"
    TCT_MYSHOWNAME = "MylistHeader-name"

    # エラーメッセージ定数
    MSG_TITLE = f"title parse failed. '{TCT_TITLE}' is not found."
    MSG_UPLOADED1 = f"uploaded_at parse failed. '{TCT_UPLOADED}' is not found."
    MSG_UPLOADED2 = "uploaded_at date parse failed."
    MSG_REGISTERED1 = f"registered_at parse failed. '{TCT_REGISTERED}' is not found."
    MSG_REGISTERED2 = "registered_at date parse failed."
    MSG_USERNAME = f"username parse failed. '{TCT_USERNAME}' is not found."
    MSG_MYSHOWNAME = f"myshowname parse failed. '{TCT_MYSHOWNAME}' is not found."

    # 動画名収集
    # 全角スペースは\u3000(unicode-escape)となっている
    title_list = []
    title_lx = lxml.find_class(TCT_TITLE)
    if title_lx == []:
        raise AttributeError(MSG_TITLE)
    title_list = [str(t.text) for t in title_lx]

    # 投稿日時収集
    # src_df: HTMLページに記載されている日付形式
    # dst_df: NNMMで扱う日付形式
    src_df = "%Y/%m/%d %H:%M"
    dst_df = "%Y-%m-%d %H:%M:00"
    uploaded_at_list = []
    try:
        uploaded_at_lx = lxml.find_class(TCT_UPLOADED)
        if uploaded_at_lx == []:
            raise AttributeError(MSG_UPLOADED1)

        for t in uploaded_at_lx:
            tca = str(t.text)
            if "前" in tca or "今" in tca:
                tca = TranslatePageDate(tca)
                if tca != "":
                    uploaded_at_list.append(tca)
                else:
                    raise ValueError
            else:
                dst = datetime.strptime(tca, src_df)
                uploaded_at_list.append(dst.strftime(dst_df))
    except ValueError:
        raise ValueError(MSG_UPLOADED2)

    # 登録日時収集
    registered_at_list = []
    try:
        registered_at_lx = lxml.find_class(TCT_REGISTERED)
        if registered_at_lx == []:
            raise AttributeError(MSG_REGISTERED1)

        for t in registered_at_lx:
            tca = str(t.text).replace(" マイリスト登録", "")
            if "前" in tca or "今" in tca:
                tca = TranslatePageDate(tca)
                if tca != "":
                    registered_at_list.append(tca)
                else:
                    raise ValueError
            else:
                dst = datetime.strptime(tca, src_df)
                registered_at_list.append(dst.strftime(dst_df))
    except ValueError:
        raise ValueError(MSG_REGISTERED2)

    # マイリスト作成者名収集
    username_lx = lxml.find_class(TCT_USERNAME)
    if username_lx == []:
        raise AttributeError(MSG_USERNAME)
    username = username_lx[0].text  # マイリスト作成者は元のhtmlに含まれている

    # マイリスト名収集
    showname = ""
    myshowname = ""
    myshowname_lx = lxml.find_class(TCT_MYSHOWNAME)
    if myshowname_lx == []:
        raise AttributeError(MSG_MYSHOWNAME)
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


async def GetUsernameFromApi(video_id_list: list[str]):
    """動画IDから投稿者名を取得する

    Notes:
        video_id_listで渡された動画IDについてAPIを通して投稿者を取得する
        うまく投稿者名が取得出来なかった場合は default_name を割り当てる
        動画情報API："https://ext.nicovideo.jp/api/getthumbinfo/{動画ID}"

    Args:
        video_id_list (list[str]): 動画IDリスト

    Returns:
        dict: 解析結果をまとめた辞書
            {
                "video_id_list": video_id_list,         # 動画IDリスト [sm12345678]
                "title_list": title_list,               # 動画タイトルリスト [テスト動画]
                "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
                "video_url_list": video_url_list,       # 動画URLリスト [https://www.nicovideo.jp/watch/sm12345678]
                "username_list": username_list,         # 投稿者リスト [投稿者1]
            }
    """
    base_url = "https://ext.nicovideo.jp/api/getthumbinfo/"
    src_df = "%Y-%m-%dT%H:%M:%S%z"
    dst_df = "%Y-%m-%d %H:%M:%S"

    title_list = []
    uploaded_at_list = []
    video_url_list = []
    username_list = []
    session = None
    for video_id in video_id_list:
        url = base_url + video_id
        session, response = await GetAsyncSessionResponse(url, False, session)
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
        "uploaded_at_list": uploaded_at_list,   # 投稿日時リスト [%Y-%m-%d %H:%M:%S]
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
    video_list = loop.run_until_complete(GetMyListInfoFromHtml(url))
    # video_list = loop.run_until_complete(GetMyListInfoFromHtmlLightWeight(url))
    pprint.pprint(video_list)

    pass
