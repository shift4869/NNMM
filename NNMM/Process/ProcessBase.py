# coding: utf-8
from abc import ABC, abstractmethod
from logging import INFO, getLogger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from NNMM.MainWindow import MainWindow

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessBase(ABC):
    def __init__(self, log_sflag: bool, log_eflag: bool, process_name: str) -> None:
        self.log_sflag = log_sflag
        self.log_eflag = log_eflag
        self.process_name = process_name
        self.main_window = None

    @abstractmethod
    def run(self, mw: "MainWindow") -> int:
        return 0
