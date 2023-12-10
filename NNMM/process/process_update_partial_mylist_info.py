from datetime import datetime, timedelta
from logging import INFO, getLogger

from NNMM.model import Mylist
from NNMM.process.process_update_mylist_info_base import ProcessUpdateMylistInfoBase, ProcessUpdateMylistInfoThreadDoneBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import interval_translate

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessUpdatePartialMylistInfo(ProcessUpdateMylistInfoBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        """一部（複数の）マイリストのマイリスト情報を更新するクラス

        Attributes:
            L_KIND (str): ログ出力用のメッセージベース
            E_DONE (str): 後続処理へのイベントキー
        """
        super().__init__(process_info)

        self.POST_PROCESS = ProcessUpdatePartialMylistInfoThreadDone
        self.L_KIND = "Partial mylist"
        self.E_DONE = "-PARTIAL_UPDATE_THREAD_DONE-"

    def get_target_mylist(self) -> list[Mylist]:
        """更新対象のマイリストを返す

        Notes:
            ProcessUpdatePartialMylistInfoにおいては対象は複数のマイリストとなる
            前回更新確認時からインターバル分だけ経過しているもののみ更新対象とする

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        result = []
        m_list = self.mylist_db.select()

        src_df = "%Y/%m/%d %H:%M"
        dst_df = "%Y-%m-%d %H:%M:%S"
        now_dst = datetime.now()
        try:
            for m in m_list:
                # 前回チェック時日時取得
                checked_dst = datetime.strptime(m["checked_at"], dst_df)
                # インターバル文字列取得
                interval_str = str(m["check_interval"])

                dt = interval_translate(interval_str) - 1
                if dt < -1:
                    # インターバル文字列解釈エラー
                    mylist_url = m["url"]
                    showname = m["showname"]
                    logger.error(f"{self.L_KIND} get_target_mylist failed, update interval setting is invalid :")
                    logger.error(f"\t{showname}")
                    logger.error(f"\t{mylist_url} : {interval_str}")
                    continue

                # 予測次回チェック日時取得
                predict_dst = checked_dst + timedelta(minutes=dt)

                # 現在日時が予測次回チェック日時を過ぎているなら更新対象とする
                if predict_dst < now_dst:
                    result.append(m)
        except (KeyError, ValueError):
            # マイリストオブジェクトのキーエラーなど
            logger.error(f"{self.L_KIND} get_target_mylist failed, KeyError.")
            return []

        return result


class ProcessUpdatePartialMylistInfoThreadDone(ProcessUpdateMylistInfoThreadDoneBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.L_KIND = "Partial mylist"


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
