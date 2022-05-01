# coding: utf-8
import asyncio
import urllib.parse
from logging import INFO, getLogger
from time import sleep

import pyppeteer
import PySimpleGUI as sg
from requests_html import AsyncHTMLSession

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase
from NNMM import ConfigMain, GetMyListInfoFromHtml


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessCreateMylist(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, False, "マイリスト追加")

    async def AsyncGetMyListInfo(self, url: str) -> dict:
        """マイリスト情報を取得する

        Notes:
            以下をキーとする情報を辞書で返す
            table_cols_name = ["作成者", "マイリストURL", "マイリスト表示名", "マイリスト名"]
            table_cols = ["username", "mylist_url", "showname", "mylistname"]
            実際に内部ブラウザでページを開き、
            レンダリングして最終的に表示されたページから動画情報をスクレイピングする
            動画が一つも登録されていないマイリストを前提とするため、動画情報は取得しない

        Args:
            url (str): 投稿動画ページのアドレス

        Returns:
            mylist_info (dict): マイリスト情報をまとめた辞書 キーはNotesを参照, エラー時 空辞書
        """
        # 入力チェック
        url_type = GetURLType(url)
        if url_type not in ["uploaded", "mylist"]:
            logger.error("url_type is invalid , not target url.")
            return {}
 
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

        username = ""
        test_count = 0
        MAX_TEST_NUM = 5
        while True:
            # ブラウザエンジンでHTMLを生成
            # 初回起動時はchromiumインストールのために時間がかかる
            try:
                response = await session.get(url)
                await response.html.arender()

                # 投稿者収集
                # ひとまず投稿動画の投稿者のみ（単一）
                username = ""
                username_lx = response.html.lxml.find_class("UserDetailsHeader-nickname")
                if username_lx != []:
                    username = username_lx[0].text

            except Exception as e:
                logger.error(traceback.format_exc())
                pass

            if (username != "") or (test_count > MAX_TEST_NUM):
                break
            test_count = test_count + 1
            sleep(3)

        # responseの取得成否に関わらずセッションは閉じる
        await session.close()

        # {MAX_TEST_NUM}回レンダリングしても失敗した場合はエラー
        if test_count > MAX_TEST_NUM:
            logger.error("HTML pages request failed.")
            return {}

        # マイリスト作成者情報が取得できなかった場合は空リストを返して終了
        if username == "":
            logger.warning("HTML pages request is success , but username is nothing.")
            return {}

        # ループ脱出後はレンダリングが正常に行えたことが保証されている
        # マイリスト情報を集める
        table_cols_name = ["作成者", "マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["username", "mylist_url", "showname", "mylistname"]
        mylist_url = url

        # マイリスト名収集
        showname = ""
        myshowname = ""
        if url_type == "uploaded":
            showname = f"{username}さんの投稿動画"
            myshowname = "投稿動画"
        elif url_type == "mylist":
            myshowname_lx = response.html.lxml.find_class("MylistHeader-name")
            if myshowname_lx == []:
                logger.error("myshowname parse failed.")
                return {}
            myshowname = myshowname_lx[0].text
            showname = f"「{myshowname}」-{username}さんのマイリスト"

        # 結合
        res = {}
        value_list = [username, mylist_url, showname, myshowname]
        if len(table_cols) != len(value_list):
            return {}
        res = dict(zip(table_cols, value_list))

        return res

    def Run(self, mw) -> int:
        """マイリスト追加ボタン押下時の処理

        Notes:
            "-CREATE-"
            左下のマイリスト追加ボタンが押された場合
            またはマイリスト右クリックメニューからマイリスト追加が選択された場合

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: マイリスト追加に成功したら0,
                 キャンセルされたなら1,
                 エラー時-1
        """
        logger.info("Create mylist start.")
        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("Create mylist failed, argument error.")
            return -1

        # 追加するマイリストURL（候補）
        # mylist_url = self.values["-INPUT1-"]
        # mylist_url = self.values["-INPUT2-"]

        # 追加するマイリストURLをユーザーに問い合わせる
        sample_url1 = "https://www.nicovideo.jp/user/*******/video"
        sample_url2 = "https://www.nicovideo.jp/user/*******/mylist/********"
        # mylist_url = sg.popup_get_text("追加する マイリスト/ 投稿動画一覧 のURLを入力", title="追加URL")
        mylist_url = PopupGetText(f"追加する マイリスト/ 投稿動画一覧 のURLを入力\n{sample_url1}\n{sample_url2}", title="追加URL")

        # キャンセルされた場合
        if mylist_url is None or mylist_url == "":
            logger.info("Create mylist canceled.")
            return 1

        # クエリ除去
        mylist_url = urllib.parse.urlunparse(
            urllib.parse.urlparse(mylist_url)._replace(query=None)
        )

        # 入力されたurlが対応したタイプでない場合何もしない
        url_type = GetURLType(mylist_url)
        if url_type == "":
            sg.popup("入力されたURLには対応していません\n新規追加処理を終了します", title="")
            logger.info(f"Create mylist failed, '{mylist_url}' is invalid url.")
            return 1

        # 既存マイリストと重複していた場合何もしない
        prev_mylist = self.mylist_db.SelectFromURL(mylist_url)
        if prev_mylist:
            sg.popup("既存マイリスト一覧に含まれています\n新規追加処理を終了します", title="")
            logger.info(f"Create mylist canceled, '{mylist_url}' is already included.")
            return 1

        # マイリスト情報収集開始
        self.window["-INPUT2-"].update(value="ロード中")
        self.window.refresh()

        # asyncでマイリスト情報を収集する
        # pyppeteerでページをレンダリングしてhtmlからスクレイピングする
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url"]
        loop = asyncio.new_event_loop()
        now_video_list = loop.run_until_complete(GetMyListInfoFromHtml.GetMyListInfoFromHtml(mylist_url))
        s_record = {}
        if len(now_video_list) > 0:
            # マイリストに所属している動画情報の取得に成功したならば先頭レコードを保持
            s_record = now_video_list[0]
        if not s_record:
            # 動画が一つも登録されていない場合、個別にマイリスト情報を取得する
            s_record = loop.run_until_complete(self.AsyncGetMyListInfo(mylist_url))
        loop.close()

        # マイリスト情報が取得できたか確認
        if not s_record or not(s_record.keys() >= {"username", "mylistname", "showname"}):
            sg.popup("ページ取得に失敗しました\n時間を置いてもう一度試してください\n新規追加処理を終了します", title="")
            logger.error(f"Create mylist failed, '{mylist_url}' getting is failed.")
            return -1

        # 新規マイリスト追加
        username = s_record["username"]
        mylistname = s_record["mylistname"]
        showname = s_record["showname"]
        is_include_new = True

        # オートリロード間隔を取得する
        check_interval = ""
        config = ConfigMain.ProcessConfigBase.GetConfig()
        i_str = config["general"].get("auto_reload", "")
        try:
            if i_str == "(使用しない)" or i_str == "":
                check_interval = "15分"  # デフォルトは15分
            else:
                pattern = "^([0-9]+)分毎$"
                check_interval = re.findall(pattern, i_str)[0] + "分"
        except IndexError:
            logger.error("Create mylist failed, interval config error.")
            return -1

        # 現在時刻取得
        dst = GetNowDatetime()

        # マイリスト情報をDBに格納
        id_index = max([int(r["id"]) for r in self.mylist_db.Select()]) + 1
        self.mylist_db.Upsert(id_index, username, mylistname, url_type, showname, mylist_url, dst, dst, dst, check_interval, is_include_new)

        # 動画情報をDBに格納
        records = []
        for m in now_video_list:
            dst = GetNowDatetime()
            r = {
                "video_id": m["video_id"],
                "title": m["title"],
                "username": m["username"],
                "status": "未視聴",  # 初追加時はすべて未視聴扱い
                "uploaded_at": m["uploaded_at"],
                "registered_at": m["registered_at"],
                "video_url": m["video_url"],
                "mylist_url": m["mylist_url"],
                "created_at": dst,
            }
            records.append(r)
        self.mylist_info_db.UpsertFromList(records)

        # 後続処理へ
        self.window["-INPUT1-"].update(value=mylist_url)
        self.window["-INPUT2-"].update(value="マイリスト追加完了")
        self.window.write_event_value("-CREATE_THREAD_DONE-", "")
        return 0


class ProcessCreateMylistThreadDone(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, True, "マイリスト追加")

    def Run(self, mw) -> int:
        """マイリスト追加の後処理

        Notes:
            "-CREATE_THREAD_DONE-"
            -CREATE-の処理が終わった後の処理

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, エラー時-1
        """
        # "-CREATE_THREAD_DONE-"
        # -CREATE-の処理が終わった後の処理
        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("Create mylist done failed, argument error.")
            return -1

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info("Create mylist success.")
        return 0


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
