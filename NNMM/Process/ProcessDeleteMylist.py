# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.GuiFunction import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.Process import ProcessBase

logger = getLogger("root")
logger.setLevel(INFO)


class ProcessDeleteMylist(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト削除")

    def Run(self, mw) -> int:
        """マイリスト削除ボタン押下時の処理

        Notes:
            "-DELETE-"
            左下のマイリスト削除ボタンが押された場合
            またはマイリスト右クリックメニューからマイリスト削除が選択された場合

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: マイリスト削除に成功したら0,
                 キャンセルされたなら1,
                 エラー時-1
        """
        logger.info("Delete mylist start.")
        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("Delete mylist failed, argument error.")
            return -1

        # 対象マイリストの候補を取得する
        # 優先順位は(1)マイリストペインにて選択中のマイリスト＞(2)現在テーブルペインに表示中のマイリスト＞(3)左下テキストボックス内入力
        mylist_url = ""
        prev_mylist = {}
        try:
            if "-LIST-" in self.values and len(self.values["-LIST-"]) > 0:
                # (1)マイリストlistboxの選択値（右クリック時などほとんどの場合）
                v = self.values["-LIST-"][0]
                if v[:2] == "*:":
                    v = v[2:]
                record = self.mylist_db.select_from_showname(v)[0]
                mylist_url = record.get("url", "")
            elif self.values.get("-INPUT1-", "") != "":
                # (2)右上のテキストボックス
                mylist_url = self.values.get("-INPUT1-", "")
            elif self.values.get("-INPUT2-", "") != "":
                # (3)左下のテキストボックス
                mylist_url = self.values.get("-INPUT2-", "")

            # 既存マイリストに存在していない場合何もしない
            prev_mylist = self.mylist_db.select_from_url(mylist_url)[0]
            if not prev_mylist:
                logger.error("Delete mylist failed, target mylist not found.")
                return -1
        except IndexError:
            logger.error("Delete mylist failed, target mylist not found.")
            return -1

        # 確認
        showname = prev_mylist.get("showname", "")
        msg = f"{showname}\n{mylist_url}\nマイリスト削除します"
        res = sg.popup_ok_cancel(msg, title="削除確認")
        if res == "Cancel":
            self.window["-INPUT2-"].update(value="マイリスト削除キャンセル")
            logger.error("Delete mylist canceled.")
            return 1

        # マイリスト情報から対象動画の情報を削除する
        self.mylist_info_db.delete_in_mylist(mylist_url)

        # マイリストからも削除する
        self.mylist_db.delete_from_mylist_url(mylist_url)

        # マイリスト画面表示更新
        UpdateMylistShow(self.window, self.mylist_db)

        # マイリスト情報テーブルの表示を初期化する
        self.window["-TABLE-"].update(values=[[]])
        self.window["-INPUT1-"].update(value="")

        self.window["-INPUT2-"].update(value="マイリスト削除完了")
        logger.info("Delete mylist success.")
        return 0


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
