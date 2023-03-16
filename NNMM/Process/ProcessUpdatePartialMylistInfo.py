# coding: utf-8
from datetime import datetime, timedelta
from logging import INFO, getLogger

from NNMM.GuiFunction import *
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.Process import ProcessUpdateMylistInfoBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessUpdatePartialMylistInfo(ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoBase):

    def __init__(self):
        """一部（複数の）マイリストのマイリスト情報を更新するクラス

        Attributes:
            L_KIND (str): ログ出力用のメッセージベース
            E_DONE (str): 後続処理へのイベントキー
        """
        super().__init__(True, False, "複数マイリスト内容更新")

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
        # 属性チェック
        if not hasattr(self, "mylist_db"):
            logger.error(f"{self.L_KIND} GetTargetMylist failed, attribute error.")
            return []

        result = []
        m_list = self.mylist_db.Select()

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
                    logger.error(f"{self.L_KIND} GetTargetMylist failed, update interval setting is invalid :")
                    logger.error(f"\t{mylist_url} : {interval_str}")
                    continue

                # 予測次回チェック日時取得
                predict_dst = checked_dst + timedelta(minutes=dt)

                # 現在日時が予測次回チェック日時を過ぎているなら更新対象とする
                if predict_dst < now_dst:
                    result.append(m)
        except (KeyError, ValueError):
            # マイリストオブジェクトのキーエラーなど
            logger.error(f"{self.L_KIND} GetTargetMylist failed, KeyError.")
            return []

        return result


class ProcessUpdatePartialMylistInfoThreadDone(ProcessUpdateMylistInfoBase.ProcessUpdateMylistInfoThreadDoneBase):

    def __init__(self):
        super().__init__(False, True, "複数マイリスト内容更新")
        self.L_KIND = "Partial mylist"


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.run()
