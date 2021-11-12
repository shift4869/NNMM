# coding: utf-8
from abc import abstractmethod
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase

logger = getLogger("root")
logger.setLevel(INFO)


class PopupWindowBase(ProcessBase.ProcessBase):
    """情報ウィンドウのベースクラス

    派生クラスと外部から使用されるクラス変数とクラスメソッドを定義する
    このベースクラス自体は抽象クラスのためインスタンスは作成できない
    """
    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        """コンストラクタ

        Args:
            log_sflag (bool): 開始時ログ出力フラグ
            log_eflag (bool): 終了時時ログ出力フラグ
            process_name (str): 処理名

        Atributes:
            window (sg.Window|None): 子window
            title (str): windowタイトル
            size (tuple[str,str]): windowサイズ
            ep_dict (dict): イベント処理の対応辞書
        """
        # 派生クラスの生成時は引数ありで呼び出される
        if process_name:
            super().__init__(log_sflag, log_eflag, process_name)
        else:
            super().__init__(True, True, "ウィンドウベース")

        self.window = None
        self.title = ""
        self.size = (100, 100)
        self.ep_dict = {}

    @abstractmethod
    def MakeWindowLayout(self, mw) -> list[list[sg.Frame]] | None:
        """画面のレイアウトを作成する

        Args:
            mw (sg.Window): 親windowの情報

        Returns:
            list[list[sg.Frame]] | None: 成功時PySimpleGUIのレイアウトオブジェクト、失敗時None
        """
        return None

    @abstractmethod
    def Init(self, mw) -> int:
        """初期化

        Args:
            mw (sg.Window): 親windowの情報

        Returns:
            int: 成功時0、エラー時-1
        """
        return -1

    def Run(self, mw) -> int:
        """子windowイベントループ

        Args:
            mw (sg.Window): 親windowの情報

        Returns:
            int: 正常終了時0、エラー時-1
        """
        # 初期化
        self.Init(mw)

        # ウィンドウレイアウト作成
        layout = self.MakeWindowLayout(mw)

        if not layout:
            return -1

        # ウィンドウオブジェクト作成
        self.window = sg.Window(self.title, layout, size=self.size, finalize=True, resizable=True, modal=True)

        # イベントのループ
        while True:
            # イベントの読み込み
            event, values = self.window.read()
            # print(event, values)

            if event in [sg.WIN_CLOSED, "-EXIT-"]:
                # 終了ボタンかウィンドウの×ボタンが押されれば終了
                logger.info(self.title + " window exit.")
                break

            # イベント処理
            if self.ep_dict.get(event):
                self.values = values
                pb = self.ep_dict.get(event)()

                if pb.log_sflag:
                    logger.info(f'"{pb.process_name}" starting.')

                pb.Run(self)

                if pb.log_eflag:
                    logger.info(f'"{pb.process_name}" finished.')

        # ウィンドウ終了処理
        self.window.close()
        return 0


class PopupMylistWindow(PopupWindowBase):
    
    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        if process_name:
            super().__init__(log_sflag, log_eflag, process_name)
        else:
            super().__init__(True, True, "マイリスト情報ウィンドウ")

    def MakeWindowLayout(self, mw) -> list[list[sg.Frame]] | None:
        """画面のレイアウトを作成する

        Notes:
            先にInitを実行し、self.recordを設定しておく必要がある

        Args:
            mw (sg.Window): 親windowの情報（使用しない）

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

    def Init(self, mw) -> int:
        """初期化

        Args:
            mw (sg.Window): 親windowの情報

        Returns:
            int: 成功時0、エラー時-1
        """
        # 親windowからの情報を取得する
        v = []
        try:
            # self.window = mw.window
            v = mw.values.get("-LIST-")
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("Mylist popup window Init failed, argument error.")
            return -1

        # 選択されたマイリストのShownameを取得する
        if v and len(v) > 0:
            v = v[0]
        else:
            logger.error("Mylist popup window Init failed, mylist is not selected.")
            return -1

        # 新着表示のマークがある場合は削除する
        NEW_MARK = "*:"
        if v[:2] == NEW_MARK:
            v = v[2:]

        # 選択されたマイリストのマイリストレコードオブジェクトを取得する
        record = self.mylist_db.SelectFromShowname(v)
        if record and len(record) == 1:
            record = record[0]
        else:
            logger.error("Mylist popup window Init failed, mylist is not found in mylist_db.")
            return -1

        # recordを設定(MakeWindowLayoutで使用する)
        self.record = record

        # 子ウィンドウの初期値設定
        self.title = "マイリスト情報"
        self.size = (580, 450)
        self.ep_dict = {
            "-SAVE-": PopupMylistWindowSave,
        }
        return 0


class PopupMylistWindowSave(ProcessBase.ProcessBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        # 派生クラスの生成時は引数ありで呼び出される
        if process_name:
            super().__init__(log_sflag, log_eflag, process_name)
        else:
            super().__init__(True, True, "マイリスト情報ウィンドウSave")
    
    def Run(self, mw):
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        id_index = self.window["-ID_INDEX-"].get()
        username = self.window["-USERNAME-"].get()
        mylistname = self.window["-MYLISTNAME-"].get()
        typename = self.window["-TYPE-"].get()
        showname = self.window["-SHOWNAME-"].get()
        url = self.window["-URL-"].get()
        created_at = self.window["-CREATED_AT-"].get()
        updated_at = self.window["-UPDATED_AT-"].get()
        checked_at = self.window["-CHECKED_AT-"].get()
        is_include_new = str(self.window["-IS_INCLUDE_NEW-"].get()) == "True"

        # インターバル文字列を結合して解釈できるかどうか確認する
        check_interval_num = self.window["-CHECK_INTERVAL_NUM-"].get()
        check_interval_unit = self.window["-CHECK_INTERVAL_UNIT-"].get()
        check_interval = str(check_interval_num) + check_interval_unit
        interval_str = check_interval
        dt = IntervalTranslation(interval_str) - 1
        if dt < -1:
            # インターバル文字列解釈エラー
            logger.error(f"update interval setting is invalid : {interval_str}")
            sg.popup_ok("インターバル文字列が不正です。")
            return -1

        self.mylist_db.Upsert(id_index, username, mylistname, typename, showname, url, created_at, updated_at, checked_at, check_interval, is_include_new)

        logger.info("マイリスト情報Saved")
        return 0


class PopupVideoWindow(PopupWindowBase):
    
    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        if process_name:
            super().__init__(log_sflag, log_eflag, process_name)
        else:
            super().__init__(True, True, "動画情報ウィンドウ")

    def MakeWindowLayout(self, mw):
        # 画面のレイアウトを作成する
        horizontal_line = "-" * 132
        csize = (20, 1)
        tsize = (50, 1)

        r = self.record
        id_index = r["id"]
        video_id = r["video_id"]
        title = r["title"]
        username = r["username"]
        status = r["status"]
        uploaded_at = r["uploaded_at"]
        video_url = r["video_url"]
        mylist_url = r["mylist_url"]
        created_at = r["created_at"]
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL"]

        cf = [
            [sg.Text(horizontal_line)],
            [sg.Text("ID", size=csize, visible=False), sg.Input(f"{id_index}", key="-ID_INDEX-", visible=False, readonly=True, size=tsize)],
            [sg.Text("動画ID", size=csize), sg.Input(f"{video_id}", key="-USERNAME-", readonly=True, size=tsize)],
            [sg.Text("動画名", size=csize), sg.Input(f"{title}", key="-MYLISTNAME-", readonly=True, size=tsize)],
            [sg.Text("投稿者", size=csize), sg.Input(f"{username}", key="-TYPE-", readonly=True, size=tsize)],
            [sg.Text("状況", size=csize), sg.Input(f"{status}", key="-SHOWNAME-", readonly=True, size=tsize)],
            [sg.Text("投稿日時", size=csize), sg.Input(f"{uploaded_at}", key="-URL-", readonly=True, size=tsize)],
            [sg.Text("動画URL", size=csize), sg.Input(f"{video_url}", key="-CREATED_AT-", readonly=True, size=tsize)],
            [sg.Text("マイリストURL", size=csize), sg.Input(f"{mylist_url}", key="-UPDATED_AT-", readonly=True, size=tsize)],
            [sg.Text("作成日時", size=csize), sg.Input(f"{created_at}", key="-CHECKED_AT-", readonly=True, size=tsize)],
            [sg.Text(horizontal_line)],
            [sg.Text("")],
            [sg.Text("")],
            [sg.Column([[sg.Button("閉じる", key="-EXIT-")]], justification="right")],
        ]
        layout = [[
            sg.Frame(self.title, cf)
        ]]
        return layout

    def Init(self, mw):
        # 初期化
        # 親ウィンドウからの情報を取得する
        window = mw.window
        values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # mylist_url = values["-INPUT1-"]

        # テーブルの行が選択されていなかったら何もしない
        if not values["-TABLE-"]:
            logger.info("Table row is none selected.")
            return

        # 選択されたテーブル行数
        row = int(values["-TABLE-"][0])
        # 現在のテーブルの全リスト
        def_data = window["-TABLE-"].Values
        # 選択されたテーブル行
        selected = def_data[row]

        # 動画情報を取得する
        records = self.mylist_info_db.SelectFromVideoID(selected[1])
        record = []
        mylist_url = selected[7]
        # 可能ならマイリストURLを照合する
        if mylist_url != "":
            record = [r for r in records if r["mylist_url"] == mylist_url]
        else:
            record = records[0:1]

        if record and len(record) == 1:
            record = record[0]

        self.record = record

        # 子ウィンドウの初期値
        self.title = "動画情報"
        self.size = (580, 400)
        return 0


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
