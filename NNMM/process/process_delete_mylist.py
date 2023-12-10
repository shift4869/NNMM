from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.gui_function import update_mylist_pane
from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessDeleteMylist(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> None:
        """マイリスト削除ボタン押下時の処理

        Notes:
            "-DELETE-"
            左下のマイリスト削除ボタンが押された場合
            またはマイリスト右クリックメニューからマイリスト削除が選択された場合
        """
        logger.info("Delete mylist start.")

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
                return
        except IndexError:
            logger.error("Delete mylist failed, target mylist not found.")
            return

        # 確認
        showname = prev_mylist.get("showname", "")
        msg = f"{showname}\n{mylist_url}\nマイリスト削除します"
        res = sg.popup_ok_cancel(msg, title="削除確認")
        if res == "Cancel":
            self.window["-INPUT2-"].update(value="マイリスト削除キャンセル")
            logger.error("Delete mylist canceled.")
            return

        # マイリスト情報から対象動画の情報を削除する
        self.mylist_info_db.delete_in_mylist(mylist_url)

        # マイリストからも削除する
        self.mylist_db.delete_from_mylist_url(mylist_url)

        # マイリスト画面表示更新
        update_mylist_pane(self.window, self.mylist_db)

        # マイリスト情報テーブルの表示を初期化する
        self.window["-TABLE-"].update(values=[[]])
        self.window["-INPUT1-"].update(value="")

        self.window["-INPUT2-"].update(value="マイリスト削除完了")
        logger.info("Delete mylist success.")
        return


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
