from logging import INFO, getLogger

from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, update_mylist_pane, update_table_pane

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessNotWatched(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """動画の状況ステータスを"未視聴"に設定する

        Notes:
            "未視聴にする::-TR-"
            テーブル右クリックで「未視聴にする」が選択された場合

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("NotWatched start.")

        # 現在のtableの全リスト
        def_data = self.window["-TABLE-"].Values

        # 行が選択されていないなら何もしない
        if not self.values["-TABLE-"]:
            logger.error("NotWatched failed, no record selected.")
            return Result.failed

        # 選択された行（複数可）についてすべて処理する
        all_num = len(self.values["-TABLE-"])
        row = 0
        for i, v in enumerate(self.values["-TABLE-"]):
            row = int(v)

            # マイリスト情報ステータスDB更新
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL"]
            selected = def_data[row]
            res = self.mylist_info_db.update_status(selected[1], selected[8], "未視聴")
            if res == 0:
                logger.info(f'{selected[1]} ({i + 1}/{all_num}) -> marked "non-watched".')
            else:
                logger.info(f"{selected[1]} ({i + 1}/{all_num}) -> failed.")

            # テーブル更新
            def_data[row][4] = "未視聴"

            # 未視聴になったことでマイリストの新着表示を表示する
            # 未視聴にしたので必ず新着あり扱いになる
            # マイリストDB新着フラグ更新
            self.mylist_db.update_include_flag(selected[8], True)

        # テーブル更新を反映させる
        self.window["-TABLE-"].update(values=def_data)

        # テーブルの表示を更新する
        mylist_url = self.values["-INPUT1-"]
        update_table_pane(self.window, self.mylist_db, self.mylist_info_db, mylist_url)
        self.window["-TABLE-"].update(select_rows=[row])

        # マイリスト画面表示更新
        update_mylist_pane(self.window, self.mylist_db)

        logger.info("NotWatched success.")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
