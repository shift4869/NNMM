# coding: utf-8
import asyncio
import threading
from logging import INFO, getLogger

import PySimpleGUI as sg
import niconico_dl

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM import GetMyListInfo
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessDownload(ProcessBase.ProcessBase):

    def __init__(self, log_sflag: bool = False, log_eflag: bool = False, process_name: str = None):
        # 派生クラス（すべて更新時）の生成時は引数ありで呼び出される
        if process_name:
            super().__init__(log_sflag, log_eflag, process_name)
        else:
            super().__init__(True, False, "動画ダウンロード")

    def Run(self, mw):
        # "動画ダウンロード::-TR-"
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

        # 動画情報を取得する
        video_id = selected[1]
        video_url = selected[6]
        mylist_url = selected[7]
        records = self.mylist_info_db.SelectFromIDURL(video_id, mylist_url)

        if records == []:
            logger.info("Selected row is invalid.")
            return

        self.record = records[0]

        # 左下の表示変更
        self.window["-INPUT2-"].update(value="動画DL開始(ログ参照)")
        self.window.refresh()

        logger.info(video_url + " : download start ...")

        # マルチスレッド処理
        threading.Thread(target=self.DownloadThread, args=(self.record, ), daemon=True).start()

    def DownloadThread(self, record):
        loop = asyncio.new_event_loop()
        res = loop.run_until_complete(self.DownloadThreadWorker(record))

        video_url = record["video_url"]
        logger.info(video_url + " : download done.")
        self.window.write_event_value("-DOWNLOAD_THREAD_DONE-", "")

    async def DownloadThreadWorker(self, record: Mylist):
        video_url = record["video_url"]
        # TODO::プログレス表示
        with niconico_dl.NicoNicoVideo(video_url, log=False) as nico:
            data = nico.get_info()
            nico.download(data["video"]["title"] + ".mp4")
        pass


class ProcessDownloadThreadDone(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(False, True, "動画ダウンロード")

    def Run(self, mw):
        # -DOWNLOAD-のマルチスレッド処理が終わった後の処理
        window = mw.window
        values = mw.values
        mylist_db = mw.mylist_db
        mylist_info_db = mw.mylist_info_db
        # 左下の表示を更新する
        window["-INPUT2-"].update(value="動画DL完了!")

        # logger.info(video_url + " : download done.")


if __name__ == "__main__":
    # video_url = "https://www.nicovideo.jp/watch/sm39619606"

    # def DownloadVideo(url):
    #     with niconico_dl.NicoNicoVideoAsync(url, log=False) as nico:
    #         data = nico.get_info()
    #         nico.download(data["video"]["title"] + ".mp4")

    # DownloadVideo(video_url)
    # print("Downloaded!")
    
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
    pass
