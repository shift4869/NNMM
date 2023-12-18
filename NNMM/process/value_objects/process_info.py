from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

import PySimpleGUI as sg

if TYPE_CHECKING:
    from NNMM.main_window import MainWindow

from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController


@dataclass(frozen=True)
class ProcessInfo():
    name: str
    window: sg.Window
    values: dict
    mylist_db: MylistDBController
    mylist_info_db: MylistInfoDBController

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise ValueError("name must be str.")
        if not isinstance(self.window, sg.Window):
            raise ValueError("window must be sg.Window.")
        if not isinstance(self.values, dict):
            raise ValueError("values must be dict.")
        if not isinstance(self.mylist_db, MylistDBController):
            raise ValueError("mylist_db must be MylistDBController.")
        if not isinstance(self.mylist_info_db, MylistInfoDBController):
            raise ValueError("mylist_info_db must be MylistInfoDBController.")

    def __repr__(self) -> str:
        name_str = f"name={self.name}"
        window_str = f"window={id(self.window)}"
        values_str = f"values={id(self.values)}"
        mylist_db_str = f"mylist_db={id(self.mylist_db)}"
        mylist_info_db_str = f"mylist_info_db={id(self.mylist_info_db)}"
        return f"ProcessInfo({name_str}, {window_str}, {values_str}, {mylist_db_str}, {mylist_info_db_str})"

    @classmethod
    def create(cls, process_name: str, main_window: "MainWindow") -> Self:
        # if not isinstance(main_window, MainWindow):
        #     raise ValueError("main_window must be MainWindow.")
        if not hasattr(main_window, "window"):
            raise ValueError("main_window must have 'window' attribute.")
        if not hasattr(main_window, "values"):
            raise ValueError("main_window must have 'values' attribute.")
        if not hasattr(main_window, "mylist_db"):
            raise ValueError("main_window must have 'mylist_db' attribute.")
        if not hasattr(main_window, "mylist_info_db"):
            raise ValueError("main_window must have 'mylist_info_db' attribute.")

        return ProcessInfo(
            process_name,
            main_window.window,
            main_window.values,
            main_window.mylist_db,
            main_window.mylist_info_db,
        )


if __name__ == "__main__":
    mw = MainWindow()
    mw.values = {"-TABLE-": ["test"]}
    process_info = ProcessInfo.create("-TEST_PROCESS-", mw)
    print(repr(process_info))
