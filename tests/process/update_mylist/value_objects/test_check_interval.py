import sys
import unittest
from collections import namedtuple

from NNMM.process.update_mylist.value_objects.check_interval import CheckInterval


class TestCheckInterval(unittest.TestCase):
    def test_init(self):
        self.assertEqual(CheckInterval.UNIT, ["分", "時間", "日", "週間", "ヶ月"])
        Params = namedtuple("Params", ["amount", "unit"])
        params_list = [
            Params(15, "分"),
            Params(1, "時間"),
            Params(2, "日"),
            Params(3, "週間"),
            Params(4, "ヶ月"),
        ]
        for params in params_list:
            instance = CheckInterval(params.amount, params.unit)
            self.assertEqual(params.amount, instance._amount)
            self.assertEqual(params.unit, instance._unit)

        params_list = [
            Params(15, "invalid"),
            Params(-1, "分"),
            Params(0, "時間"),
            Params(15, -1),
            Params("1", "分"),
        ]
        for params in params_list:
            with self.assertRaises(ValueError):
                instance = CheckInterval(params.amount, params.unit)

    def test_interval_str(self):
        Params = namedtuple("Params", ["amount", "unit"])
        params_list = [
            Params(15, "分"),
            Params(1, "時間"),
            Params(2, "日"),
            Params(3, "週間"),
            Params(4, "ヶ月"),
        ]
        for params in params_list:
            instance = CheckInterval(params.amount, params.unit)
            self.assertEqual(f"{params.amount}{params.unit}", instance.interval_str)

    def test_get_min_amount(self):
        Params = namedtuple("Params", ["amount", "unit", "result"])
        params_list = [
            Params(15, "分", 15),
            Params(1, "時間", 1 * 60),
            Params(2, "日", 2 * 60 * 24),
            Params(3, "週間", 3 * 60 * 24 * 7),
            Params(4, "ヶ月", 4 * 60 * 24 * 31),
        ]
        for params in params_list:
            instance = CheckInterval(params.amount, params.unit)
            actual = instance.get_minute_amount()
            expect = params.result
            self.assertEqual(expect, actual)

        # 一旦正常にインスタンスを作ってから、
        # 不正な値を設定してget_min_amountを呼ぶ
        instance = CheckInterval(15, "分")
        object.__setattr__(instance, "_unit", "invalid")
        actual = instance.get_minute_amount()
        expect = -1
        self.assertEqual(expect, actual)

    def test_split(self):
        Params = namedtuple("Params", ["interval_str", "amount", "unit"])
        params_list = [
            Params("15分", 15, "分"),
            Params("1時間", 1, "時間"),
            Params("2日", 2, "日"),
            Params("3週間", 3, "週間"),
            Params("4ヶ月", 4, "ヶ月"),
        ]
        for params in params_list:
            interval_str = params.interval_str
            actual = CheckInterval.split(interval_str)
            expect = (params.amount, params.unit)
            self.assertEqual(expect, actual)

        with self.assertRaises(ValueError):
            actual = CheckInterval.split("0分")

        with self.assertRaises(ValueError):
            actual = CheckInterval.split("invalid")

    def test_can_split(self):
        Params = namedtuple("Params", ["interval_str", "result"])
        params_list = [
            Params("15分", True),
            Params("1時間", True),
            Params("2日", True),
            Params("3週間", True),
            Params("4ヶ月", True),
            Params("0分", False),
            Params("invalid", False),
        ]
        for params in params_list:
            interval_str = params.interval_str
            actual = CheckInterval.can_split(interval_str)
            expect = params.result
            self.assertEqual(expect, actual)

    def test_create(self):
        Params = namedtuple("Params", ["interval_str", "amount", "unit"])
        params_list = [
            Params("15分", 15, "分"),
            Params("1時間", 1, "時間"),
            Params("2日", 2, "日"),
            Params("3週間", 3, "週間"),
            Params("4ヶ月", 4, "ヶ月"),
        ]
        for params in params_list:
            interval_str = params.interval_str
            actual = CheckInterval.create(interval_str)
            self.assertEqual(params.amount, actual._amount)
            self.assertEqual(params.unit, actual._unit)

        error_interval_list = [
            "1invalid",
            "0分",
            "nm12346578",
            "",
            -1,
        ]
        for error_interval in error_interval_list:
            with self.assertRaises(ValueError):
                actual = CheckInterval.create(error_interval)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
