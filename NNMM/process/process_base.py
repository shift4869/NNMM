from abc import ABC, abstractmethod

from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result


class ProcessBase(ABC):
    def __init__(self, process_info: ProcessInfo) -> None:
        if not isinstance(process_info, ProcessInfo):
            raise ValueError("process_info must be ProcessInfo.")
        self.process_info = process_info
        self.name = process_info.name
        self.window = process_info.window
        self.values = process_info.values
        self.mylist_db = process_info.mylist_db
        self.mylist_info_db = process_info.mylist_info_db

    @abstractmethod
    def run(self) -> Result:
        raise NotImplementedError
