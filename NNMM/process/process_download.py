import asyncio
import threading
from logging import INFO, getLogger
from typing import TYPE_CHECKING

from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo

# import niconico_dl

if TYPE_CHECKING:
    from NNMM.main_window import MainWindow

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessDownload(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> None:
        """動画ダウンロード処理

        Notes:
            "動画ダウンロード::-TR-"
            動画右クリックメニューから動画ダウンロードが選択された場合
        """
        logger.info("Download video start.")

        # テーブルの行が選択されていなかったら何もしない
        if not self.values["-TABLE-"]:
            logger.info("Table row is not selected.")
            return -1

        try:
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
            records = self.mylist_info_db.select_from_id_url(video_id, mylist_url)

            if records == []:
                logger.error("Selected row is invalid.")
                return -1

            self.record = records[0]
        except IndexError:
            logger.error("Download video failed, getting record info is failed.")
            return -1

        # 左下の表示変更
        self.window["-INPUT2-"].update(value="動画DL開始(ログ参照)")
        self.window.refresh()

        logger.info(video_url + " : download start ...")

        # マルチスレッド処理
        threading.Thread(
            target=self.download_thread,
            args=(self.record, ),
            daemon=True
        ).start()
        return

    def download_thread(self, record) -> int:
        """動画ダウンロードワーカーを実行する処理

        Notes:
            threading.Threadにより別threadで実行される前提

        Args:
            record (dict): DL対象の動画情報レコード

        Returns:
            int: 動画ダウンロードに成功したら0,
                 エラー時-1
        """
        if not (record and "video_url" in record):
            logger.error("DownloadThread failed, argument record is invalid.")
            return -1

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        res = loop.run_until_complete(self.download_thread_worker(record))

        video_url = record["video_url"]
        logger.info(video_url + " : download done.")
        self.window.write_event_value("-DOWNLOAD_THREAD_DONE-", "")
        return res

    async def download_thread_worker(self, record) -> int:
        """動画ダウンロードワーカー

        Notes:
            niconico_dlライブラリを使用

        Args:
            record (dict): DL対象の動画情報レコード

        Returns:
            int: 動画ダウンロードに成功したら0,
                 エラー時-1
        """
        if not (record and "video_url" in record):
            logger.error("DownloadThreadWorker failed, argument record is invalid.")
            return -1

        video_url = record["video_url"]
        # with niconico_dl.NicoNicoVideo(video_url, log=True) as nico:
        #     data = nico.get_info()
        #     nico.download(data["video"]["title"] + ".mp4", load_chunk_size=8 * 1024 * 1024)
        return 0


class ProcessDownloadThreadDone(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> None:
        """動画ダウンロードのマルチスレッド処理が終わった後の処理

        Notes:
            "-DOWNLOAD_THREAD_DONE-"
        """
        # 左下の表示を更新する
        self.window["-INPUT2-"].update(value="動画DL完了!")

        logger.info("Download video done.")
        return


if __name__ == "__main__":
    # video_url = "https://www.nicovideo.jp/watch/sm9"

    # def DownloadVideo(url):
    #     with niconico_dl.NicoNicoVideoAsync(url, log=False) as nico:
    #         data = nico.get_info()
    #         nico.download(data["video"]["title"] + ".mp4")

    # DownloadVideo(video_url)
    # print("Downloaded!")

    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
