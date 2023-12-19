from abc import ABC, abstractmethod


class ExecutorBase(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def execute(self, *argv) -> None:
        pass

    @abstractmethod
    def execute_worker(self, *argv) -> None:
        pass


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
