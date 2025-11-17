from logging import INFO, getLogger

from PySide6.QtWidgets import QDialog

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class DeleteMylist(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト削除ボタン押下時の処理

        Notes:
            "-DELETE-"
            左下のマイリスト削除ボタンが押された場合
            またはマイリスト右クリックメニューからマイリスト削除が選択された場合
        """
        logger.info("Delete mylist start.")

        # 対象マイリストの候補を取得する
        # 優先順位は
        # (1)マイリストペインにて選択中のマイリスト＞
        # (2)現在テーブルペインに表示中のマイリスト＞
        # (3)左下テキストボックス内入力
        mylist_url = ""
        prev_mylist = {}
        try:
            selected_mylist_row = self.get_selected_mylist_row()
            if selected_mylist_row:
                # (1)マイリストlistboxの選択値（右クリック時などほとんどの場合）
                showname = selected_mylist_row.without_new_mark_name()
                record = self.mylist_db.select_from_showname(showname)[0]
                mylist_url = record.get("url", "")
            elif textbox := self.get_upper_textbox():
                # (2)右上のテキストボックス
                mylist_url = textbox.to_str()
            elif textbox := self.get_bottom_textbox():
                # (3)左下のテキストボックス
                mylist_url = textbox.to_str()

            # 既存マイリストに存在していない場合何もしない
            prev_mylist = self.mylist_db.select_from_url(mylist_url)[0]
            if not prev_mylist:
                logger.error("Delete mylist failed, target mylist not found.")
                return Result.failed
        except IndexError:
            logger.error("Delete mylist failed, target mylist not found.")
            return Result.failed

        # 確認
        showname = prev_mylist.get("showname", "")
        msg = f"{showname}\n{mylist_url}\nマイリスト削除します"
        res = sg.popup_ok_cancel(msg, title="削除確認")
        if res == "Cancel":
            self.window["-INPUT2-"].update(value="マイリスト削除キャンセル")
            logger.error("Delete mylist canceled.")
            return Result.failed

        # マイリスト情報から対象動画の情報を削除する
        self.mylist_info_db.delete_in_mylist(mylist_url)

        # マイリストからも削除する
        self.mylist_db.delete_from_mylist_url(mylist_url)

        # マイリスト画面表示更新
        self.update_mylist_pane()

        # マイリスト情報テーブルの表示を初期化する
        self.window["-TABLE-"].update(values=[[]])
        self.window["-INPUT1-"].update(value="")

        self.window["-INPUT2-"].update(value="マイリスト削除完了")
        logger.info("Delete mylist success.")
        return Result.success


if __name__ == "__main__":
    from nnmm import main_window

    mw = main_window.MainWindow()
    mw.run()
