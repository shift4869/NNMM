import shutil
import sys
import unittest
import warnings
from collections import namedtuple
from pathlib import Path

from mock import MagicMock, call, mock_open, patch

from NNMM.video_info_fetcher.value_objects.mylist_url_factory import MylistURLFactory
from NNMM.video_info_fetcher.video_info_fetcher import VideoInfoFetcher

RSS_PATH = "./tests/rss/"


class TestVideoInfoFetcher(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)

    def tearDown(self):
        if Path(RSS_PATH).exists():
            shutil.rmtree(RSS_PATH)

    def _get_url_set(self) -> list[str]:
        """urlセットを返す"""
        url_info = [
            "https://www.nicovideo.jp/user/11111111/video",
            "https://www.nicovideo.jp/user/22222222/video",
            "https://www.nicovideo.jp/user/11111111/mylist/00000011",
            "https://www.nicovideo.jp/user/11111111/mylist/00000012",
            "https://www.nicovideo.jp/user/33333333/mylist/00000031",
            "https://www.nicovideo.jp/user/11111111/series/00000011",
        ]
        return url_info

    def test_init(self):
        urls = self._get_url_set()
        for url in urls:
            instance = VideoInfoFetcher(url)
            expect_mylist_url = MylistURLFactory.create(url)
            self.assertEqual(expect_mylist_url, instance.mylist_url)

    async def test_analysis_response_text(self):
        self.enterContext(patch("NNMM.video_info_fetcher.video_info_fetcher.logger.error"))
        mock_create = self.enterContext(patch("NNMM.video_info_fetcher.video_info_fetcher.ParserFactory.create"))

        async def f():
            return "parser.parse()"

        mock_create.return_value.parse.side_effect = f

        response_text = "response_text"
        urls = self._get_url_set()
        for url in urls:
            instance = VideoInfoFetcher(url)

            mock_create.reset_mock()
            actual = await instance._analysis_response_text(response_text)
            expect = "parser.parse()"
            self.assertEqual(expect, actual)

            mylist_url = MylistURLFactory.create(url)
            non_query_url = mylist_url.non_query_url
            mylist_type = mylist_url.mylist_type
            self.assertEqual([call(mylist_type, non_query_url, response_text), call().parse()], mock_create.mock_calls)

        mock_create.side_effect = ValueError
        url = urls[0]
        with self.assertRaises(ValueError):
            instance = VideoInfoFetcher(url)
            actual = await instance._analysis_response_text(response_text)

    async def test_fetch_videoinfo_from_fetch_url(self):
        self.enterContext(patch("NNMM.video_info_fetcher.video_info_fetcher.logger.error"))
        mock_config = self.enterContext(patch("NNMM.process.config.ConfigBase.get_config"))
        mock_session = self.enterContext(
            patch("NNMM.video_info_fetcher.video_info_fetcher.VideoInfoFetcher._get_session_response")
        )
        mock_analysis = self.enterContext(
            patch("NNMM.video_info_fetcher.video_info_fetcher.VideoInfoFetcher._analysis_response_text")
        )
        mock_api = self.enterContext(
            patch("NNMM.video_info_fetcher.video_info_fetcher.VideoInfoFetcher._get_videoinfo_from_api")
        )
        mock_path: MagicMock = self.enterContext(
            patch("NNMM.video_info_fetcher.video_info_fetcher.Path.open", mock_open())
        )
        mock_video_info = self.enterContext(patch("NNMM.video_info_fetcher.video_info_fetcher.FetchedVideoInfo.merge"))

        response_text = "response_text"
        urls = self._get_url_set()
        url = MylistURLFactory.create(urls[0])

        def prerun(
            is_valid_response, is_valid_title_list, is_valid_video_url_list, is_valid_config, mylistid, is_valid_write
        ):
            mock_session.reset_mock()
            if is_valid_response:
                mock_session.return_value.text = response_text
            else:
                mock_session.side_effect = lambda u: ""

            if is_valid_title_list:
                title_list_1 = "title_list"
                title_list_2 = "title_list"
            else:
                title_list_1 = "title_list_1"
                title_list_2 = "title_list_2"

            if is_valid_video_url_list:
                video_url_list_1 = "video_url_list"
                video_url_list_2 = "video_url_list"
            else:
                video_url_list_1 = "video_url_list_1"
                video_url_list_2 = "video_url_list_2"

            async def f(t):
                r = MagicMock()
                r.userid.id = "userid"
                r.mylistid.id = mylistid
                r.video_id_list = "video_id_list"
                r.title_list = title_list_1
                r.video_url_list = video_url_list_1
                return r

            mock_analysis.reset_mock()
            mock_analysis.side_effect = f

            async def g(v):
                r = MagicMock()
                r.title_list = title_list_2
                r.video_url_list = video_url_list_2
                return r

            mock_api.reset_mock()
            mock_api.side_effect = g

            def h(key, d):
                return RSS_PATH

            mock_config.reset_mock()
            if is_valid_config:
                mock_config.return_value.__getitem__.return_value.get.side_effect = h
            else:
                mock_config.side_effect = lambda: None

            def b(t):
                if is_valid_write:
                    return t
                else:
                    raise ValueError

            mock_path.reset_mock()
            mock_path.return_value.write.side_effect = b

            mock_video_info.reset_mock()
            mock_video_info.side_effect = lambda f, a: (f.video_url_list, a.video_url_list)
            return (video_url_list_1, video_url_list_2)

        def is_error(
            is_valid_response, is_valid_title_list, is_valid_video_url_list, is_valid_config, mylistid, is_valid_write
        ):
            return not all([is_valid_response, is_valid_title_list, is_valid_video_url_list, is_valid_config])

        def postrun(
            is_valid_response, is_valid_title_list, is_valid_video_url_list, is_valid_config, mylistid, is_valid_write
        ):
            if is_valid_response:
                self.assertEqual([call(url.fetch_url), call().__bool__()], mock_session.mock_calls)
            else:
                self.assertEqual([call(url.fetch_url)], mock_session.mock_calls)
                mock_analysis.assert_not_called()
                mock_api.assert_not_called()
                mock_config.assert_not_called()
                mock_path.assert_not_called()
                mock_video_info.assert_not_called()
                return

            self.assertEqual([call(response_text)], mock_analysis.mock_calls)
            if not is_valid_title_list:
                mock_config.assert_not_called()
                mock_path.assert_not_called()
                mock_video_info.assert_not_called()
                return

            self.assertEqual([call("video_id_list")], mock_api.mock_calls)
            if not is_valid_video_url_list:
                mock_config.assert_not_called()
                mock_path.assert_not_called()
                mock_video_info.assert_not_called()
                return

            if not is_valid_config:
                self.assertEqual(
                    [call()],
                    mock_config.mock_calls,
                )
                mock_path.assert_not_called()
                mock_video_info.assert_not_called()
                return

            self.assertEqual(
                [
                    call(),
                    call().__bool__(),
                    call().__getitem__("general"),
                    call().__getitem__().get("rss_save_path", ""),
                ],
                mock_config.mock_calls,
            )

            if is_valid_write:
                self.assertEqual(
                    [
                        call("w", encoding="utf-8"),
                        call().__enter__(),
                        call().write(response_text),
                        call().__exit__(None, None, None),
                        call().close(),
                    ],
                    mock_path.mock_calls,
                )

            mock_video_info.assert_called_once()

        Params = namedtuple(
            "Params",
            [
                "is_valid_response",
                "is_valid_title_list",
                "is_valid_video_url_list",
                "is_valid_config",
                "mylistid",
                "is_valid_write",
            ],
        )
        params_list = [
            Params(True, True, True, True, "mylistid", True),
            Params(True, True, True, True, "", True),
            Params(True, True, True, True, "mylistid", False),
            Params(True, True, True, False, "mylistid", True),
            Params(True, True, False, True, "mylistid", True),
            Params(True, False, True, True, "mylistid", True),
            Params(False, True, True, True, "mylistid", True),
        ]

        for params in params_list:
            instance = VideoInfoFetcher(url)

            expect = prerun(*params)
            if not is_error(*params):
                actual = await instance._fetch_videoinfo_from_fetch_url()
                self.assertEqual(expect, actual)
            else:
                with self.assertRaises(ValueError):
                    actual = await instance._fetch_videoinfo_from_fetch_url()
            postrun(*params)

    async def test_fetch_videoinfo(self):
        mock_fetch_videoinfo_from_fetch_url = self.enterContext(
            patch("NNMM.video_info_fetcher.video_info_fetcher.VideoInfoFetcher._fetch_videoinfo_from_fetch_url")
        )
        urls = self._get_url_set()
        url = urls[0]
        instance = VideoInfoFetcher(url)
        actual = await instance._fetch_videoinfo()
        mock_fetch_videoinfo_from_fetch_url.assert_awaited_once_with()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
