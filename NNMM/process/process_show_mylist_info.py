from logging import INFO, getLogger

from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, update_table_pane

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessShowMylistInfo(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """選択されたマイリストに含まれる動画情報レコードを表示する

        Notes:
            "-LIST-+DOUBLE CLICK+"
            リストボックスの項目がダブルクリックされた場合（単一）
        """
        logger.info("ShowMylistInfo start.")

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
        return


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
