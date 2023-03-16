# coding: utf-8
import configparser
import shutil
from pathlib import Path

import PySimpleGUI as sg

from NNMM.CSVSaveLoad import load_mylist, save_mylist
from NNMM.GuiFunction import update_mylist_pane
from NNMM.MylistDBController import MylistDBController
from NNMM.MylistInfoDBController import MylistInfoDBController
from NNMM.Process import ProcessBase


class ProcessConfigBase(ProcessBase.ProcessBase):
    """コンフィグ機能のベースクラス

    派生クラスと外部から使用されるクラス変数とクラスメソッドを定義する
    このベースクラス自体は抽象メソッドであるrunを実装していないためインスタンスは作成できない
    """
    CONFIG_FILE_PATH = "./config/config.ini"
    config = None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    def make_layout(cls) -> list[list[sg.Frame]]:
        """設定画面のレイアウトを作成する

        Returns:
            list[list[sg.Frame]]: PySimpleGUIのレイアウトオブジェクト
        """
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
            # [sg.Text("・ニコニコアカウント")],
            # [sg.Text("email:", size=(8, 1)), sg.Input(key="-C_ACCOUNT_EMAIL-")],
            # [sg.Text("password:", size=(8, 1)), sg.Input(key="-C_ACCOUNT_PASSWORD-", password_char="*")],
            # [sg.Text(horizontal_line)],
            [sg.Text("")],
            [sg.Text("")],
            [sg.Column([[sg.Button("設定保存", key="-C_CONFIG_SAVE-")]], justification="right")],
        ]
        layout = [[
            sg.Frame("Config", cf, size=(500, 580))
        ]]
        return layout

    @classmethod
    def get_config(cls) -> configparser.ConfigParser:
        """クラス変数configを返す

        Notes:
            外部からもグローバルに参照される

        Returns:
            ConfigParser: クラス変数config
        """
        if not cls.config:
            ProcessConfigBase.set_config()
        return cls.config

    @classmethod
    def set_config(cls) -> configparser.ConfigParser:
        """クラス変数configを設定する

        Notes:
            config.iniをロードしてプラグラム内で用いる変数に適用する

        Returns:
            ConfigParser: クラス変数config
        """
        cls.config = configparser.ConfigParser()
        cls.config.read(cls.CONFIG_FILE_PATH, encoding="utf-8")
        return cls.config


class ProcessMylistLoadCSV(ProcessConfigBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト一覧入力")

    def run(self, mw) -> int:
        """マイリスト一覧読込ボタンが押されたときの処理

        Notes:
            "-C_MYLIST_LOAD-"
            csvを読み込んで現在のマイリストに追加する

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, キャンセル時1, エラー時-1
        """
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
            return 1

        # マイリスト読込
        sd_path = Path(sd_path_str)
        res = load_mylist(mw.mylist_db, str(sd_path))

        update_mylist_pane(mw.window, mw.mylist_db)

        # 結果通知
        if res == 0:
            sg.popup("読込完了")
            return 0
        else:
            sg.popup("読込失敗")
            return -1


class ProcessMylistSaveCSV(ProcessConfigBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト一覧出力")

    def run(self, mw) -> int:
        """マイリスト一覧保存ボタンが押されたときの処理

        Notes:
            "-C_MYLIST_SAVE-"
            現在のマイリストをcsvとして保存する

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, キャンセル時1, エラー時-1
        """
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
            return 1

        # マイリスト保存
        sd_path = Path(sd_path_str)
        res = save_mylist(mw.mylist_db, str(sd_path))

        # 結果通知
        if res == 0:
            sg.popup("保存完了")
            return 0
        else:
            sg.popup("保存失敗")
            return -1


class ProcessConfigLoad(ProcessConfigBase):
    def __init__(self):
        super().__init__(False, False, "設定読込")

    def run(self, mw):
        """設定タブを開いたときの処理

        Notes:
            "-TAB_CHANGED-" -> select_tab == "設定"
            config.iniをロードして現在の設定値をレイアウトに表示する

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0
        """
        ProcessConfigBase.set_config()
        c = ProcessConfigBase.get_config()
        window = mw.window

        # General
        window["-C_BROWSER_PATH-"].update(value=c["general"]["browser_path"])
        window["-C_AUTO_RELOAD-"].update(value=c["general"]["auto_reload"])
        window["-C_RSS_PATH-"].update(value=c["general"]["rss_save_path"])

        # DB
        window["-C_DB_PATH-"].update(value=c["db"]["save_path"])

        # Niconico
        # window["-C_ACCOUNT_EMAIL-"].update(value=c["niconico"]["email"])
        # window["-C_ACCOUNT_PASSWORD-"].update(value=c["niconico"]["password"])

        # 選択された状態になるので外す
        window["-C_BROWSER_PATH-"].update(select=False)
        return 0


class ProcessConfigSave(ProcessConfigBase):
    def __init__(self):
        super().__init__(True, True, "設定保存")

    def run(self, mw):
        """設定保存ボタンが押されたときの処理

        Notes:
            "-C_CONFIG_SAVE-"
            GUIで設定された値をconfig.iniに保存する

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0
        """
        c = configparser.ConfigParser()
        c.read(ProcessConfigBase.CONFIG_FILE_PATH, encoding="utf-8")
        window = mw.window

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
                mw.db_fullpath = str(sd_new)
                mw.mylist_db = MylistDBController(db_fullpath=str(sd_new))
                mw.mylist_info_db = MylistInfoDBController(db_fullpath=str(sd_new))

                # 移動成功
                db_move_success = True
        if db_move_success:
            c["db"]["save_path"] = window["-C_DB_PATH-"].get()

        # Niconico
        # c["niconico"]["email"] = window["-C_ACCOUNT_EMAIL-"].get()
        # c["niconico"]["password"] = window["-C_ACCOUNT_PASSWORD-"].get()

        # ファイルを保存する
        with Path(ProcessConfigBase.CONFIG_FILE_PATH).open("w", encoding="utf-8") as fout:
            c.write(fout)
        ProcessConfigBase.set_config()
        return 0


if __name__ == "__main__":
    ps = ProcessConfigSave()
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.run()
