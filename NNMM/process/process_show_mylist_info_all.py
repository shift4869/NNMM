from logging import INFO, getLogger

from NNMM.process.process_base import ProcessBase

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessShowMylistInfoAll(ProcessBase):

    def __init__(self):
        super().__init__(True, True, "最近追加された動画を一覧表示")

    def run(self, mw):
        """すべてのマイリストを横断的に探索し、含まれる動画情報レコードを100件まで表示する

        Notes:
            "全動画表示::-MR-"
            マイリスト右クリックで「全動画表示」が選択された場合
            動画IDの数値で判定し、降順に動画情報レコードを100件まで表示する

        Todo:
            最新のレコードを表示するためのソート順を考える
                動画ID→予約投稿を考えると投稿日時順とは必ずしも一致しない
                投稿日時→投コメ修正などの更新でも日時が更新されてしまう
            初回格納時の投稿日時のみ保持するようにし、
            それ以降投稿日時が上書きされないようにした上で投稿日時順ソートが有効か

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 成功時0, エラー時-1
        """
        logger.info("ShowMylistInfoAll start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("ShowMylistInfoAll failed, argument error.")
            return -1

        # 現在選択中のマイリストがある場合そのindexを保存
        index = 0
        if self.window["-LIST-"].get_indexes():
            index = self.window["-LIST-"].get_indexes()[0]

        # 全動画情報を取得
        NUM = 100
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url"]
        m_list = self.mylist_info_db.select()  # DB内にある全ての動画情報を取得
        records = sorted(m_list, key=lambda x: int(x["video_id"][2:]), reverse=True)[0:NUM]  # 最大100要素までのスライス
        def_data = []
        for i, r in enumerate(records):
            a = [i + 1, r["video_id"], r["title"], r["username"], r["status"], r["uploaded_at"], r["registered_at"], r["video_url"], r["mylist_url"]]
            def_data.append(a)

        # 右上のマイリストURLは空白にする
        self.window["-INPUT1-"].update(value="")

        # テーブル更新
        # update_table_paneはリフレッシュには使えるが初回は別に設定が必要なため使用できない
        self.window["-LIST-"].update(set_to_index=index)
        self.window["-TABLE-"].update(values=def_data)
        if len(def_data) > 0:
            self.window["-TABLE-"].update(select_rows=[0])
        # 1行目は背景色がリセットされないので個別に指定してdefaultの色で上書き
        self.window["-TABLE-"].update(row_colors=[(0, "", "")])

        logger.info("ShowMylistInfoAll success.")
        return 0


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()()
    mw.run()
