from datetime import datetime, timedelta
from logging import INFO, getLogger

from NNMM.process.update_mylist.base import Base, ThreadDoneBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import interval_translate

logger = getLogger(__name__)
logger.setLevel(INFO)


class Partial(Base):
    def __init__(self, process_info: ProcessInfo) -> None:
        """一部（複数の）マイリストのマイリスト情報を更新するクラス

        Attributes:
            L_KIND (str): ログ出力用のメッセージベース
            E_DONE (str): 後続処理へのイベントキー
        """
        super().__init__(process_info)

        self.post_process = PartialThreadDone
        self.L_KIND = "Partial mylist"
        self.E_DONE = "-PARTIAL_UPDATE_THREAD_DONE-"

    def get_target_mylist(self) -> list[dict]:
        """更新対象のマイリストを返す

        Notes:
            Partialにおいては対象は複数のマイリストとなる
            前回更新確認時からインターバル分だけ経過している、かつ
            更新確認失敗カウントが MAX_CHECK_FAILED_COUNT 未満 のマイリストのみ更新対象とする

        Returns:
            list[dict]: 更新対象のマイリストのリスト、エラー時空リスト
        """
        MAX_CHECK_FAILED_COUNT = 10
        result = []
        m_list = self.mylist_db.select()

        src_df = "%Y/%m/%d %H:%M"
        dst_df = "%Y-%m-%d %H:%M:%S"
        now_dst = datetime.now()
        try:
            for m in m_list:
                checked_dst = datetime.strptime(m["checked_at"], dst_df)
                interval_str = str(m["check_interval"])
                check_failed_count = int(m["check_failed_count"])

                if check_failed_count >= MAX_CHECK_FAILED_COUNT:
                    # 更新確認失敗カウントが MAX_CHECK_FAILED_COUNT 以上なら更新対象としない
                    # この条件に当てはまるマイリストはPartialにおいては更新が停止したor削除されたマイリストとみなす
                    # このマイリストを再び更新対象としたい場合はDBの check_failed_count を手動更新すること
                    mylist_url = m["url"]
                    showname = m["showname"]
                    warning_str = "{} get_target_mylist warning, exceed MAX_CHECK_FAILED_COUNT retry for {} : {}."
                    logger.warning(warning_str.format(self.L_KIND, mylist_url, showname))
                    continue

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


class PartialThreadDone(ThreadDoneBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)
        self.L_KIND = "Partial mylist"


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
