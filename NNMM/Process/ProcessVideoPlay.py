# coding: utf-8
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM import ConfigMain
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process.ProcessWatched import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessVideoPlay(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "ブラウザで開く")

    def Run(self, mw):
        # "ブラウザで開く::-TR-"
        # テーブル右クリックで「再生」が選択された場合
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # テーブルの行が選択されていなかったら何もしない
        if not self.values["-TABLE-"]:
            logger.info("Table row is none selected.")
            return

        # 選択されたテーブル行数
        row = int(self.values["-TABLE-"][0])
        # 現在のテーブルの全リスト
        def_data = self.window["-TABLE-"].Values
        # 選択されたテーブル行
        selected = def_data[row]

        # ブラウザに動画urlを渡す
        config = ConfigMain.ProcessConfigBase.GetConfig()
        cmd = config["general"].get("browser_path", "")
        video_url = self.mylist_info_db.SelectFromVideoID(selected[1])[0].get("video_url")
        if cmd != "" and Path(cmd).is_file():
            sp = sg.execute_command_subprocess(cmd, video_url)
            # logger.info(sg.execute_get_results(sp)[0])
            logger.info(f"{cmd} -> valid browser path.")
            logger.info(f"{video_url} -> browser opened.")
        else:
            sg.popup_ok("ブラウザパスが不正です。設定タブから設定してください。")
            logger.info(f"{cmd} -> invalid browser path.")
            logger.info(f"{video_url} -> browser open failed.")
        
        # 視聴済にする
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時"]
        mylist_url = self.values["-INPUT1-"]
        # 状況を更新
        if def_data[row][4] != "":
            def_data[row][4] = ""
            self.window["-TABLE-"].update(values=def_data)

        # 視聴済にする
        pb = ProcessWatched()
        pb.Run(mw)


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
