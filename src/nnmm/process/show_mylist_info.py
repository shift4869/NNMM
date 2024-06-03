from logging import INFO, getLogger

from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.mylist_row import SelectedMylistRow
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class ShowMylistInfo(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """選択されたマイリストに含まれる動画情報レコードを表示する

        Notes:
            "-LIST-+DOUBLE CLICK+"
            リストボックスの項目がダブルクリックされた場合（単一）

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("ShowMylistInfo start.")

        # ダブルクリックされたリストボックスの選択値を取得
        selected_mylist = self.get_selected_mylist_row()

        # 新着表示のマークがある場合は削除する
        showname = selected_mylist.without_new_mark_name()

        # 対象マイリストをmylist_dbにshownameで問い合わせ
        record = self.mylist_db.select_from_showname(showname)[0]

        # 対象マイリストのアドレスをテキストボックスに表示
        mylist_url = record.get("url")
        self.window["-INPUT1-"].update(value=mylist_url)

        # テーブル更新
        self.update_table_pane(mylist_url)

        logger.info(f"{mylist_url} -> mylist info shown.")
        logger.info("ShowMylistInfo success.")
        return Result.success


if __name__ == "__main__":
    from nnmm import main_window

    mw = main_window.MainWindow()
    mw.run()
