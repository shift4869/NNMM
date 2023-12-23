import threading
from abc import ABC, abstractmethod

import PySimpleGUI as sg

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController
from NNMM.process.update_mylist.value_objects.payload_list import PayloadList
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result
from NNMM.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo


class ExecutorBase(ABC):
    process_info: ProcessInfo
    window: sg.Window
    values: dict
    mylist_db: MylistDBController
    mylist_info_db: MylistInfoDBController
    lock: threading.Lock
    done_count: int

    def __init__(self, process_info: ProcessInfo) -> None:
        if not isinstance(process_info, ProcessInfo):
            raise ValueError("process_info must be ProcessInfo.")
        self.process_info = process_info
        self.window = process_info.window
        self.values = process_info.values
        self.mylist_db = process_info.mylist_db
        self.mylist_info_db = process_info.mylist_info_db

        self.lock = threading.Lock()
        self.done_count = 0

    @abstractmethod
    def execute(self) -> PayloadList:
        raise NotImplementedError

    @abstractmethod
    def execute_worker(self, *argv) -> FetchedVideoInfo | Result:
        raise NotImplementedError


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
