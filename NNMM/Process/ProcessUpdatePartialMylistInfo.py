# coding: utf-8
from datetime import date, datetime, timedelta
from logging import INFO, getLogger


from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process.ProcessUpdateAllMylistInfo import *


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessUpdatePartialMylistInfo(ProcessUpdateAllMylistInfo):

    def __init__(self):
        super().__init__()

        # ログメッセージ
        self.L_START = "Partial mylist update starting."
        self.L_GETTING_ELAPSED_TIME = "Partial getting done elapsed time"
        self.L_UPDATE_ELAPSED_TIME = "Partial update done elapsed time"

        # イベントキー
        self.E_PROGRESS = "-PARTIAL_UPDATE_THREAD_PROGRESS-"
        self.E_DONE = "-PARTIAL_UPDATE_THREAD_DONE-"

    def GetTargetMylist(self):
        """更新対象のマイリストを返す

        Returns:
            list[Mylist]: 更新対象のマイリストのリスト
        """
        result = []
        m_list = self.mylist_db.Select()

        # 前回更新確認時からインターバル分だけ経過しているもののみ更新対象とする
        td_format = "%Y/%m/%d %H:%M"
        dts_format = "%Y-%m-%d %H:%M:%S"
        now_dst = datetime.now()
        for m in m_list:
            checked_dst = datetime.strptime(m["checked_at"], dts_format)
            interval_str = str(m["check_interval"])
            dt = IntervalTranslation(interval_str) - 1
            if dt < -1:
                # インターバル文字列解釈エラー
                logger.error(f"update interval setting is invalid : {interval_str}")
                continue
            predict_dst = checked_dst + timedelta(minutes=dt)
            if predict_dst < now_dst:
                result.append(m)

        return result


# class ProcessUpdatePartialMylistInfoThreadProgress(ProcessUpdateAllMylistInfoThreadProgress):

#     def __init__(self):
#         super().__init__()

#         # イベントキー
#         self.E_PROGRESS = "-PARTIAL_UPDATE_THREAD_PROGRESS-"


class ProcessUpdatePartialMylistInfoThreadDone(ProcessUpdateAllMylistInfoThreadDone):

    def __init__(self):
        super().__init__()

        # ログメッセージ
        self.L_FINISH = "Partial mylist update finished."


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
