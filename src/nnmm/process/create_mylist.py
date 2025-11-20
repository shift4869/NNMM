import re
from logging import INFO, getLogger

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from nnmm.process import config as process_config
from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import MylistType, Result, get_now_datetime, popup, popup_get_text
from nnmm.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory

logger = getLogger(__name__)
logger.setLevel(INFO)


class CreateMylist(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def popup_for_detail(self, mylist_type: MylistType, mylist_url: str, window_title: str) -> dict:
        horizontal_line = "-" * 132
        dialog = QDialog()
        dialog.setWindowTitle(window_title)
        vbox = QVBoxLayout()
        label1 = QLabel(horizontal_line)

        hbox2 = QHBoxLayout()
        label2 = QLabel("URL")
        label2.setMinimumWidth(80)
        tbox2 = QLineEdit(mylist_url, readOnly=True)
        hbox2.addWidget(label2)
        hbox2.addWidget(tbox2)

        hbox3 = QHBoxLayout()
        label3 = QLabel("URLタイプ")
        label3.setMinimumWidth(80)
        tbox3 = QLineEdit(mylist_type.value, readOnly=True)
        hbox3.addWidget(label3)
        hbox3.addWidget(tbox3)

        hbox4 = QHBoxLayout()
        label4 = QLabel("ユーザー名")
        label4.setMinimumWidth(80)
        self.tbox_username = QLineEdit()
        self.tbox_username.setStyleSheet("QLineEdit {background-color: olive;}")
        hbox4.addWidget(label4)
        hbox4.addWidget(self.tbox_username)

        if mylist_type == MylistType.uploaded:
            hbox5 = None
        elif mylist_type == MylistType.mylist:
            hbox5 = QHBoxLayout()
            label5 = QLabel("マイリスト名")
            label5.setMinimumWidth(80)
            self.tbox_mylistname = QLineEdit()
            self.tbox_mylistname.setStyleSheet("QLineEdit {background-color: olive;}")
            hbox5.addWidget(label5)
            hbox5.addWidget(self.tbox_mylistname)
        elif mylist_type == MylistType.series:
            hbox5 = QHBoxLayout()
            label5 = QLabel("シリーズ名")
            label5.setMinimumWidth(80)
            self.tbox_mylistname = QLineEdit()
            self.tbox_mylistname.setStyleSheet("QLineEdit {background-color: olive;}")
            hbox5.addWidget(label5)
            hbox5.addWidget(self.tbox_mylistname)

        label6 = QLabel(horizontal_line)

        hbox7 = QHBoxLayout()
        button_register = QPushButton("登録")
        button_cancel = QPushButton("キャンセル")
        self.register_or_cancel = "cancel"

        def register_or_cancel(args: str) -> None:
            self.register_or_cancel = args
            dialog.close()

        button_register.clicked.connect(lambda: register_or_cancel("register"))
        button_cancel.clicked.connect(lambda: register_or_cancel("cancel"))
        hbox7.addWidget(button_register)
        hbox7.addWidget(button_cancel)

        vbox.addWidget(label1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)
        vbox.addLayout(hbox5) if hbox5 else ""
        vbox.addWidget(label6)
        vbox.addLayout(hbox7)

        dialog.setLayout(vbox)
        dialog.exec()
        result = self.register_or_cancel

        if mylist_type == MylistType.uploaded:
            username = self.tbox_username.text()
            mylistname = "投稿動画"
            showname = f"{username}さんの投稿動画"
            is_include_new = False
        elif mylist_type == MylistType.mylist:
            username = self.tbox_username.text()
            mylistname = self.tbox_mylistname.text()
            showname = f"「{mylistname}」-{username}さんのマイリスト"
            is_include_new = False
        elif mylist_type == MylistType.series:
            username = self.tbox_username.text()
            mylistname = self.tbox_mylistname.text()
            showname = f"「{mylistname}」-{username}さんのシリーズ"
            is_include_new = False
        return {
            "result": result,
            "username": username,
            "mylistname": mylistname,
            "showname": showname,
            "is_include_new": is_include_new,
        }

    def create_component(self) -> QWidget:
        add_mylist_button = QPushButton("マイリスト追加")
        add_mylist_button.clicked.connect(lambda: self.callback())
        return add_mylist_button

    @Slot()
    def callback(self) -> Result:
        """マイリスト追加ボタン押下時の処理

        Notes:
            "-CREATE-"
            左下のマイリスト追加ボタンが押された場合
            またはマイリスト右クリックメニューからマイリスト追加が選択された場合
        """
        logger.info("Create mylist start.")

        # 追加するマイリストURLをユーザーに問い合わせる
        sample_url_list = [
            "https://www.nicovideo.jp/user/*******/video",
            "https://www.nicovideo.jp/user/*******/mylist/********",
            "https://www.nicovideo.jp/user/*******/series/********",
        ]
        sample_url_str = "\n".join(sample_url_list)
        message = "追加するマイリストのURLを入力\n" + sample_url_str
        mylist_url = popup_get_text(message, title="追加マイリストURL")

        # キャンセルされた場合
        if mylist_url is None or mylist_url == "":
            logger.info("Create mylist canceled.")
            return Result.failed

        # 入力されたurlが対応したタイプでない場合何もしない
        try:
            mylist_url = MylistURLFactory.create(mylist_url)
        except Exception:
            popup("入力されたURLには対応していません\n新規追加処理を終了します")
            logger.info(f"Create mylist failed, '{mylist_url}' is invalid url.")
            return Result.failed
        non_query_url = mylist_url.non_query_url
        mylist_type = mylist_url.mylist_type

        # 既存マイリストと重複していた場合何もしない
        prev_mylist = self.mylist_db.select_from_url(non_query_url)
        if prev_mylist:
            popup("既存マイリスト一覧に含まれています\n新規追加処理を終了します")
            logger.info(f"Create mylist canceled, '{non_query_url}' is already included.")
            return Result.failed

        # マイリスト情報収集開始
        self.set_bottom_textbox("ロード中")

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
        check_failed_count = 0
        is_include_new = False

        detail_dict = self.popup_for_detail(mylist_type, non_query_url, window_title)

        if detail_dict["result"] != "register":
            logger.info("Create mylist canceled.")
            return Result.failed
        else:
            username = detail_dict["username"]
            mylistname = detail_dict["mylistname"]
            showname = detail_dict["showname"]
            is_include_new = detail_dict["is_include_new"]

        # ユーザー入力値が不正の場合は登録しない
        if any([username == "", mylistname == "", showname == "", check_interval == ""]):
            popup("入力されたマイリスト情報が不正です\n新規追加処理を終了します")
            logger.info(f"Create mylist canceled, can't retrieve the required information.")
            return Result.failed

        # 現在時刻取得
        dst = get_now_datetime()

        # マイリスト情報をDBに格納
        now_mylist_id_list = [int(r["id"]) for r in self.mylist_db.select()]
        id_index = max(now_mylist_id_list) + 1 if now_mylist_id_list else 1
        self.mylist_db.upsert(
            id_index,
            username,
            mylistname,
            mylist_type.value,
            showname,
            non_query_url,
            dst,
            dst,
            dst,
            check_interval,
            check_failed_count,
            is_include_new,
        )

        # テキストボックス表示更新
        self.set_upper_textbox(non_query_url)
        self.set_bottom_textbox("マイリスト追加完了")

        # マイリスト画面表示更新
        self.update_mylist_pane()

        # テーブル表示更新
        mylist_url = self.get_upper_textbox().to_str()
        self.update_table_pane(mylist_url)

        logger.info("Create mylist done.")
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
        mylist_url = self.get_upper_textbox().to_str()
        self.update_table_pane(mylist_url)

        logger.info("Create mylist done.")
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
