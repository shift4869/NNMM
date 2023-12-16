import re
import urllib.parse
from logging import INFO, getLogger
from typing import Literal

import PySimpleGUI as sg

from NNMM.process import config as process_config
from NNMM.process.base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, get_mylist_type, get_now_datetime, popup_get_text

logger = getLogger(__name__)
logger.setLevel(INFO)


class CreateMylist(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def make_layout(self, url_type: Literal["uploaded", "mylist"], mylist_url: str, window_title: str) -> list[list[sg.Frame]]:
        horizontal_line = "-" * 132
        csize = (20, 1)
        tsize = (50, 1)
        cf = []
        if url_type == "uploaded":
            cf = [
                [sg.Text(horizontal_line)],
                [sg.Text("URL", size=csize), sg.Input(mylist_url, key="-URL-", readonly=True, size=tsize)],
                [sg.Text("URLタイプ", size=csize), sg.Input(url_type, key="-URL_TYPE-", readonly=True, size=tsize)],
                [sg.Text("ユーザー名", size=csize), sg.Input("", key="-USERNAME-", background_color="light goldenrod", size=tsize)],
                [sg.Text(horizontal_line)],
                [sg.Button("登録", key="-REGISTER-"), sg.Button("キャンセル", key="-CANCEL-")],
            ]
        elif url_type == "mylist":
            cf = [
                [sg.Text(horizontal_line)],
                [sg.Text("URL", size=csize), sg.Input(mylist_url, key="-URL-", readonly=True, size=tsize)],
                [sg.Text("URLタイプ", size=csize), sg.Input(url_type, key="-URL_TYPE-", readonly=True, size=tsize)],
                [sg.Text("ユーザー名", size=csize), sg.Input("", key="-USERNAME-", background_color="light goldenrod", size=tsize)],
                [sg.Text("マイリスト名", size=csize), sg.Input("", key="-MYLISTNAME-", background_color="light goldenrod", size=tsize)],
                [sg.Text(horizontal_line)],
                [sg.Button("登録", key="-REGISTER-"), sg.Button("キャンセル", key="-CANCEL-")],
            ]
        layout = [[
            sg.Frame(window_title, cf)
        ]]
        return layout

    def run(self) -> Result:
        """マイリスト追加ボタン押下時の処理

        Notes:
            "-CREATE-"
            左下のマイリスト追加ボタンが押された場合
            またはマイリスト右クリックメニューからマイリスト追加が選択された場合
        """
        logger.info("Create mylist start.")

        # 追加するマイリストURLをユーザーに問い合わせる
        sample_url1 = "https://www.nicovideo.jp/user/*******/video"
        sample_url2 = "https://www.nicovideo.jp/user/*******/mylist/********"
        message = f"追加する マイリスト/ 投稿動画一覧 のURLを入力\n{sample_url1}\n{sample_url2}"
        mylist_url = popup_get_text(message, title="追加URL")

        # キャンセルされた場合
        if mylist_url is None or mylist_url == "":
            logger.info("Create mylist canceled.")
            return Result.failed

        # クエリ除去
        mylist_url = urllib.parse.urlunparse(
            urllib.parse.urlparse(mylist_url)._replace(query=None, fragment=None)
        )

        # 入力されたurlが対応したタイプでない場合何もしない
        url_type = get_mylist_type(mylist_url)
        if url_type == "":
            sg.popup("入力されたURLには対応していません\n新規追加処理を終了します", title="")
            logger.info(f"Create mylist failed, '{mylist_url}' is invalid url.")
            return Result.failed

        # 既存マイリストと重複していた場合何もしない
        prev_mylist = self.mylist_db.select_from_url(mylist_url)
        if prev_mylist:
            sg.popup("既存マイリスト一覧に含まれています\n新規追加処理を終了します", title="")
            logger.info(f"Create mylist canceled, '{mylist_url}' is already included.")
            return Result.failed

        # マイリスト情報収集開始
        self.window["-INPUT2-"].update(value="ロード中")
        self.window.refresh()

        # オートリロード間隔を取得する
        check_interval = ""
        config = process_config.ConfigBase.get_config()
        i_str = config["general"].get("auto_reload", "")
        try:
            if i_str == "(使用しない)" or i_str == "":
                check_interval = "15分"  # デフォルトは15分
            else:
                pattern = r"^([0-9]+)分毎$"
                check_interval = re.findall(pattern, i_str)[0] + "分"
        except IndexError:
            logger.error("Create mylist failed, interval config error.")
            return Result.failed

        # 必要な情報をポップアップでユーザーに問い合わせる
        window_title = "登録情報入力"
        username = ""
        mylistname = ""
        showname = ""
        is_include_new = False

        layout = self.make_layout(url_type, mylist_url, window_title)
        window = sg.Window(title=window_title, layout=layout, auto_size_text=True, finalize=True)
        window["-USERNAME-"].set_focus(True)
        button, values = window.read()
        window.close()
        del window
        if button != "-REGISTER-":
            logger.info("Create mylist canceled.")
            return Result.failed
        else:
            if url_type == "uploaded":
                username = values["-USERNAME-"]
                mylistname = "投稿動画"
                showname = f"{username}さんの投稿動画"
                is_include_new = False
            elif url_type == "mylist":
                username = values["-USERNAME-"]
                mylistname = values["-MYLISTNAME-"]
                showname = f"「{mylistname}」-{username}さんのマイリスト"
                is_include_new = False

        # ユーザー入力値が不正の場合は登録しない
        if any([username == "",
                mylistname == "",
                showname == "",
                check_interval == ""]):
            sg.popup("入力されたマイリスト情報が不正です\n新規追加処理を終了します", title="")
            logger.info(f"Create mylist canceled, can't retrieve the required information.")
            return Result.failed

        # 現在時刻取得
        dst = get_now_datetime()

        # マイリスト情報をDBに格納
        id_index = max([int(r["id"]) for r in self.mylist_db.select()]) + 1
        self.mylist_db.upsert(id_index, username, mylistname, url_type, showname, mylist_url,
                              dst, dst, dst, check_interval, is_include_new)

        # 後続処理へ
        self.window["-INPUT1-"].update(value=mylist_url)
        self.window["-INPUT2-"].update(value="マイリスト追加完了")
        self.window.write_event_value("-CREATE_THREAD_DONE-", "")
        return Result.success


class CreateMylistThreadDone(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト追加の後処理

        Notes:
            "-CREATE_THREAD_DONE-"
            -CREATE-の処理が終わった後の処理
        """
        # マイリスト画面表示更新
        self.update_mylist_pane()

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        self.update_table_pane(mylist_url)

        logger.info("Create mylist success.")
        return


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
