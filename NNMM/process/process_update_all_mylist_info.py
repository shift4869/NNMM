from logging import INFO, getLogger

from NNMM.model import Mylist
from NNMM.process.process_update_mylist_info_base import ProcessUpdateMylistInfoBase, ProcessUpdateMylistInfoThreadDoneBase
from NNMM.process.value_objects.process_info import ProcessInfo

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessUpdateAllMylistInfo(ProcessUpdateMylistInfoBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.POST_PROCESS = ProcessUpdateAllMylistInfoThreadDone
        self.L_KIND = "All mylist"
        self.E_DONE = "-ALL_UPDATE_THREAD_DONE-"

    def get_target_mylist(self) -> list[Mylist]:
        """更新対象のマイリストを返す

        Note:
            ProcessUpdateAllMylistInfoにおいては対象はすべてのマイリストとなる

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        m_list = self.mylist_db.select()
        return m_list


class ProcessUpdateAllMylistInfoThreadDone(ProcessUpdateMylistInfoThreadDoneBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.L_KIND = "All mylist"


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
