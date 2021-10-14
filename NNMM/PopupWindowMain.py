# coding: utf-8
from abc import abstractmethod
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.Process import ProcessBase

logger = getLogger("root")
logger.setLevel(INFO)


class PopupWindowBase(ProcessBase.ProcessBase):
    # 情報ウィンドウのベースクラス
    # 派生クラスと外部から使用されるクラス変数とクラスメソッドを定義する
    # このベースクラス自体は抽象クラスのためインスタンスは作成できない

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
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
    def MakeWindowLayout(self, mw):
        # 画面のレイアウトを作成する
        return None

    @abstractmethod
    def Init(self, mw):
        # 初期化
        pass

    def Run(self, mw):
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

    def MakeWindowLayout(self, mw):
        # 画面のレイアウトを作成する
        horizontal_line = "-" * 132
        csize = (20, 1)
        tsize = (50, 1)

        r = self.record
        id_index = r["id"]
        username = r["username"]
        mylistname = r["mylistname"]
        typename = r["type"]
        showname = r["showname"]
        url = r["url"]
        created_at = r["created_at"]
        updated_at = r["updated_at"]
        checked_at = r["checked_at"]
        check_interval = r["check_interval"]
        is_include_new = "True" if r["is_include_new"] else "False"

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
            [sg.Text("更新確認インターバル", size=csize), sg.Input(f"{check_interval}", key="-CHECK_INTERVAL-", background_color="light goldenrod", size=tsize)],
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

    def Init(self, mw):
        # 初期化
        # 親ウィンドウからの情報を取得する
        # self.window = mw.window
        # self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # 選択されたマイリストのマイリストレコードオブジェクトを取得する
        v = mw.values.get("-LIST-")
        if v and len(v) > 0:
            v = v[0]

        if v[:2] == "*:":
            v = v[2:]
        record = self.mylist_db.SelectFromShowname(v)
        
        if record and len(record) == 1:
            record = record[0]

        self.record = record

        # 子ウィンドウの初期値
        self.title = "マイリスト情報"
        self.size = (580, 450)
        self.ep_dict = {
            "-SAVE-": PopupMylistWindowSave,
        }


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
        check_interval = self.window["-CHECK_INTERVAL-"].get()
        is_include_new = str(self.window["-IS_INCLUDE_NEW-"].get()) == "True"

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
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時"]

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

        mylist_url = values["-INPUT1-"]

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

        records = self.mylist_info_db.SelectFromVideoID(selected[1])
        record = [r for r in records if r["mylist_url"] == mylist_url]

        if record and len(record) == 1:
            record = record[0]

        self.record = record

        # 子ウィンドウの初期値
        self.title = "動画情報"
        self.size = (580, 400)


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()