from logging import INFO, getLogger

from NNMM.model import Mylist
from NNMM.process.update_mylist.base import Base, ThreadDoneBase
from NNMM.process.value_objects.process_info import ProcessInfo

logger = getLogger(__name__)
logger.setLevel(INFO)


class Every(Base):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.post_process = EveryThreadDone
        self.L_KIND = "Every mylist"
        self.E_DONE = "-ALL_UPDATE_THREAD_DONE-"

    def get_target_mylist(self) -> list[dict]:
        """更新対象のマイリストを返す

        Note:
            Everyにおいては対象はすべてのマイリストとなる

        Returns:
            list[dict]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        m_list = self.mylist_db.select()
        return m_list


class EveryThreadDone(ThreadDoneBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.L_KIND = "Every mylist"


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
