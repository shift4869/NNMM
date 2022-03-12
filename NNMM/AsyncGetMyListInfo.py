# coding: utf-8
import asyncio
import logging.config
import pprint
import re
import traceback
from datetime import datetime
from logging import INFO, getLogger

import pyppeteer
from requests_html import AsyncHTMLSession, HTMLResponse, HtmlElement

from NNMM import ConfigMain, GuiFunction


logger = getLogger("root")
logger.setLevel(INFO)


async def AsyncGetMyListInfo(url: str) -> list[dict]:
    """投稿動画/マイリストページアドレスから掲載されている動画の情報を取得する

    Notes:
        table_colsをキーとする情報を辞書で返す
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]
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
        logger.error("url_type is invalid , not target url.")
        return []

    # ページ取得
    session, response = None, None
    try:
        session, response = await GetAsyncSessionResponce(url, True)
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
    video_list = []
    pattern = "^https://www.nicovideo.jp/watch/sm[0-9]+$"  # ニコニコ動画URLの形式
    video_link_lx = response.html.lxml.find_class("NC-MediaObject-main")
    for video_link in video_link_lx:
        a = video_link.find("a")
        if re.search(pattern, a.attrib["href"]):
            video_list.append(a.attrib["href"])

    # 動画リンクが1つもない場合は空リストを返して終了
    if video_list == []:
        logger.warning("HTML pages request is success , but video info is nothing.")
        return []

    # 動画情報を集める
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]
    mylist_url = url

    # 動画リンク抽出は降順でないため、ソートする（ロード順？）
    # video_list.sort(reverse=True)  # 降順ソート

    # 動画ID収集
    pattern = "^https://www.nicovideo.jp/watch/(sm[0-9]+)$"  # ニコニコ動画URLの形式
    video_id_list = [re.findall(pattern, s)[0] for s in video_list]

    # 取得ページと動画IDから必要な情報を収集する
    t = None
    try:
        t = await AnalysisHtml(url_type, video_id_list, response.html.lxml)
    except Exception:
        logger.error(traceback.format_exc())
        return []
    title_list, uploaded_list, username_list, showname, myshowname = t

    # 結合
    res = []
    # 収集した情報の数はそれぞれ一致するはずだが最小のものに合わせる
    list_num_min = min(len(video_list), len(title_list), len(uploaded_list), len(username_list), len(video_id_list))
    video_list = video_list[:list_num_min]
    title_list = title_list[:list_num_min]
    uploaded_list = uploaded_list[:list_num_min]
    username_list = username_list[:list_num_min]
    video_id_list = video_id_list[:list_num_min]
    if len(video_list) != len(title_list) or len(title_list) != len(uploaded_list) or len(uploaded_list) != len(username_list) or len(username_list) != len(video_id_list):
        logger.error("getting video info list length is invalid.")
        return []
    for id, title, uploaded, username, video_url in zip(video_id_list, title_list, uploaded_list, username_list, video_list):
        value_list = [-1, id, title, username, "", uploaded, video_url, mylist_url, showname, myshowname]
        res.append(dict(zip(table_cols, value_list)))

    # No.を付記する
    for i, _ in enumerate(res):
        res[i]["no"] = i + 1

    return res


async def GetAsyncSessionResponce(request_url: str, do_rendering: bool, session: AsyncHTMLSession = None) -> tuple[AsyncHTMLSession, HTMLResponse] | None:
    """_summary_

    Args:
        request_url (_type_): _description_
        do_rendering (_type_): _description_
        session (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_

    Raises:
        ValueError: if arg1 is empty string.
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
            if do_rendering:
                await response.html.arender(sleep=2)

            response.raise_for_status()

            if (response is not None) and (response.html.lxml is not None):
                break

            await asyncio.sleep(1)
        except Exception:
            logger.error(traceback.format_exc())
    else:
        response = None

    return (session, response)


async def AnalysisHtml(url_type: str, video_id_list: list[str], lxml: HtmlElement):
    res = None
    if url_type == "uploaded":
        res = await AnalysisUploadedPage(lxml)
    elif url_type == "mylist":
        res = await AnalysisMylistPage(video_id_list, lxml)

    if isinstance(res, str):
        logger.error(res)
        return (None, None, None, None, None)

    return res


async def AnalysisUploadedPage(lxml: HtmlElement):
    # 動画名収集
    # 全角スペースは\u3000(unicode-escape)となっている
    title_list = []
    try:
        title_lx = lxml.find_class("NC-MediaObjectTitle")
        if title_lx == []:
            raise AttributeError
        title_list = [str(t.text) for t in title_lx]
    except AttributeError as e:
        return "title parse failed."

    # 投稿日時収集
    # td_format: HTMLページに記載されている日付形式
    # dts_format: NNMMで扱う日付形式
    td_format = "%Y/%m/%d %H:%M"
    dts_format = "%Y-%m-%d %H:%M:00"
    uploaded_list = []
    try:
        uploaded_lx = lxml.find_class("NC-VideoRegisteredAtText-text")
        if uploaded_lx == []:
            raise AttributeError

        for t in uploaded_lx:
            tca = str(t.text)
            if "前" in tca or "今" in tca:
                uploaded_list.append(tca)
            else:
                dst = datetime.strptime(tca, td_format)
                uploaded_list.append(dst.strftime(dts_format))
    except AttributeError as e:
        return "uploaded parse failed."
    except ValueError as e:
        return "uploaded date parse failed."

    # 投稿者収集
    # 投稿動画の投稿者は単一であることが保証されている
    username_lx = lxml.find_class("UserDetailsHeader-nickname")
    if username_lx == []:
        return "username parse failed."
    username = username_lx[0].text
    num = len(title_list)
    username_list = [username for i in range(num)]

    # マイリスト名収集
    showname = f"{username}さんの投稿動画"
    myshowname = "投稿動画"
    return (title_list, uploaded_list, username_list, showname, myshowname)


async def AnalysisMylistPage(video_id_list: list[str], lxml: HtmlElement):
    # 動画名収集
    # 全角スペースは\u3000(unicode-escape)となっている
    title_list = []
    try:
        title_lx = lxml.find_class("NC-MediaObjectTitle")
        if title_lx == []:
            raise AttributeError
        title_list = [str(t.text) for t in title_lx]
    except AttributeError as e:
        return "title parse failed."

    # 投稿日時収集
    # td_format: HTMLページに記載されている日付形式
    # dts_format: NNMMで扱う日付形式
    td_format = "%Y/%m/%d %H:%M"
    dts_format = "%Y-%m-%d %H:%M:00"
    uploaded_list = []
    try:
        uploaded_lx = lxml.find_class("NC-VideoRegisteredAtText-text")
        if uploaded_lx == []:
            raise AttributeError

        for t in uploaded_lx:
            tca = str(t.text)
            if "前" in tca or "今" in tca:
                uploaded_list.append(tca)
            else:
                dst = datetime.strptime(tca, td_format)
                uploaded_list.append(dst.strftime(dts_format))
    except AttributeError as e:
        return "uploaded parse failed."
    except ValueError as e:
        return "uploaded date parse failed."

    # 投稿者収集
    username_lx = lxml.find_class("UserDetailsHeader-nickname")
    if username_lx == []:
        return "username parse failed."
    username = username_lx[0].text  # マイリスト作成者は元のhtmlに含まれている
    # 各動画の投稿者は元のhtmlに含まれていないのでAPIを通して取得する
    username_list = await GetUsernameFromApi(video_id_list)

    # マイリスト名収集
    showname = ""
    myshowname = ""
    myshowname_lx = lxml.find_class("MylistHeader-name")
    if myshowname_lx == []:
        return "myshowname parse failed."
    myshowname = myshowname_lx[0].text
    showname = f"「{myshowname}」-{username}さんのマイリスト"
    return (title_list, uploaded_list, username_list, showname, myshowname)


async def GetUsernameFromApi(video_id_list: list[str]):
    # video_id_listで渡された動画IDについてAPIを通して投稿者を取得する
    default_name = "<NULL>"
    base_url = "https://ext.nicovideo.jp/api/getthumbinfo/"
    username_list = []
    session = None
    for video_id in video_id_list:
        username = default_name
        url = base_url + video_id
        session, response = await GetAsyncSessionResponce(url, False, session)
        if response:
            username_lx = response.html.lxml.findall("thumb/user_nickname")
            if username_lx and len(username_lx) == 1:
                username = username_lx[0].text
            else:
                username = default_name
        username_list.append(username)

    await session.close()
    return username_list


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    ConfigMain.ProcessConfigBase.SetConfig()

    # url = "https://www.nicovideo.jp/user/37896001/video"
    # url = "https://www.nicovideo.jp/user/12899156/mylist/39194985"
    # url = "https://www.nicovideo.jp/user/12899156/mylist/67376990"
    url = "https://www.nicovideo.jp/user/6063658/mylist/72036443"
    # url = "https://www.nicovideo.jp/user/12899156/mylist/99999999"

    loop = asyncio.new_event_loop()
    video_list = loop.run_until_complete(AsyncGetMyListInfo(url))
    # video_list = loop.run_until_complete(AsyncGetMyListInfoLightWeight(url))
    pprint.pprint(video_list)

    pass
