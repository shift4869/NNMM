import asyncio
import logging.config
import sys
import traceback
from logging import INFO, getLogger
from pathlib import Path

import qdarktheme
from PySide6.QtCore import QDateTime, QDir, QLibraryInfo, QSysInfo, Qt, QTimer, Slot, qVersion
from PySide6.QtGui import QCursor, QDesktopServices, QGuiApplication, QIcon, QKeySequence, QPalette, QShortcut
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QCommandLinkButton, QDateTimeEdit, QDial, QDialog
from PySide6.QtWidgets import QDialogButtonBox, QFileSystemModel, QGridLayout, QGroupBox, QHBoxLayout, QLabel
from PySide6.QtWidgets import QLayoutItem, QLineEdit, QListView, QListWidget, QMenu, QPlainTextEdit, QProgressBar
from PySide6.QtWidgets import QPushButton, QRadioButton, QScrollBar, QSizePolicy, QSlider, QSpinBox, QStyleFactory
from PySide6.QtWidgets import QTableWidget, QTabWidget, QTextBrowser, QTextEdit, QToolBox, QToolButton, QTreeView
from PySide6.QtWidgets import QVBoxLayout, QWidget

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process import base, config, copy_mylist_url, copy_video_url, create_mylist, delete_mylist, move_down
from nnmm.process import move_up, not_watched, popup, search, show_mylist_info, show_mylist_info_all, timer
from nnmm.process import video_play, video_play_with_focus_back, watched, watched_all_mylist, watched_mylist
from nnmm.process.update_mylist import every, partial, single
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import CustomLogger, Result

APP_NAME = "NNMM"
ICON_PATH = "./image/icon.png"

# ログ設定
logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
for name in logging.root.manager.loggerDict:
    if "nnmm" not in name:
        getLogger(name).disabled = True
logging.setLoggerClass(CustomLogger)
logger = getLogger(__name__)
logger.setLevel(INFO)


class MainWindow(QDialog):
    """メインウィンドウクラス"""

    def __init__(self) -> None:
        """メインウィンドウクラスのコンストラクタ"""
        super().__init__()
        # 設定値初期化
        self.config = config.ConfigBase.set_config()

        # DB操作コンポーネント設定
        self.db_fullpath = Path(self.config["db"].get("save_path", ""))
        self.mylist_db = MylistDBController(db_fullpath=str(self.db_fullpath))
        self.mylist_info_db = MylistInfoDBController(db_fullpath=str(self.db_fullpath))

        # アイコン画像取得
        if Path(ICON_PATH).exists():
            self.setWindowIcon(QIcon(ICON_PATH))

        # ウィンドウタイトル設定
        qv = qVersion()
        self.setWindowTitle(f"{APP_NAME} by pyside {qv}")

        # ウィンドウオブジェクト作成
        # self.window = sg.Window("NNMM", layout, icon=icon_binary, size=(1330, 900), finalize=True, resizable=True)
        # self.window["-LIST-"].bind("<Double-Button-1>", "+DOUBLE CLICK+")
        # ウィンドウレイアウト作成
        layout = self.create_layout()
        self.setLayout(layout)

        # Windows特有のruntimeError抑止
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        # マイリスト一覧初期化
        # DBからマイリスト一覧を取得する
        self.update_mylist_pane()

        return

        # テーブル初期化
        def_data = [[]]
        self.window["-TABLE-"].update(values=def_data)

        # タイマーセットイベントを起動
        self.window.write_event_value("-TIMER_SET-", "-FIRST_SET-")

        # イベントと処理の辞書
        self.dict = {
            "ブラウザで開く::-TR-": video_play.VideoPlay,
            "ブラウザで開く（フォーカスを戻す）::-TR-": video_play_with_focus_back.VideoPlayWithFocusBack,
            "動画URLをクリップボードにコピー::-TR-": copy_video_url.CopyVideoUrl,
            "視聴済にする::-TR-": watched.Watched,
            "未視聴にする::-TR-": not_watched.NotWatched,
            "検索（動画名）::-TR-": search.VideoSearch,
            "強調表示を解除::-TR-": search.VideoSearchClear,
            "情報表示::-TR-": popup.PopupVideoWindow,
            "全動画表示::-MR-": show_mylist_info_all.ShowMylistInfoAll,
            "マイリストURLをクリップボードにコピー::-MR-": copy_mylist_url.CopyMylistUrl,
            "視聴済にする（選択）::-MR-": watched_mylist.WatchedMylist,
            "視聴済にする（全て）::-MR-": watched_all_mylist.WatchedAllMylist,
            "上に移動::-MR-": move_up.MoveUp,
            "下に移動::-MR-": move_down.MoveDown,
            "マイリスト追加::-MR-": create_mylist.CreateMylist,
            "マイリスト削除::-MR-": delete_mylist.DeleteMylist,
            "検索（マイリスト名）::-MR-": search.MylistSearch,
            "検索（動画名）::-MR-": search.MylistSearchFromVideo,
            "検索（URL）::-MR-": search.MylistSearchFromMylistURL,
            "強調表示を解除::-MR-": search.MylistSearchClear,
            "情報表示::-MR-": popup.PopupMylistWindow,
            "-LIST-+DOUBLE CLICK+": show_mylist_info.ShowMylistInfo,
            "-CREATE-": create_mylist.CreateMylist,
            "-CREATE_THREAD_DONE-": create_mylist.CreateMylistThreadDone,
            "-DELETE-": delete_mylist.DeleteMylist,
            "-UPDATE-": single.Single,
            "-UPDATE_THREAD_DONE-": single.SingleThreadDone,
            "-ALL_UPDATE-": every.Every,
            "-ALL_UPDATE_THREAD_DONE-": every.EveryThreadDone,
            "-PARTIAL_UPDATE-": partial.Partial,
            "-PARTIAL_UPDATE_THREAD_DONE-": partial.PartialThreadDone,
            "-C_CONFIG_SAVE-": config.ConfigSave,
            "-C_MYLIST_SAVE-": config.MylistSaveCSV,
            "-C_MYLIST_LOAD-": config.MylistLoadCSV,
            "-TIMER_SET-": timer.Timer,
        }

        logger.info("window setup done.")

    def create_layout(self) -> QVBoxLayout:
        """画面のレイアウトを作成する

        Returns:
            QVBoxLayout | None: 成功時レイアウトオブジェクト、失敗時None
        """
        WINDOW_WIDTH = 1200  # 1330
        WINDOW_HEIGHT = 850  # 900
        # 全体レイアウト
        layout = QVBoxLayout()
        # タブバー
        tabs = QTabWidget()

        # マイリストタブ
        tab1 = self.create_mylist_tab_layout(WINDOW_WIDTH, WINDOW_HEIGHT)

        # 設定タブ
        tab2 = self.create_config_tab_layout(WINDOW_WIDTH, WINDOW_HEIGHT)

        # ログ出力用テキストエリア
        tab3 = QLabel("タブ3の内容")
        self.textarea = QTextEdit()
        self.textarea.setMinimumHeight(300)

        # タブにウィジェットを追加
        tabs.addTab(tab1, "マイリスト")
        tabs.addTab(tab2, "設定")
        tabs.addTab(self.textarea, "ログ")

        layout.addWidget(tabs)
        return layout

        # 左ペイン
        listbox_right_click_menu = [
            "-LISTBOX_RIGHT_CLICK_MENU-",
            [
                "! ",
                "---",
                "全動画表示::-MR-",
                "マイリストURLをクリップボードにコピー::-MR-",
                "---",
                "視聴済にする（選択）::-MR-",
                "視聴済にする（全て）::-MR-",
                "---",
                "上に移動::-MR-",
                "下に移動::-MR-",
                "---",
                "マイリスト追加::-MR-",
                "マイリスト削除::-MR-",
                "---",
                "検索（マイリスト名）::-MR-",
                "検索（動画名）::-MR-",
                "検索（URL）::-MR-",
                "強調表示を解除::-MR-",
                "---",
                "情報表示::-MR-",
            ],
        ]
        l_pane = [
            [
                sg.Listbox(
                    [],
                    key="-LIST-",
                    enable_events=False,
                    size=(40, 44),
                    auto_size_text=True,
                    right_click_menu=listbox_right_click_menu,
                )
            ],
            [sg.Button(" インターバル更新 ", key="-PARTIAL_UPDATE-"), sg.Button(" すべて更新 ", key="-ALL_UPDATE-")],
            [
                sg.Button("  +  ", key="-CREATE-"),
                sg.Button("  -  ", key="-DELETE-"),
                sg.Input("", key="-INPUT2-", size=(24, 10)),
            ],
        ]

        # 右ペイン
        table_cols_name = [
            "No.",
            "   動画ID   ",
            "                動画名                ",
            "   投稿者   ",
            "  状況  ",
            "     投稿日時      ",
            "     登録日時      ",
            "動画URL",
            "所属マイリストURL",
        ]
        cols_width = [20, 20, 20, 20, 80, 100, 100, 0, 0]
        def_data = [["", "", "", "", "", "", "", "", ""]]
        table_right_click_menu = [
            "-TABLE_RIGHT_CLICK_MENU-",
            [
                "! ",
                "---",
                "ブラウザで開く::-TR-",
                "ブラウザで開く（フォーカスを戻す）::-TR-",
                "動画URLをクリップボードにコピー::-TR-",
                "---",
                "視聴済にする::-TR-",
                "未視聴にする::-TR-",
                "---",
                "検索（動画名）::-TR-",
                "強調表示を解除::-TR-",
                "---",
                "情報表示::-TR-",
                "---",
                "!動画ダウンロード::-TR-",
            ],
        ]
        table_style = {
            "values": def_data,
            "headings": table_cols_name,
            "max_col_width": 600,
            "def_col_width": cols_width,
            "num_rows": 2400,
            "auto_size_columns": True,
            "bind_return_key": True,
            "justification": "left",
            "key": "-TABLE-",
            "right_click_menu": table_right_click_menu,
        }
        t = sg.Table(**table_style)
        r_pane = [
            [
                sg.Input("", key="-INPUT1-", size=(120, 100)),
                sg.Button("更新", key="-UPDATE-"),
                sg.Button("終了", key="-EXIT-"),
            ],
            [sg.Column([[t]], expand_x=True)],
        ]

        # ウィンドウのレイアウト
        mf_layout = [
            [
                sg.Frame(
                    "Main",
                    [
                        [
                            sg.Column(l_pane, expand_x=True),
                            sg.Column(r_pane, expand_x=True, element_justification="right"),
                        ]
                    ],
                    size=(1370, 1000),
                )
            ]
        ]
        cf_layout = config.ConfigBase.make_layout()
        lf_layout = [
            [
                sg.Frame(
                    "ログ",
                    [
                        [
                            sg.Column([
                                [
                                    sg.Multiline(
                                        size=(1080, 100),
                                        auto_refresh=True,
                                        autoscroll=True,
                                        reroute_stdout=True,
                                        reroute_stderr=True,
                                    )
                                ]
                            ])
                        ]
                    ],
                    size=(1370, 1000),
                )
            ]
        ]
        layout = [
            [
                sg.TabGroup(
                    [[sg.Tab("マイリスト", mf_layout), sg.Tab("設定", cf_layout), sg.Tab("ログ", lf_layout)]],
                    key="-TAB_CHANGED-",
                    enable_events=True,
                )
            ]
        ]

        return layout

    def create_mylist_tab_layout(self, window_w: int, window_h: int) -> QGroupBox:
        group = QGroupBox("マイリスト")

        leftpane = QVBoxLayout()
        update_button = QHBoxLayout()
        all_update_button = QPushButton("すべて更新")
        partial_update_button = QPushButton("インターバル更新")
        single_update_button = QPushButton("更新")
        update_button.addWidget(all_update_button)
        update_button.addWidget(partial_update_button)
        update_button.addWidget(single_update_button)
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(window_w * 1 / 3)
        self.list_widget.setMinimumHeight(window_h)
        self.list_widget.setStyleSheet("QListWidget {background-color: #121213;}")
        mylist_control_button = QHBoxLayout()
        add_mylist_button = QPushButton("マイリスト追加")
        del_mylist_button = QPushButton("マイリスト削除")
        mylist_control_button.addWidget(add_mylist_button)
        mylist_control_button.addWidget(del_mylist_button)
        self.oneline_log = QLineEdit()
        leftpane.addLayout(update_button)
        leftpane.addWidget(self.list_widget)
        leftpane.addLayout(mylist_control_button)
        leftpane.addWidget(self.oneline_log)

        rightpane = QVBoxLayout()
        self.tbox_mylist_url = QLineEdit()
        self.table_widget = QTableWidget()
        self.table_widget.setMinimumWidth(window_w * 2 / 3)
        self.table_widget.setMinimumHeight(window_h)
        rightpane.addWidget(self.tbox_mylist_url)
        rightpane.addWidget(self.table_widget)

        pane = QGridLayout(group)
        pane.addLayout(leftpane, 0, 0)
        pane.addLayout(rightpane, 0, 1)
        return group

    def create_config_tab_layout(self, window_w: int, window_h: int) -> QGroupBox:
        group = QGroupBox("設定")
        group.setMinimumWidth(window_w / 4)
        group.setMaximumWidth(window_w / 2)
        group.setMinimumHeight(window_h / 2)
        group.setMaximumHeight(window_h * 2 / 3)
        vbox = QVBoxLayout(group)

        c_group1 = QGroupBox("ブラウザパス")
        vbox1 = QVBoxLayout(c_group1)
        label1 = QLabel("「ブラウザで再生」時に使用するブラウザパス")
        hbox1 = QHBoxLayout()
        self.tbox_browser_path = QLineEdit()
        button1 = QPushButton("参照")
        hbox1.addWidget(self.tbox_browser_path)
        hbox1.addWidget(button1)
        vbox1.addWidget(label1)
        vbox1.addLayout(hbox1)

        c_group2 = QGroupBox("オートリロード")
        vbox2 = QVBoxLayout(c_group2)
        label2 = QLabel("オートリロードする間隔")
        self.cbox = QComboBox()
        combo_box_text = ("(使用しない)", "15分毎", "30分毎", "60分毎")
        self.cbox.addItems(combo_box_text)
        vbox2.addWidget(label2)
        vbox2.addWidget(self.cbox)

        c_group3 = QGroupBox("RSS")
        vbox3 = QVBoxLayout(c_group3)
        label3 = QLabel("RSS保存先パス")
        hbox3 = QHBoxLayout()
        self.tbox_rss_save_path = QLineEdit()
        button3 = QPushButton("参照")
        hbox3.addWidget(self.tbox_rss_save_path)
        hbox3.addWidget(button3)
        vbox3.addWidget(label3)
        vbox3.addLayout(hbox3)

        c_group4 = QGroupBox("マイリスト一覧")
        vbox4 = QVBoxLayout(c_group4)
        label41 = QLabel("マイリスト一覧保存")
        button41 = QPushButton("保存")
        label42 = QLabel("マイリスト一覧読込")
        button42 = QPushButton("読込")
        vbox4.addWidget(label41)
        vbox4.addWidget(button41, alignment=Qt.AlignmentFlag.AlignLeft)
        vbox4.addWidget(label42)
        vbox4.addWidget(button42, alignment=Qt.AlignmentFlag.AlignLeft)

        c_group5 = QGroupBox("情報保存DB")
        vbox5 = QVBoxLayout(c_group5)
        label5 = QLabel("マイリスト・動画情報保存DBのパス")
        hbox5 = QHBoxLayout()
        self.tbox_db_path = QLineEdit()
        button5 = QPushButton("参照")
        hbox5.addWidget(self.tbox_db_path)
        hbox5.addWidget(button5)
        vbox5.addWidget(label5)
        vbox5.addLayout(hbox5)

        button5 = QPushButton("設定保存")

        vbox.addWidget(c_group1)
        vbox.addWidget(c_group2)
        vbox.addWidget(c_group3)
        vbox.addWidget(c_group4)
        vbox.addWidget(c_group5)
        vbox.addStretch(1)
        vbox.addWidget(button5, alignment=Qt.AlignmentFlag.AlignRight)

        return group

    def update_mylist_pane(self) -> Result:
        """マイリストペインの初期表示

        Returns:
            Result: 成功時success
        """
        if not hasattr(self, "list_widget"):
            return Result.failed

        index = 0

        # マイリスト画面表示更新
        NEW_MARK = "*:"
        m_list = self.mylist_db.select()
        include_new_index_list = []
        for i, m in enumerate(m_list):
            if m["is_include_new"]:
                m["showname"] = NEW_MARK + m["showname"]
                include_new_index_list.append(i)
        list_data = [m["showname"] for m in m_list]
        self.list_widget.addItems(list_data)
        # self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        # for i in include_new_index_list:
        #     self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # indexをセットしてスクロール
        # self.window["-LIST-"].Widget.see(index)
        # self.window["-LIST-"].update(set_to_index=index)
        return Result.success

    def run(self) -> Result:
        """メインイベントループ"""
        while True:
            # イベントの読み込み
            event, values = self.window.read()

            if event in [sg.WIN_CLOSED, "-EXIT-"]:
                # 終了ボタンかウィンドウの×ボタンが押されれば終了
                logger.info("window exit.")
                break

            # イベント処理
            if self.dict.get(event):
                self.values = values
                info = ProcessInfo.create(event, self)

                try:
                    pb: base.ProcessBase = self.dict.get(event)(info)

                    if pb is None or not hasattr(pb, "run"):
                        continue

                    pb.run()
                except Exception:
                    logger.error(traceback.format_exc())
                    logger.error("main event loop error.")

            # タブ切り替え
            if event == "-TAB_CHANGED-":
                select_tab = values["-TAB_CHANGED-"]
                if select_tab == "設定":
                    # 設定タブを開いたときの処理
                    self.values = values
                    info = ProcessInfo.create(event, self)
                    pb = config.ConfigLoad(info)
                    pb.run()

        # ウィンドウ終了処理
        self.window.close()
        return Result.success


if __name__ == "__main__":
    app = QApplication()
    qdarktheme.setup_theme()
    window_main = MainWindow()
    window_main.show()
    sys.exit(app.exec())
