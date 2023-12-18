from logging import INFO, getLogger

from NNMM.model import Mylist
from NNMM.process.update_mylist.base import Base, ThreadDoneBase
from NNMM.process.value_objects.process_info import ProcessInfo

logger = getLogger(__name__)
logger.setLevel(INFO)


class Single(Base):
    def __init__(self, process_info: ProcessInfo) -> None:
        """マイリスト情報を更新する

        Notes:
            "-UPDATE-"
            右上の更新ボタンが押された場合
            Singleは現在表示されている単一のマイリストについて動画情報を更新する
        """
        super().__init__(process_info)

        # ログメッセージ
        self.L_KIND = "Mylist"
        # イベントキー
        self.E_DONE = "-UPDATE_THREAD_DONE-"

    def get_target_mylist(self) -> list[Mylist]:
        """更新対象のマイリストを返す

        Notes:
            Singleにおいては対象は単一のマイリストとなる

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        mylist_url = self.values["-INPUT1-"]
        if mylist_url == "":
            return []

        m_list = self.mylist_db.select_from_url(mylist_url)
        return m_list


class SingleThreadDone(ThreadDoneBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.L_KIND = "Mylist"


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
