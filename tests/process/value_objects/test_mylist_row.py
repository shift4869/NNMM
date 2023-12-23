import sys
import unittest
from collections import namedtuple
from contextlib import ExitStack
from dataclasses import FrozenInstanceError

from mock import patch

from NNMM.process.value_objects.mylist_row import MylistRow, SelectedMylistRow
from NNMM.process.value_objects.showname import Showname


class TestMylistRow(unittest.TestCase):
    def test_init(self):
        Params = namedtuple("Params", ["showname", "result"])
        params_list = [
            Params("投稿者1さんの投稿動画", "投稿者1さんの投稿動画"),
            Params("「マイリスト1」-投稿者1さんのマイリスト", "「マイリスト1」-投稿者1さんのマイリスト"),
            Params("*:投稿者1さんの投稿動画", "投稿者1さんの投稿動画"),
            Params(-1, "invalid"),
            Params("1", "invalid"),
        ]
        for params in params_list:
            if params.result == "invalid":
                with self.assertRaises((ValueError, TypeError)):
                    instance = MylistRow(params.showname)
            else:
                instance = MylistRow(params.showname)
                self.assertEqual(params.result, instance.name)
        for params in params_list:
            if params.result == "invalid":
                with self.assertRaises((ValueError, TypeError)):
                    instance = SelectedMylistRow(params.showname)
            else:
                instance = SelectedMylistRow(params.showname)
                self.assertEqual(params.result, instance.name)

        self.assertEqual("*:", MylistRow.NEW_MARK)
        with self.assertRaises(FrozenInstanceError):
            instance = MylistRow("投稿者1さんの投稿動画")
            instance._name = "invalid"

    def test_is_new_mark(self):
        with ExitStack() as stack:
            mock_without_new_mark_name = stack.enter_context(
                patch("NNMM.process.value_objects.mylist_row.MylistRow.without_new_mark_name")
            )
            showname = "投稿者1さんの投稿動画"
            mock_without_new_mark_name.side_effect = lambda: showname
            instance = MylistRow(showname)
            actual = instance.is_new_mark()
            self.assertFalse(actual)

            mock_without_new_mark_name.side_effect = lambda: "*:" + showname
            instance = MylistRow("*:" + showname)
            actual = instance.is_new_mark()
            self.assertTrue(actual)

    def test_without_new_mark_name(self):
        showname = "投稿者1さんの投稿動画"
        instance = MylistRow(showname)
        actual = instance.without_new_mark_name()
        self.assertEqual(showname, actual)

        showname = "*:投稿者1さんの投稿動画"
        instance = MylistRow(showname)
        actual = instance.without_new_mark_name()
        self.assertEqual(showname[2:], actual)

    def test_with_new_mark_name(self):
        with ExitStack() as stack:
            mock_without_new_mark_name = stack.enter_context(
                patch("NNMM.process.value_objects.mylist_row.MylistRow.without_new_mark_name")
            )
            showname = "投稿者1さんの投稿動画"
            mock_without_new_mark_name.side_effect = lambda: showname
            instance = MylistRow(showname)
            actual = instance.with_new_mark_name()
            self.assertEqual("*:" + showname, actual)

            showname = "*:投稿者1さんの投稿動画"
            mock_without_new_mark_name.side_effect = lambda: showname
            instance = MylistRow(showname)
            actual = instance.with_new_mark_name()
            self.assertEqual(showname, actual)

    def test_create(self):
        Params = namedtuple("Params", ["showname", "result"])
        params_list = [
            Params("投稿者1さんの投稿動画", "投稿者1さんの投稿動画"),
            Params("「マイリスト1」-投稿者1さんのマイリスト", "「マイリスト1」-投稿者1さんのマイリスト"),
            Params("*:投稿者1さんの投稿動画", "投稿者1さんの投稿動画"),
            Params(Showname("投稿者1さんの投稿動画"), "投稿者1さんの投稿動画"),
            Params("", "invalid"),
            Params(-1, "invalid"),
            Params("1", "invalid"),
        ]
        for params in params_list:
            if params.result == "invalid":
                with self.assertRaises((ValueError, TypeError)):
                    instance = MylistRow.create(params.showname)
            else:
                instance = MylistRow.create(params.showname)
                self.assertEqual(params.result, instance.name)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
