from abc import abstractmethod
from logging import INFO, getLogger
from typing import TYPE_CHECKING

import PySimpleGUI as sg

from NNMM.gui_function import interval_translate
from NNMM.model import Mylist, MylistInfo
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo

if TYPE_CHECKING:
    from NNMM.main_window import MainWindow

logger = getLogger(__name__)
logger.setLevel(INFO)


class PopupWindowBase(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        """コンストラクタ

        Atributes:
            window (MainWindow|None): 子window
            title (str): windowタイトル
            size (tuple[str,str]): windowサイズ
            process_dict (dict): イベント処理の対応辞書
        """
        super().__init__(process_info)

        self.popup_window = None
        self.title = ""
        self.size = (100, 100)
        self.process_dict = {}

    @abstractmethod
    def init(self) -> int:
        """初期化

        Returns:
            int: 成功時0、エラー時-1
        """
        raise NotImplementedError

    @abstractmethod
    def make_window_layout(self) -> list[list[sg.Frame]] | None:
        """画面のレイアウトを作成する

        Returns:
            list[list[sg.Frame]] | None: 成功時PySimpleGUIのレイアウトオブジェクト、失敗時None
        """
        raise NotImplementedError

    def run(self) -> None:
        """子windowイベントループ
        """
        # 初期化
        res = self.init()
        if res == -1:
            sg.popup_ok("情報ウィンドウの初期化に失敗しました。")
            return

        # ウィンドウレイアウト作成
        layout = self.make_window_layout()
        if not layout:
            sg.popup_ok("情報ウィンドウのレイアウト表示に失敗しました。")
            return

        # ウィンドウオブジェクト作成
        self.popup_window = sg.Window(self.title, layout, size=self.size, finalize=True, resizable=True, modal=True)

        # イベントのループ
        while True:
            # イベントの読み込み
            event, values = self.popup_window.read()

            if event in [sg.WIN_CLOSED, "-EXIT-"]:
                # 終了ボタンかウィンドウの×ボタンが押されれば終了
                logger.info(self.title + " window exit.")
                break

            # イベント処理
            if self.process_dict.get(event):
                self.values = values
                process_info = ProcessInfo.create(event, self)
                process_info.window = self.popup_window
                pb: ProcessBase = self.process_dict.get(event)(process_info)
                pb.run()

        # ウィンドウ終了処理
        self.popup_window.close()
        return


class PopupMylistWindow(PopupWindowBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def init(self) -> int:
        """初期化

        Returns:
            int: 成功時0、エラー時-1
        """
        # 親windowからの情報を取得する
        values = self.values.get("-LIST-")

        # 選択されたマイリストのShownameを取得する
        if values and len(values) > 0:
            values = values[0]
        else:
            logger.error("Mylist popup window Init failed, mylist is not selected.")
            return -1

        # 新着表示のマークがある場合は削除する
        NEW_MARK = "*:"
        if values[:2] == NEW_MARK:
            values = values[2:]

        # 選択されたマイリストのマイリストレコードオブジェクトを取得する
        record = self.mylist_db.select_from_showname(values)
        if record and len(record) == 1:
            record = record[0]
        else:
            logger.error("Mylist popup window Init failed, mylist is not found in mylist_db.")
            return -1

        # recordを設定(make_window_layoutで使用する)
        self.record = record

        # 子ウィンドウの初期値設定
        self.title = "マイリスト情報"
        self.size = (580, 450)
        self.process_dict = {
            "-SAVE-": PopupMylistWindowSave,
        }
        return 0

    def make_window_layout(self) -> list[list[sg.Frame]] | None:
        """画面のレイアウトを作成する

        Notes:
            先にInitを実行し、self.recordを設定しておく必要がある

        Returns:
            list[list[sg.Frame]] | None: 成功時PySimpleGUIのレイアウトオブジェクト、失敗時None
        """
        horizontal_line = "-" * 132
        csize = (20, 1)
        tsize = (50, 1)
        thsize = (5, 1)

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

        cf = [
            [sg.Text(horizontal_line)],
            [sg.Text("ID", size=csize, visible=False), sg.Input(f"{id_index}", key="-ID_INDEX-", visible=False, readonly=True, size=tsize)],
            [sg.Text("ユーザー名", size=csize), sg.Input(f"{username}", key="-USERNAME-", readonly=True, size=tsize)],
            [sg.Text("マイリスト名", size=csize), sg.Input(f"{mylistname}", key="-MYLISTNAME-", readonly=True, size=tsize)],
            [sg.Text("種別", size=csize), sg.Input(f"{typename}", key="-TYPE-", readonly=True, size=tsize)],
            [sg.Text("表示名", size=csize), sg.Input(f"{showname}", key="-SHOWNAME-", readonly=True, size=tsize)],
            [sg.Text("URL", size=csize), sg.Input(f"{url}", key="-URL-", readonly=True, size=tsize)],
            [sg.Text("作成日時", size=csize), sg.Input(f"{created_at}", key="-CREATED_AT-", readonly=True, size=tsize)],
            [sg.Text("更新日時", size=csize), sg.Input(f"{updated_at}", key="-UPDATED_AT-", readonly=True, size=tsize)],
            [sg.Text("更新確認日時", size=csize), sg.Input(f"{checked_at}", key="-CHECKED_AT-", readonly=True, size=tsize)],
            [sg.Text("更新確認インターバル", size=csize),
                sg.InputCombo([i for i in range(1, 60)], default_value=check_interval_num, key="-CHECK_INTERVAL_NUM-", background_color="light goldenrod", size=thsize),
                sg.InputCombo(unit_list, default_value=check_interval_unit, key="-CHECK_INTERVAL_UNIT-", background_color="light goldenrod", size=thsize)],
            [sg.Text("未視聴フラグ", size=csize), sg.Input(f"{is_include_new}", key="-IS_INCLUDE_NEW-", readonly=True, size=tsize)],
            [sg.Text(horizontal_line)],
            [sg.Text("")],
            [sg.Text("")],
            [sg.Column([[sg.Button("保存", key="-SAVE-"), sg.Button("閉じる", key="-EXIT-")]], justification="right")],
        ]
        layout = [[
            sg.Frame(self.title, cf)
        ]]
        return layout



class PopupMylistWindowSave(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> None:
        """ポップアップwindow上の変更を保存する

        Notes:
            "-SAVE-"
            マイリスト情報windowの保存ボタンが押された時呼び出される

        Returns:
            int: 正常終了時0、エラー時-1
        """
        self.popup_window: sg.Window = self.window

        # キーチェック
        PMW_ROWS = ["-ID_INDEX-", "-USERNAME-", "-MYLISTNAME-", "-TYPE-", "-SHOWNAME-", "-URL-",
                    "-CREATED_AT-", "-UPDATED_AT-", "-CHECKED_AT-", "-IS_INCLUDE_NEW-", "-CHECK_INTERVAL_NUM-", "-CHECK_INTERVAL_UNIT-"]
        allkeys = list(self.popup_window.AllKeysDict.keys())
        for k in PMW_ROWS:
            if k not in allkeys:
                logger.error("Mylist popup window layout key error.")
                return

        # 値の設定
        id_index = self.popup_window["-ID_INDEX-"].get()
        username = self.popup_window["-USERNAME-"].get()
        mylistname = self.popup_window["-MYLISTNAME-"].get()
        typename = self.popup_window["-TYPE-"].get()
        showname = self.popup_window["-SHOWNAME-"].get()
        url = self.popup_window["-URL-"].get()
        created_at = self.popup_window["-CREATED_AT-"].get()
        updated_at = self.popup_window["-UPDATED_AT-"].get()
        checked_at = self.popup_window["-CHECKED_AT-"].get()
        is_include_new = str(self.popup_window["-IS_INCLUDE_NEW-"].get()) == "True"

        # インターバル文字列を結合して解釈できるかどうか確認する
        check_interval_num = self.popup_window["-CHECK_INTERVAL_NUM-"].get()
        check_interval_unit = self.popup_window["-CHECK_INTERVAL_UNIT-"].get()
        check_interval = str(check_interval_num) + check_interval_unit
        interval_str = check_interval
        dt = interval_translate(interval_str) - 1
        if dt < -1:
            # インターバル文字列解釈エラー
            logger.error(f"update interval setting is invalid : {interval_str}")
            return

        # マイリスト情報更新
        self.mylist_db.upsert(id_index, username, mylistname, typename, showname, url, created_at, updated_at, checked_at, check_interval, is_include_new)
        logger.info("マイリスト情報Saved")
        return


class PopupVideoWindow(PopupWindowBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def init(self) -> int:
        """初期化

        Returns:
            int: 成功時0、エラー時-1
        """
        # 親windowからの情報を取得する
        window = self.window
        values = self.values

        # 引数設定チェック
        if window is None or values is None:
            logger.error("MylistInfo popup window Init failed, argument error.")
            return -1

        # テーブルの行が選択されていなかったら何もしない
        if not values["-TABLE-"]:
            logger.info("Table row is not selected.")
            return -1

        # 選択されたテーブル行番号
        row = int(values["-TABLE-"][0])
        # 現在のテーブルの全リスト
        def_data = window["-TABLE-"].Values
        # 選択されたテーブル行
        selected = def_data[row]

        # 動画情報を取得する
        video_id = selected[1]
        mylist_url = selected[8]
        records = self.mylist_info_db.select_from_id_url(video_id, mylist_url)

        if records == [] or len(records) != 1:
            logger.error("Selected row is invalid.")
            return -1

        self.record = records[0]

        # 子ウィンドウの初期値
        self.title = "動画情報"
        self.size = (580, 400)
        return 0

    def make_window_layout(self) -> list[list[sg.Frame]]:
        """画面のレイアウトを作成する

        Notes:
            先にInitを実行し、self.recordを設定しておく必要がある

        Returns:
            list[list[sg.Frame]] | None: 成功時PySimpleGUIのレイアウトオブジェクト、失敗時None
        """
        horizontal_line = "-" * 132
        csize = (20, 1)
        tsize = (50, 1)

        # self.recordが設定されていない場合はNoneを返して終了
        if not hasattr(self, "record") or self.record is None:
            return None

        r = self.record
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
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

        cf = [
            [sg.Text(horizontal_line)],
            [sg.Text("ID", size=csize, visible=False), sg.Input(f"{id_index}", key="-ID_INDEX-", visible=False, readonly=True, size=tsize)],
            [sg.Text("動画ID", size=csize), sg.Input(f"{video_id}", key="-USERNAME-", readonly=True, size=tsize)],
            [sg.Text("動画名", size=csize), sg.Input(f"{title}", key="-MYLISTNAME-", readonly=True, size=tsize)],
            [sg.Text("投稿者", size=csize), sg.Input(f"{username}", key="-TYPE-", readonly=True, size=tsize)],
            [sg.Text("状況", size=csize), sg.Input(f"{status}", key="-SHOWNAME-", readonly=True, size=tsize)],
            [sg.Text("投稿日時", size=csize), sg.Input(f"{uploaded_at}", key="-URL-", readonly=True, size=tsize)],
            [sg.Text("登録日時", size=csize), sg.Input(f"{registered_at}", key="-URL-", readonly=True, size=tsize)],
            [sg.Text("動画URL", size=csize), sg.Input(f"{video_url}", key="-CREATED_AT-", readonly=True, size=tsize)],
            [sg.Text("マイリストURL", size=csize), sg.Input(f"{mylist_url}", key="-UPDATED_AT-", readonly=True, size=tsize)],
            [sg.Text("作成日時", size=csize), sg.Input(f"{created_at}", key="-CHECKED_AT-", readonly=True, size=tsize)],
            [sg.Text(horizontal_line)],
            [sg.Text("")],
            [sg.Column([[sg.Button("閉じる", key="-EXIT-")]], justification="right")],
        ]
        layout = [[
            sg.Frame(self.title, cf)
        ]]
        return layout


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
