# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM import ConfigMain
from NNMM.GuiFunction import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.Process import ProcessBase
from NNMM.Process.ProcessWatched import *

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessVideoPlay(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "ブラウザで開く")

    def run(self, mw) -> int:
        """選択された動画をブラウザで開く

        Notes:
            "ブラウザで開く::-TR-"
            テーブル右クリックで「再生」が選択された場合

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, エラー時-1
        """
        logger.info(f"VideoPlay start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("VideoPlay failed, argument error.")
            return -1

        # テーブルの行が選択されていなかったら何もしない
        if not self.values["-TABLE-"]:
            logger.info("VideoPlay failed, Table row is not selected.")
            return -1

        # 選択されたテーブル行数
        row = int(self.values["-TABLE-"][0])
        # 現在のテーブルの全リスト
        def_data = self.window["-TABLE-"].Values
        # 選択されたテーブル行
        selected = def_data[row]

        # 動画URLを取得
        records = self.mylist_info_db.selectFromVideoID(selected[1])
        record = records[0]
        video_url = record.get("video_url")

        config = ConfigMain.ProcessConfigBase.GetConfig()
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
            return -1

        # 視聴済にする
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        STATUS_INDEX = 4
        # 状況を更新
        if def_data[row][STATUS_INDEX] != "":
            # 視聴済にする
            pb = ProcessWatched()
            pb.run(mw)

        logger.info(f"VideoPlay success.")
        return 0


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.run()
