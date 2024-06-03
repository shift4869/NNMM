from concurrent.futures import ThreadPoolExecutor
from logging import INFO, getLogger

from nnmm.mylist_db_controller import MylistDBController
from nnmm.mylist_info_db_controller import MylistInfoDBController
from nnmm.process.update_mylist.executor_base import ExecutorBase
from nnmm.process.update_mylist.value_objects.payload_list import PayloadList
from nnmm.process.update_mylist.value_objects.typed_mylist import TypedMylist
from nnmm.process.update_mylist.value_objects.typed_video import TypedVideo
from nnmm.process.update_mylist.value_objects.typed_video_list import TypedVideoList
from nnmm.process.value_objects.process_info import ProcessInfo
from nnmm.process.value_objects.table_row import Status
from nnmm.util import Result, get_now_datetime
from nnmm.video_info_fetcher.value_objects.fetched_video_info import FetchedVideoInfo

logger = getLogger(__name__)
logger.setLevel(INFO)


class DatabaseUpdater(ExecutorBase):
    """fetch 後の動画情報をDBに反映させる処理をマルチスレッドで起動する

    Attribute:
        payload_list (PayloadList): fetch 後のペイロードのリスト

    Returns:
        Result: DB更新に成功したら Result.success, 失敗時 Result.failed
    """

    payload_list: PayloadList

    def __init__(self, payload_list: PayloadList, process_info: ProcessInfo) -> None:
        """初期設定

        Args:
            payload_list (PayloadList): fetch 後のペイロードのリスト
            process_info (ProcessInfo): 画面更新用 process_info
        """
        super().__init__(process_info)
        if not isinstance(payload_list, PayloadList):
            raise ValueError("payload_list must be PayloadList.")
        self.payload_list = payload_list

    def execute(self) -> PayloadList:
        """DB更新を行う thread を起動する

        Returns:
            PayloadList: DB更新に用いたペイロードと、DB更新処理結果のResult
                         この返り値は呼び出し元では使用されない
        """
        result_buf = []
        all_index_num = len(self.payload_list)
        with ThreadPoolExecutor(max_workers=8, thread_name_prefix="np_thread") as executor:
            futures = []
            for payload in self.payload_list:
                mylist = payload.mylist
                video_list = payload.video_list
                fetched_info = payload.fetched_info
                future = executor.submit(self.execute_worker, mylist, video_list, fetched_info, all_index_num)
                futures.append((payload, future))
            result_buf = [(f[0], f[1].result()) for f in futures]
        return result_buf

    def execute_worker(self, *argv) -> FetchedVideoInfo | Result:
        """具体的なDB更新を担当するワーカー

        TODO:
            処理を分割したい

        Returns:
            FetchedVideoInfo | Result: Result のみ返す
                                       DB更新に成功したら Result.success, 失敗時 Result.failed
        """
        mylist: TypedMylist = argv[0]
        video_list: TypedVideoList = argv[1]
        fetched_info: FetchedVideoInfo | Result = argv[2]
        all_index_num: int = argv[3]

        # マルチスレッド内では各々のスレッドごとに新しくDBセッションを張る
        mylist_db = MylistDBController(self.mylist_db.dbname)
        mylist_info_db = MylistInfoDBController(self.mylist_info_db.dbname)

        mylist_url = mylist.url.non_query_url
        if fetched_info == Result.failed:
            # 新規マイリスト取得でレンダリングが失敗した場合など
            logger.info(mylist_url + f" : no records ... ({self.done_count}/{all_index_num}).")
            mylist_db.update_check_failed_count(mylist_url)
            return Result.failed
        else:
            # マイリスト更新に成功しているのでカウントをリセット
            mylist_db.reset_check_failed_count(mylist_url)

        # fetched_info から TypedVideoList を作成
        dst = get_now_datetime()
        prev_video_list: TypedVideoList = video_list
        fetched_info_dict_list = fetched_info._make_result_dict()
        now_video_list = TypedVideoList.create([
            TypedVideo.create(fetched_info_dict | {"id": fetched_info_dict["no"], "created_at": dst})
            for fetched_info_dict in fetched_info_dict_list
        ])

        # 更新前の動画idリストの設定
        prev_videoid_list = [v.video_id.id for v in prev_video_list]

        # 更新後の動画idリストの設定
        now_videoid_list = [v.video_id.id for v in now_video_list]

        # 状況ステータスを調べる
        status_check_list = []
        add_new_video_flag = False
        for n in now_videoid_list:
            if n in prev_videoid_list:
                # 以前から保持していた動画が取得された場合->ステータスも保持する
                s = [p.status for p in prev_video_list if p.video_id.id == n]
                status_check_list.append(s[0])
            else:
                # 新規に動画が追加された場合->"未視聴"に設定
                status_check_list.append(Status.not_watched)
                add_new_video_flag = True

        # 状況ステータス設定
        for index, status in enumerate(status_check_list):
            now_video_list[index] = now_video_list[index].replace_from_typed_value(status=status)

        # THINK::マイリスト作成者名が変わっていた場合に更新する方法
        # usernameが変更されていた場合
        # 作成したばかり等で登録件数0のマイリストの場合は除く
        # if now_video_list:
        #     # usernameが変更されていた場合
        #     now_username = now_video_list[0].get("username")
        #     if prev_username != now_username:
        #         # マイリストの名前を更新する
        #         mylist_db.update_username(mylist_url, now_username)
        #         # 格納済の動画情報の投稿者名を更新する
        #         mylist_info_db.update_username_in_mylist(mylist_url, now_username)
        #         logger.info(f"Mylist username changed , {prev_username} -> {now_username}")

        # DBに格納
        records = [m.to_dict() for m in now_video_list]
        mylist_info_db.upsert_from_list(records)

        # マイリストの更新確認日時更新
        # 新しい動画情報が追加されたかに関わらずchecked_atを更新する
        mylist_db.update_checked_at(mylist_url, dst)

        # マイリストの更新日時更新
        # 新しい動画情報が追加されたときにupdated_atを更新する
        if add_new_video_flag:
            mylist_db.update_updated_at(mylist_url, dst)

        # プログレス表示
        with self.lock:
            self.done_count = self.done_count + 1
            p_str = f"更新中({self.done_count}/{all_index_num})"
            self.window["-INPUT2-"].update(value=p_str)
            logger.info(mylist_url + f" : update done ... ({self.done_count}/{all_index_num}).")
        return Result.success


if __name__ == "__main__":
    from NNMM import main_window

    mw = main_window.MainWindow()
    mw.run()
