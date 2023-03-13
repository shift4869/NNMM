# coding: utf-8
"""ProcessDownload のテスト
"""
import asyncio
import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, call, patch

from NNMM.Process import ProcessDownload


class TestProcessDownload(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def __GetRecordList(self):
        record_list = {
            "sm11111111": (1, "sm11111111", "動画タイトル1", "投稿者1", "未視聴", "2021-05-29 22:00:11",
                           "https://www.nicovideo.jp/watch/sm11111111", "https://www.nicovideo.jp/user/11111111/video", "マイリスト1", "")
        }
        return record_list

    def __ReturnSelectFromIDURL(self, video_id, mylist_url):
        res = {}
        record_list = self.__GetRecordList()
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded", "video_url", "mylist_url", "showname", "mylistname"]
        table_vals = record_list.get(video_id, ("", ))
        if len(table_cols) != len(table_vals):
            return {}
        for c, v in zip(table_cols, table_vals):
            res[c] = v
        return [res]

    def test_PDLRun(self):
        """ProcessDownloadのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessDownload.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessDownload.logger.error"))
            mockthread = stack.enter_context(patch("threading.Thread"))

            pdl = ProcessDownload.ProcessDownload()

            # 正常系
            video_id_s = "sm11111111"
            mylist_url_s = "https://www.nicovideo.jp/user/11111111/video"

            def ReturnMockValue(value):
                r = MagicMock()
                r.Values = value
                return r

            expect_values_dict = {
                "-TABLE-": [0]
            }
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "動画URL", "所属マイリストURL"]
            row_e = self.__GetRecordList().get(video_id_s, ("", ))
            expect_window_dict = {
                "-TABLE-": ReturnMockValue([row_e]),
                "-INPUT2-": MagicMock()
            }

            mockmw = MagicMock()
            mockwindow = MagicMock()
            mockwindow.__getitem__.side_effect = expect_window_dict.__getitem__
            mockwindow.__iter__.side_effect = expect_window_dict.__iter__
            mockwindow.__contains__.side_effect = expect_window_dict.__contains__
            type(mockmw).window = mockwindow
            mockvalue = MagicMock()
            mockvalue.__getitem__.side_effect = expect_values_dict.__getitem__
            mockvalue.__iter__.side_effect = expect_values_dict.__iter__
            mockvalue.__contains__.side_effect = expect_values_dict.__contains__
            type(mockmw).values = mockvalue
            mockmylist_info_db = MagicMock()
            type(mockmylist_info_db).SelectFromIDURL = self.__ReturnSelectFromIDURL
            type(mockmw).mylist_info_db = mockmylist_info_db

            actual = pdl.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            def assertMockCall():
                mc = mockmw.window.mock_calls
                self.assertEqual(3, len(mc))
                self.assertEqual(call.__getitem__("-TABLE-"), mc[0])
                self.assertEqual(call.__getitem__("-INPUT2-"), mc[1])
                self.assertEqual(call.refresh(), mc[2])
                mockmw.window.reset_mock()

                mc = mockmw.values.mock_calls
                self.assertEqual(2, len(mc))
                self.assertEqual(call.__getitem__("-TABLE-"), mc[0])
                self.assertEqual(call.__getitem__("-TABLE-"), mc[1])
                mockmw.values.reset_mock()

                mc = mockthread.mock_calls
                record = self.__ReturnSelectFromIDURL(video_id_s, mylist_url_s)[0]
                mockthread.assert_called_with(target=pdl.DownloadThread, args=(record, ), daemon=True)
                mockthread.reset_mock()

            assertMockCall()

            # 異常系
            # 動画情報取得に失敗
            type(mockmylist_info_db).SelectFromIDURL = lambda s, video_id, mylist_url: []
            actual = pdl.Run(mockmw)
            self.assertEqual(-1, actual)

            # テーブル行取得に失敗
            expect_window_dict["-TABLE-"] = ReturnMockValue([["invalid table row"]])
            actual = pdl.Run(mockmw)
            self.assertEqual(-1, actual)

            # テーブル行が選択されていない
            expect_values_dict["-TABLE-"] = []
            actual = pdl.Run(mockmw)
            self.assertEqual(-1, actual)

            # 引数エラー
            del mockmw.window
            del type(mockmw).window
            actual = pdl.Run(mockmw)
            self.assertEqual(-1, actual)

    def test_PDLDownloadThread(self):
        """ProcessDownloadの動画ダウンロードワーカーを実行する処理をテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessDownload.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessDownload.logger.error"))
            mockworker = stack.enter_context(patch("NNMM.Process.ProcessDownload.ProcessDownload.DownloadThreadWorker"))

            pdl = ProcessDownload.ProcessDownload()

            # 正常系
            mockworker.return_value = 0
            pdl.window = MagicMock()
            video_id_s = "sm11111111"
            mylist_url_s = "https://www.nicovideo.jp/user/11111111/video"
            record = self.__ReturnSelectFromIDURL(video_id_s, mylist_url_s)[0]
            actual = pdl.DownloadThread(record)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            mc = pdl.window.mock_calls
            self.assertEqual(1, len(mc))
            self.assertEqual(call.write_event_value("-DOWNLOAD_THREAD_DONE-", ""), mc[0])
            pdl.window.reset_mock()
            mockworker.assert_called()
            mockworker.reset_mock()

            # 異常系
            # レコードが不正
            record = {"invalid": "invalid record"}
            actual = pdl.DownloadThread(record)
            self.assertEqual(-1, actual)

    def test_PDLDownloadThread(self):
        """ProcessDownloadの動画ダウンロードワーカーをテストする
        """
        with ExitStack() as stack:
            mockle = stack.enter_context(patch("NNMM.Process.ProcessDownload.logger.error"))
            mocknico = stack.enter_context(patch("niconico_dl.NicoNicoVideo"))

            pdl = ProcessDownload.ProcessDownload()

            # 正常系
            video_id_s = "sm11111111"
            mylist_url_s = "https://www.nicovideo.jp/user/11111111/video"
            record = self.__ReturnSelectFromIDURL(video_id_s, mylist_url_s)[0]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(pdl.DownloadThreadWorker(record))
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            mc = mocknico.mock_calls
            self.assertEqual(8, len(mc))
            self.assertEqual(call(record["video_url"], log=True), mc[0])
            self.assertEqual(call().__enter__(), mc[1])
            self.assertEqual(call().__enter__().get_info(), mc[2])
            self.assertEqual(call().__enter__().get_info().__getitem__("video"), mc[3])
            self.assertEqual(call().__enter__().get_info().__getitem__().__getitem__("title"), mc[4])
            self.assertEqual(call().__enter__().get_info().__getitem__().__getitem__().__add__(".mp4"), mc[5])
            mockarg = mocknico().__enter__().get_info().__getitem__().__getitem__().__add__()
            self.assertEqual(call().__enter__().download(mockarg, load_chunk_size=8 * 1024 * 1024), mc[6])
            self.assertEqual(call().__exit__(None, None, None), mc[7])
            mocknico.reset_mock()

            # 異常系
            # レコードが不正
            record = {"invalid": "invalid record"}
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            actual = loop.run_until_complete(pdl.DownloadThreadWorker(record))
            self.assertEqual(-1, actual)

    def test_PDLTDRun(self):
        """ProcessDownloadThreadDoneのRunをテストする
        """
        with ExitStack() as stack:
            mockli = stack.enter_context(patch("NNMM.Process.ProcessDownload.logger.info"))
            mockle = stack.enter_context(patch("NNMM.Process.ProcessDownload.logger.error"))

            pdltd = ProcessDownload.ProcessDownloadThreadDone()

            # 正常系
            mockmw = MagicMock()
            actual = pdltd.Run(mockmw)
            self.assertEqual(0, actual)

            # 実行後呼び出し確認
            mc = mockmw.window.mock_calls
            self.assertEqual(2, len(mc))
            self.assertEqual(call.__getitem__("-INPUT2-"), mc[0])
            self.assertEqual(call.__getitem__().update(value="動画DL完了!"), mc[1])

            # 引数エラー
            del mockmw.window
            actual = pdltd.Run(mockmw)
            self.assertEqual(-1, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
