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
        if not hasattr(self, "mylist_db"):
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

    def Run(self, mw):
        # -UPDATE-のマルチスレッド処理が終わった後の処理
        window = mw.window
        values = mw.values
        mylist_db = mw.mylist_db
        mylist_info_db = mw.mylist_info_db
        # 左下の表示を戻す
        window["-INPUT2-"].update(value="更新完了！")

        # テーブルの表示を更新する
        mylist_url = values["-INPUT1-"]
        if mylist_url != "":
            UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)
        window.refresh()

        # マイリストの新着表示を表示するかどうか判定する
        def_data = window["-TABLE-"].Values  # 現在のtableの全リスト

        # 左のマイリストlistboxの表示を更新する
        # 一つでも未視聴の動画が含まれる場合はマイリストの進捗フラグを立てる
        if IsMylistIncludeNewVideo(def_data):
            # 新着フラグを更新
            mylist_db.UpdateIncludeFlag(mylist_url, True)

        # マイリスト画面表示更新
        UpdateMylistShow(window, mylist_db)

        logger.info(mylist_url + " : update done.")


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
