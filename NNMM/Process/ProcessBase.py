# coding: utf-8
from abc import ABC, abstractmethod
from logging import INFO, getLogger


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessBase(ABC):

    def __init__(self, log_sflag: bool, log_eflag: bool, process_name: str) -> None:
        self.log_sflag = log_sflag
        self.log_eflag = log_eflag
        self.process_name = process_name
        self.main_window = None

    @abstractmethod
    def Run(self, mw) -> int:
        # mwはMainWindowクラスを想定
        # アノテーションで記述すると循環参照になるため記述無し
        return 0
