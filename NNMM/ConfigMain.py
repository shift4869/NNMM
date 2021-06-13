# coding: utf-8
import configparser
import logging.config
import shutil
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM.CSVSaveLoad import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *


CONFIG_FILE_PATH = "./config/config.ini"
global_config = None


def GetConfigLayout():
    # オートリロード間隔
    auto_reload_combo_box = sg.InputCombo(
        ("(使用しない)", "15分毎", "30分毎", "60分毎"), default_value="(使用しない)", key="-C_AUTO_RELOAD-", size=(20, 10)
    )

    horizontal_line = "-" * 100

    cf = [
        [sg.Text(horizontal_line)],
        [sg.Text("・「ブラウザで再生」時に使用するブラウザパス")],
        [sg.Input(key="-C_BROWSER_PATH-"), sg.FileBrowse()],
        [sg.Text("・オートリロードする間隔")],
        [auto_reload_combo_box],
        [sg.Text("・RSS保存先パス")],
        [sg.Input(key="-C_RSS_PATH-"), sg.FolderBrowse()],
        [sg.Text("・マイリスト一覧保存")],
        [sg.Button("保存", key="-C_MYLIST_SAVE-")],
        [sg.Text("・マイリスト一覧読込")],
        [sg.Button("読込", key="-C_MYLIST_LOAD-")],
        [sg.Text(horizontal_line)],
        [sg.Text("・マイリスト・動画情報保存DBのパス")],
        [sg.Input(key="-C_DB_PATH-"), sg.FileBrowse()],
        [sg.Text(horizontal_line)],
        [sg.Text("・ニコニコアカウント")],
        [sg.Text("email:", size=(8, 1)), sg.Input(key="-C_ACCOUNT_EMAIL-")],
        [sg.Text("password:", size=(8, 1)), sg.Input(key="-C_ACCOUNT_PASSWORD-", password_char="*")],
        [sg.Text(horizontal_line)],
        [sg.Text("")],
        [sg.Text("")],
        [sg.Column([[sg.Button("設定保存", key="-C_CONFIG_SAVE-")]], justification="right")],
    ]
    layout = [[
        sg.Frame("Config", cf, size=(1070, 100))
    ]]
    return layout


def GetConfig():
    # global_configを返す
    global global_config
    return global_config


def SetConfig():
    # config.iniをロードしてプラグラム内で用いる変数に適用する
    global global_config
    global_config = configparser.ConfigParser()
    global_config.read(CONFIG_FILE_PATH, encoding="utf-8")
    pass


def ProcessConfigLoad(window, values, mylist_db, mylist_info_db):
    # 設定タブを開いたときの処理
    # config.iniをロードして現在の設定値をレイアウトに表示する
    SetConfig()
    c = global_config

    # General
    window["-C_BROWSER_PATH-"].update(value=c["general"]["browser_path"])
    window["-C_AUTO_RELOAD-"].update(value=c["general"]["auto_reload"])
    window["-C_RSS_PATH-"].update(value=c["general"]["rss_save_path"])

    # DB
    window["-C_DB_PATH-"].update(value=c["db"]["save_path"])

    # Niconico
    window["-C_ACCOUNT_EMAIL-"].update(value=c["niconico"]["email"])
    window["-C_ACCOUNT_PASSWORD-"].update(value=c["niconico"]["password"])

    # 選択された状態になるので外す
    window["-C_BROWSER_PATH-"].update(select=False)
    pass


def ProcessMylistSaveCSV(window, values, mylist_db, mylist_info_db):
    # "-C_MYLIST_SAVE-"
    # マイリスト一覧保存ボタンが押されたときの処理
    # 現在のマイリストをcsvとして保存する

    # 保存先ファイルパスをユーザーから取得する
    default_path = Path("") / "result.csv"
    sd_path_str = sg.popup_get_file(
        "保存先ファイル選択",
        default_path=default_path.absolute(),
        default_extension="csv",
        save_as=True
    )

    # キャンセルされた場合は何もしない
    if not sd_path_str:
        return

    # マイリスト保存
    sd_path = Path(sd_path_str)
    res = SaveMylist(mylist_db, str(sd_path))

    # 結果通知
    if res == 0:
        sg.popup("保存完了")
    else:
        sg.popup("保存失敗")
    
    return res


def ProcessMylistLoadCSV(window, values, mylist_db, mylist_info_db):
    # "-C_MYLIST_LOAD-"
    # マイリスト一覧読込ボタンが押されたときの処理
    # csvを読み込んで現在のマイリストに追加する

    # 読込ファイルパスをユーザーから取得する
    default_path = Path("") / "input.csv"
    sd_path_str = sg.popup_get_file(
        "読込ファイル選択",
        default_path=default_path.absolute(),
        default_extension="csv",
        save_as=False
    )

    # キャンセルされた場合は何もしない
    if not sd_path_str:
        return

    # マイリスト読込
    sd_path = Path(sd_path_str)
    res = LoadMylist(mylist_db, str(sd_path))

    # 結果通知
    if res == 0:
        sg.popup("読込完了")
    else:
        sg.popup("読込失敗")

    return res


def ProcessConfigSave(window, values, mylist_db, mylist_info_db):
    # "-C_CONFIG_SAVE-"
    # 設定保存ボタンが押されたときの処理
    # GUIで設定された値をconfig.iniに保存する
    c = configparser.ConfigParser()
    c.read(CONFIG_FILE_PATH, encoding="utf-8")

    # General
    c["general"]["browser_path"] = window["-C_BROWSER_PATH-"].get()
    c["general"]["rss_save_path"] = window["-C_RSS_PATH-"].get()
    # タイマーセットイベントを登録
    c["general"]["auto_reload"] = window["-C_AUTO_RELOAD-"].get()
    window.write_event_value("-TIMER_SET-", "-FIRST_SET-")

    # DB
    db_prev = c["db"]["save_path"]
    db_new = window["-C_DB_PATH-"].get()
    db_move_success = False
    if db_prev != db_new:
        sd_prev = Path(db_prev)
        sd_new = Path(db_new)

        if sd_prev.is_file():
            # 移動先のディレクトリを作成する
            sd_new.parent.mkdir(exist_ok=True, parents=True)

            # DB移動
            shutil.move(sd_prev, sd_new)

            # 以降の処理で新しいパスに移動させたDBを参照するように再設定
            from NNMM import GuiMain
            GuiMain.mylist_db = MylistDBController(db_fullpath=str(sd_new))
            GuiMain.mylist_info_db = MylistInfoDBController(db_fullpath=str(sd_new))

            # 移動成功
            db_move_success = True
    if db_move_success:
        c["db"]["save_path"] = window["-C_DB_PATH-"].get()

    # Niconico
    c["niconico"]["email"] = window["-C_ACCOUNT_EMAIL-"].get()
    c["niconico"]["password"] = window["-C_ACCOUNT_PASSWORD-"].get()

    # ファイルを保存する
    with Path(CONFIG_FILE_PATH).open("w", encoding="utf-8") as fout:
        c.write(fout)
    SetConfig()

    pass


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
