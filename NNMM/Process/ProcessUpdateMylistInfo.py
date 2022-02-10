# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process.ProcessUpdateAllMylistInfo import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessUpdateMylistInfo(ProcessUpdateAllMylistInfo):

    def __init__(self):
        """マイリスト情報を更新する

        Notes:
            "-UPDATE-"
            右上の更新ボタンが押された場合
            ProcessUpdateMylistInfoは現在表示されている単一のマイリストについて動画情報を更新する
            ProcessUpdateAllMylistInfoを継承し、更新対象として単一のマイリストを返すことで
            その他の処理を継承元に任せている
        """
        super().__init__(True, False, "マイリスト内容更新")

        # ログメッセージ
        self.L_KIND = "Mylist"

        # イベントキー
        self.E_DONE = "-UPDATE_THREAD_DONE-"

    def GetTargetMylist(self) -> list[Mylist]:
        """更新対象のマイリストを返す

        Note:
            ProcessUpdateMylistInfoにおいては対象は単一のマイリストとなる

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        # 属性チェック
        if not hasattr(self, "mylist_db") or not hasattr(self, "values"):
            logger.error(f"{self.L_KIND} GetTargetMylist failed, attribute error.")
            return []

        mylist_url = self.values["-INPUT1-"]
        if mylist_url == "":
            return []

        m_list = self.mylist_db.SelectFromURL(mylist_url)
        return m_list


class ProcessUpdateMylistInfoThreadDone(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, True, "マイリスト内容更新")

        # ログメッセージ
        self.L_KIND = "Mylist"

    def Run(self, mw) -> int:
        """マイリスト情報を更新後の後処理

        Notes:
            "-UPDATE_THREAD_DONE-"
            -UPDATE-の処理が終わった後の処理

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, エラー時-1
        """
        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error(f"{self.L_KIND} update failed, argument error.")
            return -1

        # 左下の表示を戻す
        self.window["-INPUT2-"].update(value="更新完了！")

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        if mylist_url != "":
            UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)
        self.window.refresh()

        # マイリストの新着表示を表示するかどうか判定する
        def_data = self.window["-TABLE-"].Values  # 現在のtableの全リスト

        # 左のマイリストlistboxの表示を更新する
        # 一つでも未視聴の動画が含まれる場合はマイリストの進捗フラグを立てる
        if IsMylistIncludeNewVideo(def_data):
            # 新着フラグを更新
            self.mylist_db.UpdateIncludeFlag(mylist_url, True)

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)

        logger.info(f"{self.L_KIND} update success.")
        return 0


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
