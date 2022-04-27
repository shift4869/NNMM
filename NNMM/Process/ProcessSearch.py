# coding: utf-8
import re
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *
from NNMM.Process import ProcessBase


logger = getLogger("root")
logger.setLevel(INFO)


class ProcessMylistSearch(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト検索（マイリスト名）")

    def Run(self, mw):
        """マイリスト名でマイリストを検索

        Notes:
            "検索（マイリスト）::-MR-"
            マイリスト右クリックで「検索（マイリスト）」が選択された場合
            入力されたマイリスト名を持つマイリストをハイライト表示する

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 処理成功した場合0, キャンセル時1, エラー時-1
        """
        logger.info("MylistSearch start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("MylistSearch failed, argument error.")
            return -1

        pattern = PopupGetText("マイリスト名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("MylistSearch is canceled or target word is null.")
            return 1

        logger.info(f"search word -> {pattern}.")

        # 現在マイリストが選択中の場合indexを保存
        index = 0
        if self.window["-LIST-"].get_indexes():
            index = self.window["-LIST-"].get_indexes()[0]

        # マイリスト画面表示更新
        NEW_MARK = "*:"
        list_data = self.window["-LIST-"].Values
        m_list = self.mylist_db.Select()
        include_new_index_list = []
        match_index_list = []
        for i, m in enumerate(m_list):
            if m["is_include_new"]:
                m["showname"] = NEW_MARK + m["showname"]
                include_new_index_list.append(i)
            if re.search(pattern, m["showname"]):
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
        return 0


class ProcessMylistSearchFromVideo(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト検索（動画名）")

    def Run(self, mw):
        """マイリストの中に含んでいる動画名でマイリストを検索

        Notes:
            "検索（動画名）::-MR-"
            マイリスト右クリックで「検索（動画名）」が選択された場合
            入力された動画名を持つ動画を含むマイリストをハイライト表示する

        Todo:
            動画テーブルを表示させて動画レコードまでハイライトする

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 処理成功した場合0, キャンセル時1, エラー時-1
        """
        logger.info("MylistSearchFromVideo start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("MylistSearchFromVideo failed, argument error.")
            return -1

        pattern = PopupGetText("動画名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("MylistSearchFromVideo is canceled or target word is null.")
            return 1

        logger.info(f"search word -> {pattern}.")

        # 現在マイリストが選択中の場合indexを保存
        index = 0
        if self.window["-LIST-"].get_indexes():
            index = self.window["-LIST-"].get_indexes()[0]

        # マイリスト画面表示更新
        NEW_MARK = "*:"
        list_data = self.window["-LIST-"].Values
        m_list = self.mylist_db.Select()
        include_new_index_list = []
        match_index_list = []
        for i, m in enumerate(m_list):
            # 新着マイリストチェック
            if m["is_include_new"]:
                m["showname"] = NEW_MARK + m["showname"]
                include_new_index_list.append(i)

            # マイリスト内の動画情報を探索
            mylist_url = m["url"]
            records = self.mylist_info_db.SelectFromMylistURL(mylist_url)
            for r in records:
                if re.search(pattern, r["title"]):
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
        return 0


class ProcessVideoSearch(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "動画検索")

    def Run(self, mw):
        """マイリストの中に含んでいる動画名でマイリストを検索

        Notes:
            "検索（動画名）::-TR-"
            動画テーブル右クリックで「検索（動画名）」が選択された場合
            現在表示中の動画テーブルから入力された動画名を持つ動画をハイライト表示する

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 処理成功した場合0, キャンセル時1, エラー時-1
        """
        logger.info("VideoSearch start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("VideoSearch failed, argument error.")
            return -1

        # 検索対象ワードをユーザーに問い合わせる
        pattern = PopupGetText("動画名検索（正規表現可）")
        if pattern is None or pattern == "":
            logger.info("VideoSearch is canceled or target word is null.")
            return 1

        logger.info(f"search word -> {pattern}.")

        # 現在動画テーブルが選択中の場合indexを保存
        index = 0
        if self.values["-TABLE-"]:
            index = min([int(v) for v in self.values["-TABLE-"]])

        # マイリスト内の動画情報を探索
        # records = self.mylist_info_db.SelectFromMylistURL(mylist_url)
        table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
        table_cols = ["no", "video_id", "title", "username", "status", "uploaded_at", "registered_at", "video_url", "mylist_url"]
        records = self.window["-TABLE-"].Values  # 現在のtableの全リスト
        match_index_list = []
        for i, r in enumerate(records):
            if re.search(pattern, r[2]):
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
        return 0


class ProcessMylistSearchClear(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "強調表示を解除")

    def Run(self, mw):
        """マイリスト表示のハイライトを解除する

        Notes:
            "強調表示を解除::-MR-"
            マイリスト右クリックで「強調表示を解除」が選択された場合
            現在表示中のマイリストの表示をもとに戻す

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 処理成功した場合0, エラー時-1
        """
        logger.info("MylistSearchClear start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.mylist_db = mw.mylist_db
        except AttributeError:
            logger.error("MylistSearchClear failed, argument error.")
            return -1

        UpdateMylistShow(self.window, self.mylist_db)

        logger.info("MylistSearchClear success.")
        return 0


class ProcessVideoSearchClear(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "強調表示を解除")

    def Run(self, mw):
        """マイリスト表示のハイライトを解除する

        Notes:
            "強調表示を解除::-TR-"
            動画テーブル右クリックで「強調表示を解除」が選択された場合
            現在表示中の動画テーブルの表示をもとに戻す

        Args:
            mw (MainWindow): メインウィンドウオブジェクト

        Returns:
            int: 処理成功した場合0, エラー時-1
        """
        logger.info("VideoSearchClear start.")

        # 引数チェック
        try:
            self.window = mw.window
            self.values = mw.values
            self.mylist_db = mw.mylist_db
            self.mylist_info_db = mw.mylist_info_db
        except AttributeError:
            logger.error("VideoSearchClear failed, argument error.")
            return -1

        # マイリストURL取得
        # 右上のテキストボックスから取得する
        # 「動画をすべて表示」している場合は空文字列になる可能性がある
        # UpdateTableShowはmylist_urlが空文字列でも処理が可能
        mylist_url = self.window["-INPUT1-"].get()
        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)

        logger.info("VideoSearchClear success.")
        return 0


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
