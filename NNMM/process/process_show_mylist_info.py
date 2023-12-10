from logging import INFO, getLogger

from NNMM.gui_function import update_table_pane
from NNMM.process.process_base import ProcessBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessShowMylistInfo(ProcessBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト内容表示")

    def run(self, mw):
        """選択されたマイリストに含まれる動画情報レコードを表示する

        Notes:
            "-LIST-+DOUBLE CLICK+"
            リストボックスの項目がダブルクリックされた場合（単一）

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 処理成功した場合0, エラー時-1
        """
        logger.info("ShowMylistInfo start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("ShowMylistInfo failed, argument error.")
            return -1

        # ダブルクリックされたリストボックスの選択値を取得
        v = self.values["-LIST-"][0]

        # 新着表示のマークがある場合は削除する
        NEW_MARK = "*:"
        if v[:2] == NEW_MARK:
            v = v[2:]

        # 対象マイリストをmylist_dbにshownameで問い合わせ
        record = self.mylist_db.select_from_showname(v)[0]
        mylist_url = record.get("url")
        self.window["-INPUT1-"].update(value=mylist_url)  # 対象マイリストのアドレスをテキストボックスに表示

        # テーブル更新
        update_table_pane(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info(f"{mylist_url} -> mylist info shown.")
        logger.info("ShowMylistInfo success.")
        return 0


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
