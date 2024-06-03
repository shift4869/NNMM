import re
from dataclasses import dataclass
from typing import Literal, Self


@dataclass(frozen=True)
class CheckInterval:
    """更新間隔"""

    _amount: int
    _unit: Literal["分", "時間", "日", "週間", "ヶ月"]

    UNIT = ["分", "時間", "日", "週間", "ヶ月"]

    def __post_init__(self) -> None:
        if not isinstance(self._amount, int):
            raise ValueError("_amount must be int.")
        if not isinstance(self._unit, str):
            raise ValueError("_unit must be unit literal string.")

        if self._amount < 1:
            raise ValueError("_amount must be _amount >= 1.")
        if self._unit not in self.UNIT:
            raise ValueError(f"_unit must be in [{", ".join(self.UNIT)}].")

    @property
    def interval_str(self) -> str:
        return f"{self._amount}{self._unit}"

    def get_minute_amount(self) -> int:
        """インターバルを分[min]を表す数値として解釈して返す

        Returns:
            int: 成功時 分[min]を表す数値、失敗時 -1
        """
        interval_str: str = self.interval_str
        pattern = r"^([0-9]+)分$"
        if m := re.findall(pattern, interval_str):
            return int(m[0])

        pattern = r"^([0-9]+)時間$"
        if m := re.findall(pattern, interval_str):
            return int(m[0]) * 60

        pattern = r"^([0-9]+)日$"
        if m := re.findall(pattern, interval_str):
            return int(m[0]) * 60 * 24

        pattern = r"^([0-9]+)週間$"
        if m := re.findall(pattern, interval_str):
            return int(m[0]) * 60 * 24 * 7

        pattern = r"^([0-9]+)ヶ月$"
        if m := re.findall(pattern, interval_str):
            return int(m[0]) * 60 * 24 * 31  # 月は正確ではない28,29,30,31
        return -1

    @classmethod
    def split(cls, interval_str: str) -> tuple[int, str]:
        """インターバル文字列を数値と単位に分離する

        Args:
            interval_str (str): インターバルを表す文字列候補

        Raises
            ValueError: 数値と単位の分離に失敗

        Returns:
            (int, str): (amount, unit)
        """
        pattern = r"^([0-9]+)([^0-9]+)$"
        if m := re.findall(pattern, interval_str):
            amount = int(m[0][0])
            unit = str(m[0][1])
            if not (amount >= 1 and unit in cls.UNIT):
                message = f"amount or unit is invalid value: (amount, unit) = ({amount, unit})."
                raise ValueError(message)
            return amount, unit
        raise ValueError("check_interval cannot split.")

    @classmethod
    def can_split(cls, interval_str: str) -> bool:
        """インターバルの数値と単位に分離ができるか調べる

        Args:
            interval_str (str): インターバルを表す文字列候補

        Returns:
            bool: 数値と単位に分離ができる形式ならばTrue、それ以外ならばFalse
        """
        pattern = r"^([0-9]+)([^0-9]+)$"
        try:
            if m := re.findall(pattern, interval_str):
                amount = int(m[0][0])
                unit = str(m[0][1])
                return amount >= 1 and unit in cls.UNIT
        except Exception:
            pass
        return False

    @classmethod
    def create(cls, interval_str: str) -> Self:
        if not cls.can_split(interval_str):
            raise ValueError("interval_str cannot split.")
        amount, unit = cls.split(interval_str)
        return CheckInterval(amount, unit)


if __name__ == "__main__":
    interval_str_list = [
        "1分",
        "2分",
        "10分",
        "1時間",
        "1日",
        "1週間",
        "1ヶ月",
        "1invalid",
        "0分",
        "nm12346578",
        "",
        -1,
    ]

    for interval_str in interval_str_list:
        try:
            check_interval = CheckInterval.create(interval_str)
            print(check_interval)
            print(check_interval.interval_str)
            print(check_interval.get_minute_amount())
        except ValueError as e:
            print(e.args[0])
