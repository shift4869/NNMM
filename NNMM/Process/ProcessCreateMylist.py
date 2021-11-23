# coding: utf-8
import asyncio
import urllib.parse
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase
from NNMM import GetMyListInfo, ConfigMain


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessCreateMylist(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, False, "マイリスト追加")

    def Run(self, mw) -> int:
        """マイリスト追加ボタン押下時の処理

        Notes:
            "-CREATE-"
            左下のマイリスト追加ボタンが押された場合

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
        mylist_url = sg.popup_get_text("追加する マイリスト/ 投稿動画一覧 のURLを入力", title="追加URL")

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

        # マイリスト情報収集
        # 右ペインのテーブルに表示するマイリスト情報を取得
        self.window["-INPUT2-"].update(value="ロード中")
        self.window.refresh()
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url"]
        # asyncでマイリスト情報を収集する
        # pyppeteerでページをレンダリングしてhtmlからスクレイピングする
        loop = asyncio.new_event_loop()
        now_video_list = loop.run_until_complete(GetMyListInfo.AsyncGetMyListInfo(mylist_url))
        s_record = now_video_list[0]
        self.window["-INPUT2-"].update(value="")

        # 新規マイリスト追加
        username = s_record["username"]
        mylistname = s_record["mylistname"]
        showname = s_record["showname"]
        is_include_new = True

        # オートリロード間隔を取得する
        check_interval = ""
        config = ConfigMain.ProcessConfigBase.GetConfig()
        i_str = config["general"].get("auto_reload", "")
        if i_str == "(使用しない)" or i_str == "":
            check_interval = "15分"  # デフォルトは15分
        else:
            pattern = "^([0-9]+)分毎$"
            check_interval = re.findall(pattern, i_str)[0] + "分"

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
                "uploaded_at": m["uploaded"],
                "video_url": m["video_url"],
                "mylist_url": m["mylist_url"],
                "created_at": dst,
            }
            records.append(r)
        self.mylist_info_db.UpsertFromList(records)

        # 後続処理へ
        self.window.write_event_value("-CREATE_THREAD_DONE-", "")
        return 0


class ProcessCreateMylistThreadDone(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, True, "マイリスト追加")

    def Run(self, mw):
        # "-CREATE_THREAD_DONE-"
        # -CREATE-の処理が終わった後の処理
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info("Create mylist end.")


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
