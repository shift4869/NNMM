import configparser
import shutil
from pathlib import Path

from PySide6.QtWidgets import QDialog

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result, load_mylist, save_mylist


class ConfigBase(ProcessBase):
    """コンフィグ機能のベースクラス

    派生クラスと外部から使用されるクラス変数とクラスメソッドを定義する
    このベースクラス自体は抽象メソッドであるrunを実装していないためインスタンスは作成できない
    """

    CONFIG_FILE_PATH = "./config/config.ini"
    config = None

    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    @classmethod
    def make_layout(cls):
        """設定画面のレイアウトを作成する

        Returns:
            list[list[sg.Frame]]: PySimpleGUIのレイアウトオブジェクト
        """
        # オートリロード間隔
        auto_reload_combo_box = sg.InputCombo(
            ("(使用しない)", "15分毎", "30分毎", "60分毎"),
            default_value="(使用しない)",
            key="-C_AUTO_RELOAD-",
            size=(20, 10),
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
            [sg.Text("")],
            [sg.Text("")],
            [sg.Column([[sg.Button("設定保存", key="-C_CONFIG_SAVE-")]], justification="right")],
        ]
        layout = [[sg.Frame("Config", cf, size=(500, 580))]]
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
            ConfigBase.set_config()
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


class MylistLoadCSV(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト一覧読込ボタンが押されたときの処理

        Notes:
            "-C_MYLIST_LOAD-"
            csvを読み込んで現在のマイリストに追加する
        """
        # 読込ファイルパスをユーザーから取得する
        default_path = Path("") / "input.csv"
        sd_path_str = sg.popup_get_file(
            "読込ファイル選択", default_path=default_path.absolute(), default_extension="csv", save_as=False
        )

        # キャンセルされた場合は何もしない
        if not sd_path_str:
            return Result.failed

        # マイリスト読込
        sd_path = Path(sd_path_str)
        if not sd_path.is_file():
            sg.popup("読込ファイルが存在しません")
            return Result.failed

        res = load_mylist(self.mylist_db, str(sd_path))

        self.update_mylist_pane()

        # 結果通知
        if res == 0:
            sg.popup("読込完了")
            return Result.success
        else:
            sg.popup("読込失敗")
            return Result.failed


class MylistSaveCSV(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト一覧保存ボタンが押されたときの処理

        Notes:
            "-C_MYLIST_SAVE-"
            現在のマイリストをcsvとして保存する
        """
        # 保存先ファイルパスをユーザーから取得する
        default_path = Path("") / "result.csv"
        sd_path_str = sg.popup_get_file(
            "保存先ファイル選択", default_path=default_path.absolute(), default_extension="csv", save_as=True
        )

        # キャンセルされた場合は何もしない
        if not sd_path_str:
            return Result.failed

        # マイリスト保存
        sd_path = Path(sd_path_str)
        res = save_mylist(self.mylist_db, str(sd_path))

        # 結果通知
        if res == 0:
            sg.popup("保存完了")
            return Result.success
        else:
            sg.popup("保存失敗")
            return Result.failed


class ConfigLoad(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """設定タブを開いたときの処理

        Notes:
            "-TAB_CHANGED-" -> select_tab == "設定"
            config.iniをロードして現在の設定値をレイアウトに表示する
        """
        ConfigBase.set_config()
        c = ConfigBase.get_config()
        window = self.window

        # General
        window["-C_BROWSER_PATH-"].update(value=c["general"]["browser_path"])
        window["-C_AUTO_RELOAD-"].update(value=c["general"]["auto_reload"])
        window["-C_RSS_PATH-"].update(value=c["general"]["rss_save_path"])

        # DB
        window["-C_DB_PATH-"].update(value=c["db"]["save_path"])

        # 選択された状態になるので外す
        window["-C_BROWSER_PATH-"].update(select=False)
        return Result.success


class ConfigSave(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """設定保存ボタンが押されたときの処理

        Notes:
            "-C_CONFIG_SAVE-"
            GUIで設定された値をconfig.iniに保存する
        """
        c = configparser.ConfigParser()
        c.read(ConfigBase.CONFIG_FILE_PATH, encoding="utf-8")
        window = self.window

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
                self.db_fullpath = str(sd_new)
                self.process_info.mylist_db = MylistDBController(db_fullpath=str(sd_new))
                self.process_info.mylist_info_db = MylistInfoDBController(db_fullpath=str(sd_new))

                # 移動成功
                db_move_success = True
        if db_move_success:
            c["db"]["save_path"] = window["-C_DB_PATH-"].get()

        # ファイルを保存する
        with Path(ConfigBase.CONFIG_FILE_PATH).open("w", encoding="utf-8") as fout:
            c.write(fout)
        ConfigBase.set_config()
        return Result.success


if __name__ == "__main__":
    from nnmm import main_window

    mw = main_window.MainWindow()
    mw.run()
