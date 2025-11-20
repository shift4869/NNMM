from abc import abstractmethod
from logging import INFO, getLogger

from PySide6.QtCore import QDateTime, QDir, QItemSelectionModel, QLibraryInfo, QModelIndex, QPoint, QSysInfo, Qt
from PySide6.QtCore import QTimer, Slot, qVersion
from PySide6.QtGui import QAction, QColor, QCursor, QDesktopServices, QGuiApplication, QIcon, QKeySequence, QPalette
from PySide6.QtGui import QShortcut, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemView, QApplication, QCheckBox, QComboBox, QCommandLinkButton, QDateTimeEdit
from PySide6.QtWidgets import QDial, QDialog, QDialogButtonBox, QFileSystemModel, QGridLayout, QGroupBox, QHBoxLayout
from PySide6.QtWidgets import QHeaderView, QLabel, QLayoutItem, QLineEdit, QListView, QListWidget, QListWidgetItem
from PySide6.QtWidgets import QMenu, QPlainTextEdit, QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy
from PySide6.QtWidgets import QSlider, QSpinBox, QStyleFactory, QTableWidget, QTableWidgetItem, QTabWidget
from PySide6.QtWidgets import QTextBrowser, QTextEdit, QToolBox, QToolButton, QTreeView, QVBoxLayout, QWidget

from nnmm.model import Mylist, MylistInfo
from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result, interval_translate, popup

logger = getLogger(__name__)
logger.setLevel(INFO)


class PopupWindowBase(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

        self.popup_window = None
        self.title = ""
        self.url = ""

    def create_component(self) -> QWidget:
        """右クリックメニューから起動するためコンポーネントは作成しない"""
        return None

    @abstractmethod
    def init(self) -> Result:
        """初期化

        Returns:
            Result: 成功時success, エラー時failed
        """
        raise NotImplementedError

    @abstractmethod
    def create_window_layout(self) -> QVBoxLayout | None:
        """画面のレイアウトを作成する

        Returns:
            QVBoxLayout | None: 成功時レイアウトオブジェクト, 失敗時None
        """
        raise NotImplementedError

    @Slot()
    def callback(self) -> Result:
        logger.info("Popup information window start.")
        # 初期化
        res = self.init()
        if res == Result.failed:
            popup("情報ウィンドウの初期化に失敗しました。")
            return Result.failed

        # ウィンドウレイアウト作成
        layout = self.create_window_layout()
        if not layout:
            popup("情報ウィンドウのレイアウト表示に失敗しました。")
            return Result.failed

        logger.info(f"Show information: {self.url}")

        # ウィンドウオブジェクト作成
        self.popup_window = QDialog()
        self.popup_window.setWindowTitle(self.title)
        self.popup_window.setLayout(layout)
        self.popup_window.exec()

        logger.info("Popup information window done.")
        return Result.success


class PopupMylistWindow(PopupWindowBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def init(self) -> Result:
        """初期化

        Returns:
            Result: 成功時success, エラー時failed
        """
        # 選択されたマイリスト情報を取得する
        selected_mylist_row = self.get_selected_mylist_row()
        if not selected_mylist_row:
            logger.error("Mylist popup window Init failed, mylist is not selected.")
            return Result.failed

        # 選択されたマイリストのShownameを取得する
        # 新着表示のマークがある場合は削除する
        showname = selected_mylist_row.without_new_mark_name()

        # 選択されたマイリストのマイリストレコードオブジェクトを取得する
        record = self.mylist_db.select_from_showname(showname)
        if record and len(record) == 1:
            record = record[0]
        else:
            logger.error("Mylist popup window Init failed, mylist is not found in mylist_db.")
            return Result.failed

        # recordを設定(create_window_layoutで使用する)
        self.record = record
        self.url = record["url"]

        # 子ウィンドウの初期値設定
        self.title = "マイリスト情報"
        return Result.success

    def create_window_layout(self) -> QVBoxLayout | None:
        """画面のレイアウトを作成する

        Notes:
            先にInitを実行し、self.recordを設定しておく必要がある
        """
        # horizontal_line = "-" * 132
        horizontal_line = "-" * 100
        csize = 120

        # self.recordが設定されていない場合はNoneを返して終了
        if not hasattr(self, "record") or self.record is None:
            return None

        r = self.record
        mylist_cols = Mylist.__table__.c.keys()

        # マイリスト情報をすべて含んでいない場合はNoneを返して終了
        for c in mylist_cols:
            if c not in r:
                return None

        # 設定
        id_index = r["id"]
        username = r["username"]
        mylistname = r["mylistname"]
        typename = r["type"]
        showname = r["showname"]
        url = r["url"]
        created_at = r["created_at"]
        updated_at = r["updated_at"]
        checked_at = r["checked_at"]
        check_failed_count = r["check_failed_count"]
        is_include_new = "True" if r["is_include_new"] else "False"

        # インターバル文字列をパース
        unit_list = ["分", "時間", "日", "週間", "ヶ月"]
        check_interval = r["check_interval"]
        check_interval_num = -1
        check_interval_unit = ""
        t = str(check_interval)
        for u in unit_list:
            t = t.replace(u, "")

        try:
            check_interval_num = int(t)
            check_interval_unit = str(check_interval).replace(str(t), "")
        except ValueError:
            return None  # キャスト失敗エラー

        if check_interval_num < 0:
            return None  # 負の数ならエラー([1-59]の範囲想定)

        if check_interval_unit not in unit_list:
            return None  # 想定外の単位ならエラー

        # 返り値取得用コンポーネントメンバ
        self.component = {}
        # レイアウト
        layout = QVBoxLayout()

        def hbox_helper(key: str, value: str) -> QHBoxLayout:
            hbox = QHBoxLayout()
            label = QLabel(str(key))
            label.setMinimumWidth(csize)
            tbox = QLineEdit(str(value), readOnly=True)
            hbox.addWidget(label)
            hbox.addWidget(tbox)
            self.component[key] = tbox
            return hbox

        label1 = QLabel(horizontal_line)
        hbox2 = hbox_helper("ID", id_index)
        hbox3 = hbox_helper("ユーザー名", username)
        hbox4 = hbox_helper("マイリスト名", mylistname)
        hbox5 = hbox_helper("種別", typename)
        hbox6 = hbox_helper("表示名", showname)
        hbox7 = hbox_helper("URL", url)
        hbox8 = hbox_helper("作成日時", created_at)
        hbox9 = hbox_helper("更新日時", updated_at)
        hbox10 = hbox_helper("更新確認日時", checked_at)

        hbox11 = QHBoxLayout()
        label11 = QLabel("更新確認インターバル")
        label11.setMinimumWidth(csize)
        combobox111 = QComboBox()
        combobox111.addItems([str(i) for i in range(1, 60)])
        combobox111.setCurrentText(str(check_interval_num))
        combobox111.setStyleSheet("QComboBox {background-color: olive;}")
        combobox112 = QComboBox()
        combobox112.addItems(unit_list)
        combobox112.setCurrentText(check_interval_unit)
        combobox112.setStyleSheet("QComboBox {background-color: olive;}")
        hbox11.addWidget(label11)
        hbox11.addWidget(combobox111)
        hbox11.addWidget(combobox112)
        hbox11.addStretch(1)
        self.component["更新確認インターバル"] = {
            "num": combobox111,
            "unit": combobox112,
        }

        hbox12 = QHBoxLayout()
        label12 = QLabel("更新確認失敗カウント")
        label12.setMinimumWidth(csize)
        tbox12 = QLineEdit(str(check_failed_count))
        tbox12.setStyleSheet("QLineEdit {background-color: olive;}")
        button12 = QPushButton("リセット")
        button12.clicked.connect(lambda: tbox12.setText("0"))
        hbox12.addWidget(label12)
        hbox12.addWidget(tbox12)
        hbox12.addWidget(button12)
        self.component["更新確認失敗カウント"] = tbox12

        hbox13 = hbox_helper("未視聴フラグ", is_include_new)
        label14 = QLabel(horizontal_line)
        label15 = QLabel(" ")

        hbox16 = QHBoxLayout()
        button161 = QPushButton("保存して閉じる")
        button161.clicked.connect(lambda: self.update_mylist_info())
        button162 = QPushButton("保存しないで閉じる")
        button162.clicked.connect(lambda: self.popup_window.close())
        hbox16.addStretch(0)
        hbox16.addWidget(button161)
        hbox16.addWidget(button162)

        layout.addWidget(label1)
        layout.addLayout(hbox2)
        layout.addLayout(hbox3)
        layout.addLayout(hbox4)
        layout.addLayout(hbox5)
        layout.addLayout(hbox6)
        layout.addLayout(hbox7)
        layout.addLayout(hbox8)
        layout.addLayout(hbox9)
        layout.addLayout(hbox10)
        layout.addLayout(hbox11)
        layout.addLayout(hbox12)
        layout.addLayout(hbox13)
        layout.addWidget(label14)
        layout.addWidget(label15)
        layout.addLayout(hbox16)
        return layout

    def update_mylist_info(self) -> Result:
        if not hasattr(self, "component"):
            return Result.failed
        component: dict[str, QPushButton] | dict[str, dict[str, QComboBox]] = self.component

        # キーチェック
        COMPONENT_KEYS = [
            "ID",
            "ユーザー名",
            "マイリスト名",
            "種別",
            "表示名",
            "URL",
            "作成日時",
            "更新日時",
            "更新確認日時",
            "更新確認インターバル",
            "更新確認失敗カウント",
            "未視聴フラグ",
        ]
        if list(component.keys()) != COMPONENT_KEYS:
            return Result.failed

        # 値の設定
        id_index = component["ID"].text()
        username = component["ユーザー名"].text()
        mylistname = component["マイリスト名"].text()
        typename = component["種別"].text()
        showname = component["表示名"].text()
        url = component["URL"].text()
        created_at = component["作成日時"].text()
        updated_at = component["更新日時"].text()
        checked_at = component["更新確認日時"].text()
        check_failed_count = component["更新確認失敗カウント"].text()
        is_include_new = str(component["未視聴フラグ"].text()) == "True"

        # インターバル文字列を結合して解釈できるかどうか確認する
        check_interval_num = component["更新確認インターバル"]["num"].currentText()
        check_interval_unit = component["更新確認インターバル"]["unit"].currentText()
        check_interval = str(check_interval_num) + check_interval_unit
        interval_str = check_interval
        dt = interval_translate(interval_str) - 1
        if dt < -1:
            # インターバル文字列解釈エラー
            logger.error(f"update interval setting is invalid : {interval_str}")
            return Result.failed

        # マイリスト情報更新
        self.mylist_db.upsert(
            id_index,
            username,
            mylistname,
            typename,
            showname,
            url,
            created_at,
            updated_at,
            checked_at,
            check_interval,
            check_failed_count,
            is_include_new,
        )
        logger.info("マイリスト情報更新完了")

        self.popup_window.close()
        return Result.success


class PopupVideoWindow(PopupWindowBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def init(self) -> Result:
        """初期化

        Returns:
            Result: 成功時success, エラー時failed
        """
        # テーブルの行が選択されていなかったら何もしない
        selected_table_row_index_list = self.get_selected_table_row_index_list()
        if not selected_table_row_index_list:
            logger.info("Table row is not selected.")
            return Result.failed

        # 選択されたテーブル行
        selected_table_row = self.get_selected_table_row_list()[0]

        # 動画情報を取得する
        video_id = selected_table_row.video_id.id
        mylist_url = selected_table_row.mylist_url.non_query_url
        records = self.mylist_info_db.select_from_id_url(video_id, mylist_url)

        if records == [] or len(records) != 1:
            logger.error("Selected row is invalid.")
            return Result.failed

        self.record = records[0]
        self.url = records[0]["video_url"]

        # 子ウィンドウの初期値
        self.title = "動画情報"
        return Result.success

    def create_window_layout(self) -> QVBoxLayout | None:
        """画面のレイアウトを作成する

        Notes:
            先にInitを実行し、self.recordを設定しておく必要がある
        """
        horizontal_line = "-" * 100
        csize = 100

        # self.recordが設定されていない場合はNoneを返して終了
        if not hasattr(self, "record") or self.record is None:
            return None

        r = self.record
        table_cols_name = [
            "No.",
            "動画ID",
            "動画名",
            "投稿者",
            "状況",
            "投稿日時",
            "登録日時",
            "動画URL",
            "所属マイリストURL",
        ]
        mylist_info_cols = MylistInfo.__table__.c.keys()

        # 動画情報をすべて含んでいない場合はNoneを返して終了
        for c in mylist_info_cols:
            if c not in r:
                return None

        # 設定
        id_index = r["id"]
        video_id = r["video_id"]
        title = r["title"]
        username = r["username"]
        status = r["status"]
        uploaded_at = r["uploaded_at"]
        registered_at = r["registered_at"]
        video_url = r["video_url"]
        mylist_url = r["mylist_url"]
        created_at = r["created_at"]

        layout = QVBoxLayout()

        def hbox_helper(key: str, value: str) -> QHBoxLayout:
            hbox = QHBoxLayout()
            label = QLabel(str(key))
            label.setMinimumWidth(csize)
            tbox = QLineEdit(str(value), readOnly=True)
            hbox.addWidget(label)
            hbox.addWidget(tbox)
            return hbox

        label1 = QLabel(horizontal_line)
        hbox2 = hbox_helper("ID", id_index)
        hbox3 = hbox_helper("動画ID", video_id)
        hbox4 = hbox_helper("動画名", title)
        hbox5 = hbox_helper("投稿者", username)
        hbox6 = hbox_helper("状況", status)
        hbox7 = hbox_helper("投稿日時", uploaded_at)
        hbox8 = hbox_helper("登録日時", registered_at)
        hbox9 = hbox_helper("動画URL", video_url)
        hbox10 = hbox_helper("所属マイリストURL", mylist_url)
        hbox11 = hbox_helper("作成日時", created_at)
        label12 = QLabel(horizontal_line)
        label13 = QLabel(" ")
        button14 = QPushButton("閉じる")
        button14.clicked.connect(lambda: self.popup_window.close())

        layout.addWidget(label1)
        layout.addLayout(hbox2)
        layout.addLayout(hbox3)
        layout.addLayout(hbox4)
        layout.addLayout(hbox5)
        layout.addLayout(hbox6)
        layout.addLayout(hbox7)
        layout.addLayout(hbox8)
        layout.addLayout(hbox9)
        layout.addLayout(hbox10)
        layout.addLayout(hbox11)
        layout.addWidget(label12)
        layout.addWidget(label13)
        layout.addWidget(button14, alignment=Qt.AlignmentFlag.AlignRight)
        return layout


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
