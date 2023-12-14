import re
from logging import INFO, getLogger

from NNMM.process.process_base import ProcessBase
from NNMM.process.value_objects.process_info import ProcessInfo
from NNMM.util import Result, popup_get_text, update_mylist_pane, update_table_pane

logger = getLogger(__name__)
logger.setLevel(INFO)


class ProcessMylistSearch(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト名でマイリストを検索

        Notes:
            "検索（マイリスト）::-MR-"
            マイリスト右クリックで「検索（マイリスト）」が選択された場合
            入力されたマイリスト名を持つマイリストをハイライト表示する

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("MylistSearch start.")

        pattern = popup_get_text("マイリスト名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("MylistSearch is canceled or target word is null.")
            return Result.failed

        logger.info(f"search word -> {pattern}.")

        # 現在マイリストが選択中の場合indexを保存
        index = 0
        if self.window["-LIST-"].get_indexes():
            index = self.window["-LIST-"].get_indexes()[0]

        # マイリスト画面表示更新
        NEW_MARK = "*:"
        # list_data = self.window["-LIST-"].Values
        m_list = self.mylist_db.select()
        include_new_index_list = []
        match_index_list = []
        for i, m in enumerate(m_list):
            if m["is_include_new"]:
                m["showname"] = NEW_MARK + m["showname"]
                include_new_index_list.append(i)
            if re.findall(pattern, m["showname"]):
                match_index_list.append(i)
                index = i  # 更新後にスクロールするインデックスを更新
        list_data = [m["showname"] for m in m_list]
        self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        # 強調したいindexのみ適用すればそれ以外はデフォルトになる
        for i in include_new_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # 検索でヒットした項目の背景色とテキスト色を変更する
        for i in match_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light goldenrod")

        # indexをセットしてスクロール
        # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
        # window["-LIST-"].update(scroll_to_index=index)
        self.window["-LIST-"].Widget.see(index)
        self.window["-LIST-"].update(set_to_index=index)

        # 検索結果表示
        if len(match_index_list) > 0:
            logger.info(f"search result -> {len(match_index_list)} mylist(s) found.")
            self.window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing mylist(s) found.")
            self.window["-INPUT2-"].update(value="該当なし")

        logger.info("MylistSearch success.")
        return Result.success


class ProcessMylistSearchFromVideo(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリストの中に含んでいる動画名でマイリストを検索

        Notes:
            "検索（動画名）::-MR-"
            マイリスト右クリックで「検索（動画名）」が選択された場合
            入力された動画名を持つ動画を含むマイリストをハイライト表示する

        Todo:
            動画テーブルを表示させて動画レコードまでハイライトする

        Returns:
            Result: 成功時success, エラー時failed
        """
        logger.info("MylistSearchFromVideo start.")

        pattern = popup_get_text("動画名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("MylistSearchFromVideo is canceled or target word is null.")
            return

        logger.info(f"search word -> {pattern}.")

        # 現在マイリストが選択中の場合indexを保存
        index = 0
        if self.window["-LIST-"].get_indexes():
            index = self.window["-LIST-"].get_indexes()[0]

        # マイリスト画面表示更新
        NEW_MARK = "*:"
        list_data = self.window["-LIST-"].Values
        m_list = self.mylist_db.select()
        include_new_index_list = []
        match_index_list = []
        for i, m in enumerate(m_list):
            # 新着マイリストチェック
            if m["is_include_new"]:
                m["showname"] = NEW_MARK + m["showname"]
                include_new_index_list.append(i)

            # マイリスト内の動画情報を探索
            mylist_url = m["url"]
            records = self.mylist_info_db.select_from_mylist_url(mylist_url)
            for r in records:
                if re.findall(pattern, r["title"]):
                    match_index_list.append(i)
                    index = i  # 更新後にスクロールするインデックスを更新
        list_data = [m["showname"] for m in m_list]
        self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        # update(values=list_data)で更新されるとデフォルトに戻る？
        # 強調したいindexのみ適用すればそれ以外はデフォルトになる
        for i in include_new_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # 検索でヒットした項目の背景色とテキスト色を変更する
        for i in match_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light goldenrod")

        # indexをセットしてスクロール
        # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
        # window["-LIST-"].update(scroll_to_index=index)
        self.window["-LIST-"].Widget.see(index)
        self.window["-LIST-"].update(set_to_index=index)

        # 検索結果表示
        if len(match_index_list) > 0:
            logger.info(f"search result -> {len(match_index_list)} mylist(s) found.")
            self.window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing mylist(s) found.")
            self.window["-INPUT2-"].update(value="該当なし")

        logger.info("MylistSearchFromVideo success.")
        return


class ProcessMylistSearchFromMylistURL(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリストURLでマイリストを検索

        Notes:
            "検索（URL）::-MR-"
            マイリスト右クリックで「検索（URL）」が選択された場合
            入力されたURLをマイリストURLとして持つマイリストをハイライト表示する
        """
        logger.info("MylistSearchFromMylistURL start.")

        search_mylist_url = popup_get_text("マイリストURL入力（完全一致）")
        if search_mylist_url is None or search_mylist_url == "":
            logger.info("MylistSearchFromMylistURL is canceled or target word is null.")
            return

        logger.info(f"search word -> {search_mylist_url}.")

        # 現在マイリストが選択中の場合indexを保存
        index = 0
        if self.window["-LIST-"].get_indexes():
            index = self.window["-LIST-"].get_indexes()[0]

        # マイリスト画面表示更新
        NEW_MARK = "*:"
        list_data = self.window["-LIST-"].Values
        m_list = self.mylist_db.select()
        include_new_index_list = []
        match_index_list = []
        for i, m in enumerate(m_list):
            # 新着マイリストチェック
            if m["is_include_new"]:
                m["showname"] = NEW_MARK + m["showname"]
                include_new_index_list.append(i)

            # マイリスト内の動画情報を探索
            if search_mylist_url == m["url"]:
                match_index_list.append(i)
                index = i  # 更新後にスクロールするインデックスを更新
        list_data = [m["showname"] for m in m_list]
        self.window["-LIST-"].update(values=list_data)

        # 新着マイリストの背景色とテキスト色を変更する
        # update(values=list_data)で更新されるとデフォルトに戻る？
        # 強調したいindexのみ適用すればそれ以外はデフォルトになる
        for i in include_new_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

        # 検索でヒットした項目の背景色とテキスト色を変更する
        for i in match_index_list:
            self.window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light goldenrod")

        # indexをセットしてスクロール
        # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
        # window["-LIST-"].update(scroll_to_index=index)
        self.window["-LIST-"].Widget.see(index)
        self.window["-LIST-"].update(set_to_index=index)

        # 検索結果表示
        if len(match_index_list) > 0:
            logger.info(f"search result -> {len(match_index_list)} mylist(s) found.")
            self.window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing mylist(s) found.")
            self.window["-INPUT2-"].update(value="該当なし")

        logger.info("MylistSearchFromMylistURL success.")
        return


class ProcessVideoSearch(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリストの中に含んでいる動画名でマイリストを検索

        Notes:
            "検索（動画名）::-TR-"
            動画テーブル右クリックで「検索（動画名）」が選択された場合
            現在表示中の動画テーブルから入力された動画名を持つ動画をハイライト表示する
        """
        logger.info("VideoSearch start.")

        # 検索対象ワードをユーザーに問い合わせる
        pattern = popup_get_text("動画名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("VideoSearch is canceled or target word is null.")
            return

        logger.info(f"search word -> {pattern}.")

        # 現在動画テーブルが選択中の場合indexを保存
        index = 0
        if self.values["-TABLE-"]:
            index = min([int(v) for v in self.values["-TABLE-"]])

        # マイリスト内の動画情報を探索
        # records = self.mylist_info_db.select_from_mylist_url(mylist_url)
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url"]
        records = self.window["-TABLE-"].Values  # 現在のtableの全リスト
        match_index_list = []
        for i, r in enumerate(records):
            if re.findall(pattern, r[2]):
                match_index_list.append(i)
                index = i  # 更新後にスクロールするインデックスを更新

        # 検索でヒットした項目の背景色とテキスト色を変更する
        # for i in match_index_list:
            # self.window["-TABLE-"].Widget.itemconfig(i, fg="black", bg="light goldenrod")
        self.window["-TABLE-"].update(row_colors=[(i, "black", "light goldenrod") for i in match_index_list])

        # indexをセットしてスクロール
        self.window["-TABLE-"].Widget.see(index + 1)
        if match_index_list:
            self.window["-TABLE-"].update(select_rows=match_index_list)
        else:
            self.window["-TABLE-"].update(select_rows=[index])

        # 検索結果表示
        if len(match_index_list) > 0:
            logger.info(f"search result -> {len(match_index_list)} record(s) found.")
            self.window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing record found.")
            self.window["-INPUT2-"].update(value="該当なし")

        logger.info("VideoSearch success.")
        return


class ProcessMylistSearchClear(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト表示のハイライトを解除する

        Notes:
            "強調表示を解除::-MR-"
            マイリスト右クリックで「強調表示を解除」が選択された場合
            現在表示中のマイリストの表示をもとに戻す
        """
        logger.info("MylistSearchClear start.")

        update_mylist_pane(self.window, self.mylist_db)

        logger.info("MylistSearchClear success.")
        return


class ProcessVideoSearchClear(ProcessBase):
    def __init__(self, process_info: ProcessInfo) -> None:
        super().__init__(process_info)

    def run(self) -> Result:
        """マイリスト表示のハイライトを解除する

        Notes:
            "強調表示を解除::-TR-"
            動画テーブル右クリックで「強調表示を解除」が選択された場合
            現在表示中の動画テーブルの表示をもとに戻す
        """
        logger.info("VideoSearchClear start.")

        # マイリストURL取得
        # 右上のテキストボックスから取得する
        # 「動画をすべて表示」している場合は空文字列になる可能性がある
        # update_table_paneはmylist_urlが空文字列でも処理が可能
        mylist_url = self.window["-INPUT1-"].get()
        update_table_pane(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info("VideoSearchClear success.")
        return


if __name__ == "__main__":
    from NNMM import main_window
    mw = main_window.MainWindow()
    mw.run()
