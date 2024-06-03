from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from nnmm.process import config as process_config
from nnmm.process.base import ProcessBase
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row import Status
from nnmm.process.watched import Watched
from nnmm.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class VideoPlay(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """選択された動画をブラウザで開く

        Notes:
            "ブラウザで開く::-TR-"
            テーブル右クリックで「再生」が選択された場合
        """
        logger.info(f"VideoPlay start.")

        # テーブルの行が選択されていなかったら何もしない
        selected_table_row_index_list = self.get_selected_table_row_index_list()
        if not selected_table_row_index_list:
            logger.info("VideoPlay failed, Table row is not selected.")
            return Result.failed

        # 選択されたテーブル行
        selected_table_row_list = self.get_selected_table_row_list()
        selected_table_row = selected_table_row_list[0]

        # 動画URLを取得
        records = self.mylist_info_db.select_from_video_id(selected_table_row.video_id.id)
        record = records[0]
        video_url = record.get("video_url")

        config = process_config.ConfigBase.get_config()
        cmd = config["general"].get("browser_path", "")
        if cmd != "" and Path(cmd).is_file():
            # ブラウザに動画urlを渡す
            sp = sg.execute_command_subprocess(cmd, video_url)
            # logger.info(sg.execute_get_results(sp)[0])
            logger.info(f"{cmd} -> valid browser path.")
            logger.info(f"{video_url} -> video page opened with browser.")
        else:
            # ブラウザパスが不正
            sg.popup_ok("ブラウザパスが不正です。設定タブから設定してください。")
            logger.info(f"{cmd} -> invalid browser path.")
            logger.info(f"{video_url} -> video page open failed.")
            return Result.failed

        # 状況を更新
        if selected_table_row.status != Status.watched:
            # 視聴済にする
            pb = Watched(self.process_info)
            pb.run()

        logger.info(f"VideoPlay success.")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
