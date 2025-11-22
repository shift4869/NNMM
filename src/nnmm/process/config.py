import re
import shutil
import time
from logging import INFO, getLogger
from pathlib import Path

import orjson
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QApplication, QComboBox, QDialog, QFileDialog, QLineEdit, QListWidget, QPushButton
from PySide6.QtWidgets import QWidget

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result, find_values, load_mylist, popup, save_mylist

logger = getLogger(__name__)
logger.setLevel(INFO)


class ConfigBase(ProcessBase):
    """コンフィグ機能のベースクラス

    派生クラスと外部から使用されるクラス変数とクラスメソッドを定義する
    このベースクラス自体は抽象メソッドであるcreate_componentとcallbackを実装していないためインスタンスは作成できない
    """

    CONFIG_FILE_PATH = "./config/config.json"
    config = None

    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    @classmethod
    def get_config(cls) -> dict:
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
    def set_config(cls) -> dict:
        """クラス変数configを設定する

        Notes:
            CONFIG_FILE_PATH をロードしてプラグラム内で用いる変数に適用する

        Returns:
            ConfigParser: クラス変数config
        """
        cls.config = dict()
        if not Path(cls.CONFIG_FILE_PATH).exists():
            raise IOError("Config file not found.")
        cls.config = orjson.loads(Path(cls.CONFIG_FILE_PATH).read_bytes())
        if not cls.config:
            raise IOError("Config file is invalid.")

        # 構造チェック
        match cls.config:
            case {
                "general": {
                    "browser_path": _,
                    "auto_reload": _,
                    "rss_save_path": _,
                },
                "db": _,
            }:
                pass
            case _:
                raise IOError("Config file is invalid structure.")
        return cls.config


class ConfigBrowserPath(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        button = QPushButton("参照")
        button.clicked.connect(lambda: self.callback())
        return button

    @Slot()
    def callback(self) -> Result:
        logger.info("Browser path getting start.")
        if not hasattr(self.window, "tbox_browser_path"):
            # レイアウト作成前に呼び出された場合は何もしない
            logger.info("tbox_browser_path is not found.")
            logger.info("Browser path getting abort.")
            return Result.failed

        # 現状でテキストボックスに入っているパスを初期値とする
        tbox: QLineEdit = self.window.tbox_browser_path
        try:
            now_input_path = Path(tbox.text())
            if not now_input_path.exists():
                now_input_path = Path()
        except Exception:
            now_input_path = Path()

        # ブラウザの実行ファイルパスをユーザーに問い合わせる
        dialog = QFileDialog()
        browser_path_str, filter_str = dialog.getOpenFileName(dir=str(now_input_path))

        if not browser_path_str:
            logger.info(f"Path is empty or canceled.")
            logger.info("RSS path getting abort.")
            return Result.failed

        # 問い合わせ結果を確認
        try:
            browser_path = Path(browser_path_str)
            if not browser_path.exists():
                logger.info(f"Dirname: '{str(browser_path)}' is invalid.")
                logger.info("Browser path getting abort.")
                return Result.failed
        except Exception:
            logger.info(f"Dirname: '{str(browser_path)}' is invalid.")
            logger.info("Browser path getting abort.")
            return Result.failed

        # 新たなディレクトリパスをテキストボックスに設定する
        tbox.setText(str(browser_path))
        logger.info(f"Set browser_path: '{str(browser_path)}'.")
        logger.info("Browser path getting done.")
        return Result.success


class ConfigRSSSavePath(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        button = QPushButton("参照")
        button.clicked.connect(lambda: self.callback())
        return button

    @Slot()
    def callback(self) -> Result:
        logger.info("RSS path getting start.")
        if not hasattr(self.window, "tbox_rss_save_path"):
            # レイアウト作成前に呼び出された場合は何もしない
            logger.info("tbox_rss_save_path is not found.")
            logger.info("RSS path getting abort.")
            return Result.failed

        # 現状でテキストボックスに入っているパスを初期値とする
        tbox: QLineEdit = self.window.tbox_rss_save_path
        try:
            now_input_path = Path(tbox.text())
            if not now_input_path.exists():
                now_input_path = Path()
        except Exception:
            now_input_path = Path()

        # ディレクトリパスをユーザーに問い合わせる
        dialog = QFileDialog()
        rss_path_str = dialog.getExistingDirectory(dir=str(now_input_path))

        if not rss_path_str:
            logger.info(f"Path is empty or canceled.")
            logger.info("RSS path getting abort.")
            return Result.failed

        # 問い合わせ結果を確認
        try:
            rss_path = Path(rss_path_str)
            if not rss_path.exists():
                logger.info(f"Dirname: '{str(rss_path)}' is invalid.")
                logger.info("RSS path getting abort.")
                return Result.failed
        except Exception:
            logger.info(f"Dirname: '{str(rss_path)}' is invalid.")
            logger.info("RSS path getting abort.")
            return Result.failed

        # 新たなディレクトリパスをテキストボックスに設定する
        tbox.setText(str(rss_path))
        logger.info(f"Set rss_path: '{str(rss_path)}'.")
        logger.info("RSS path getting done.")
        return Result.success


class ConfigDBSavePath(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        button = QPushButton("参照")
        button.clicked.connect(lambda: self.callback())
        return button

    @Slot()
    def callback(self) -> Result:
        logger.info("DB path getting start.")
        if not hasattr(self.window, "tbox_db_path"):
            # レイアウト作成前に呼び出された場合は何もしない
            logger.info("tbox_db_path is not found.")
            logger.info("DB path getting abort.")
            return Result.failed

        # 現状でテキストボックスに入っているパスを初期値とする
        tbox: QLineEdit = self.window.tbox_db_path
        try:
            now_input_path = Path(tbox.text())
            if not now_input_path.exists():
                now_input_path = Path()
        except Exception:
            now_input_path = Path()

        # ディレクトリパスをユーザーに問い合わせる
        dialog = QFileDialog()
        db_path_str, filter_str = dialog.getOpenFileName(dir=str(now_input_path))

        if not db_path_str:
            logger.info(f"Path is empty or canceled.")
            logger.info("DB path getting abort.")
            return Result.failed

        # 問い合わせ結果を確認
        try:
            db_path = Path(db_path_str)
            if not db_path.exists():
                logger.info(f"Dirname: '{str(db_path)}' is invalid.")
                logger.info("DB path getting abort.")
                return Result.failed
        except Exception:
            logger.info(f"Dirname: '{str(db_path)}' is invalid.")
            logger.info("DB path getting abort.")
            return Result.failed

        # 新たなディレクトリパスをテキストボックスに設定する
        tbox.setText(str(db_path))
        logger.info(f"Set db_path: '{str(db_path)}'.")
        logger.info("DB path getting done.")
        return Result.success


class MylistLoadCSV(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        button = QPushButton("読込")
        button.clicked.connect(lambda: self.callback())
        return button

    @Slot()
    def callback(self) -> Result:
        """マイリスト一覧読込ボタンが押されたときの処理

        Notes:
            "-C_MYLIST_LOAD-"
            csvを読み込んで現在のマイリストに追加する
        """
        logger.info("Mylist load start.")
        # 読込ファイルパスをユーザーから取得する
        dialog = QFileDialog()
        default_path = Path("") / "input.csv"
        sd_path_str, filter_str = dialog.getOpenFileName(
            caption="読込ファイル選択", dir=str(default_path), filter="CSV file (*.csv)"
        )

        # キャンセルされた場合は何もしない
        if not sd_path_str:
            logger.info("Mylist load canceled.")
            return Result.failed

        # マイリスト読込
        sd_path = Path(sd_path_str)
        if not sd_path.is_file():
            popup("読込ファイルが存在しません")
            logger.info("Mylist load input file not found.")
            return Result.failed

        res = load_mylist(self.mylist_db, str(sd_path))

        time.sleep(1)
        self.update_mylist_pane()

        list_widget: QListWidget = self.window.list_widget
        mylist_row = len(self.mylist_db.select())
        list_widget.setCurrentRow(mylist_row - 1)

        # 結果通知
        if res == Result.success:
            popup("読込完了")
            logger.info("Mylist load done.")
            return Result.success
        else:
            popup("読込失敗")
            logger.info("Mylist load failed.")
            return Result.failed


class MylistSaveCSV(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        button = QPushButton("保存")
        button.clicked.connect(lambda: self.callback())
        return button

    @Slot()
    def callback(self) -> Result:
        """マイリスト一覧保存ボタンが押されたときの処理

        Notes:
            "-C_MYLIST_SAVE-"
            現在のマイリストをcsvとして保存する
        """
        logger.info("Mylist save start.")
        # 保存先ファイルパスをユーザーから取得する
        dialog = QFileDialog()
        default_path = Path("") / "result.csv"
        sd_path_str, filter_str = dialog.getOpenFileName(
            caption="保存先ファイル選択", dir=str(default_path), filter="CSV file (*.csv)"
        )

        # キャンセルされた場合は何もしない
        if not sd_path_str:
            logger.info("Mylist save canceled.")
            return Result.failed

        # マイリスト保存
        sd_path = Path(sd_path_str)
        res = save_mylist(self.mylist_db, str(sd_path))

        # 結果通知
        if res == Result.success:
            popup("保存完了")
            logger.info("Mylist save done.")
            return Result.success
        else:
            popup("保存失敗")
            logger.info("Mylist save failed.")
            return Result.failed


class ConfigLoad(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        """メインウィンドウ初期化時に起動されるためコンポーネントは作成しない"""
        return None

    @Slot()
    def callback(self) -> Result:
        """設定ファイルの内容を画面レイアウトに反映させる処理"""
        logger.info("Config load start.")
        config = ConfigBase.get_config()
        window = self.window

        # コンポーネントチェック
        component_check = [
            isinstance(window, QDialog),
            hasattr(window, "tbox_browser_path"),
            hasattr(window, "cbox"),
            hasattr(window, "tbox_rss_save_path"),
            hasattr(window, "tbox_db_path"),
        ]
        if not all(component_check):
            logger.info("Config load abort.")
            return Result.failed

        browser_path = find_values(config, "browser_path", True)
        auto_reload = find_values(config, "auto_reload", True)
        rss_save_path = find_values(config, "rss_save_path", True)
        db_save_path = find_values(config, "save_path", True, ["db"])

        tbox_browser_path: QLineEdit = window.tbox_browser_path
        tbox_browser_path.setText(browser_path)

        cbox: QComboBox = window.cbox
        combo_box_text = ("(使用しない)", "15分毎", "30分毎", "60分毎")
        cbox.clear()
        cbox.addItems(combo_box_text)

        if auto_reload in combo_box_text:
            cbox.setCurrentText(auto_reload)
        else:
            # 候補にない文言でもフォーマットが合っているなら許容する
            pattern = r"^([0-9]+)分毎$"
            try:
                interval = int(re.findall(pattern, auto_reload)[0])
            except Exception:
                interval = -1
            if interval > 0:
                cbox.addItem(auto_reload)
                cbox.setCurrentText(auto_reload)
            else:
                cbox.setCurrentText("(使用しない)")

        tbox_rss_save_path: QLineEdit = window.tbox_rss_save_path
        tbox_rss_save_path.setText(rss_save_path)

        tbox_db_path: QLineEdit = window.tbox_db_path
        tbox_db_path.setText(db_save_path)

        logger.info("Config load done.")
        return Result.success


class ConfigSave(ConfigBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def create_component(self) -> QWidget:
        button = QPushButton("設定保存")
        button.clicked.connect(lambda: self.callback())
        return button

    @Slot()
    def callback(self) -> Result:
        """設定保存ボタンが押されたときの処理

        Notes:
            画面レイアウトの内容を設定ファイルに反映させる処理
        """
        logger.info("Config save start.")
        prev_config_dict = ConfigBase.get_config()
        new_config_dict = {}
        window = self.window

        # コンポーネントチェック
        component_check = [
            isinstance(window, QDialog),
            hasattr(window, "tbox_browser_path"),
            hasattr(window, "cbox"),
            hasattr(window, "tbox_rss_save_path"),
            hasattr(window, "tbox_db_path"),
        ]
        if not all(component_check):
            logger.info("Config load abort.")
            return Result.failed

        tbox_browser_path: QLineEdit = window.tbox_browser_path
        browser_path = tbox_browser_path.text()

        cbox: QComboBox = window.cbox
        combo_box_text = ("(使用しない)", "15分毎", "30分毎", "60分毎")
        auto_reload = cbox.currentText()
        if auto_reload not in combo_box_text:
            # 候補にない文言でもフォーマットが合っているなら許容する
            pattern = r"^([0-9]+)分毎$"
            try:
                interval = int(re.findall(pattern, auto_reload)[0])
            except Exception:
                interval = -1
            if interval <= 0:
                auto_reload = "(使用しない)"

        tbox_rss_save_path: QLineEdit = window.tbox_rss_save_path
        rss_save_path = tbox_rss_save_path.text()

        tbox_db_path: QLineEdit = window.tbox_db_path
        db_save_path = tbox_db_path.text()

        # DB
        db_prev: str = prev_config_dict["db"]["save_path"]
        db_new: str = db_save_path
        if db_prev != db_new:
            db_move_success = False
            sd_prev = Path(db_prev)
            sd_new = Path(db_new)

            if sd_prev.is_file():
                # 移動先のディレクトリを作成する
                sd_new.parent.mkdir(exist_ok=True, parents=True)

                # DB移動
                try:
                    shutil.move(sd_prev, sd_new)

                    # 以降の処理で新しいパスに移動させたDBを参照するように再設定
                    self.db_fullpath = str(sd_new)
                    self.process_info.mylist_db = MylistDBController(db_fullpath=str(sd_new))
                    self.process_info.mylist_info_db = MylistInfoDBController(db_fullpath=str(sd_new))

                    # 移動成功
                    db_move_success = True
                except Exception:
                    logger.info("DB Path update failed.")

            if not db_move_success:
                db_save_path = db_prev

        # 新しい値の辞書を設定
        new_config_dict = {
            "general": {
                "browser_path": str(browser_path),
                "auto_reload": str(auto_reload),
                "rss_save_path": str(rss_save_path),
            },
            "db": {"save_path": str(db_save_path)},
        }

        Path(ConfigBase.CONFIG_FILE_PATH).write_bytes(orjson.dumps(new_config_dict, option=orjson.OPT_INDENT_2))
        ConfigBase.set_config()

        popup("設定保存完了！")
        logger.info("Config save done.")
        return Result.success


if __name__ == "__main__":
    import sys

    import qdarktheme
    from PySide6.QtWidgets import QApplication

    from nnmm.main_window import MainWindow

    app = QApplication()
    qdarktheme.setup_theme()
    window_main = MainWindow()
    window_main.show()
    sys.exit(app.exec())
