from dataclasses import dataclass


@dataclass(frozen=True)
class CheckFailedCount:
    """更新確認失敗カウント"""

    _count: int

    def __post_init__(self) -> None:
        if not isinstance(self._count, int):
            raise ValueError("_count must be int.")

        if self._count < 0:
            raise ValueError("_count must be _amount >= 0.")


if __name__ == "__main__":
    for count in range(-1, 5):
        try:
            check_failed_count = CheckFailedCount(count)
            print(check_failed_count)
        except ValueError as e:
            print(e.args[0])
