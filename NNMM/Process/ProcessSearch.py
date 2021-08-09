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
        # "検索（マイリスト）::-MR-"
        # マイリスト右クリックで「検索（マイリスト）」が選択された場合
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        pattern = sg.popup_get_text("マイリスト名検索（正規表現可）")
        if pattern is None or pattern == "":
            return 0

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
                m["listname"] = NEW_MARK + m["listname"]
                include_new_index_list.append(i)
            if re.search(pattern, m["listname"]):
                match_index_list.append(i)
                index = i  # 更新後にスクロールするインデックスを更新
        list_data = [m["listname"] for m in m_list]
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

        return 0


class ProcessMylistSearchFromVideo(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "マイリスト検索（動画名）")

    def Run(self, mw):
        # "検索（動画名）::-MR-"
        # マイリスト右クリックで「検索（動画名）」が選択された場合
        # 入力された動画名を持つマイリストをハイライト表示する
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        pattern = sg.popup_get_text("動画名検索（正規表現可）")
        if pattern is None or pattern == "":
            return 0

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
                m["listname"] = NEW_MARK + m["listname"]
                include_new_index_list.append(i)

            # マイリスト内の動画情報を探索
            mylist_url = m["url"]
            records = self.mylist_info_db.SelectFromMylistURL(mylist_url)
            for r in records:
                if re.search(pattern, r["title"]):
                    match_index_list.append(i)
                    index = i  # 更新後にスクロールするインデックスを更新
        list_data = [m["listname"] for m in m_list]
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

        return 0


class ProcessVideoSearch(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "動画検索")

    def Run(self, mw):
        # "検索（動画名）::-TR-"
        # 動画テーブル右クリックで「検索（動画名）」が選択された場合
        # 現在表示中の動画テーブルから入力された動画名を持つ動画をハイライト表示する
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # マイリストURL取得
        mylist_url = self.window["-INPUT1-"].get()
        if mylist_url == "":
            return 0

        # 検索対象ワードをユーザーに問い合わせる
        pattern = sg.popup_get_text("動画名検索（正規表現可）")
        if pattern is None or pattern == "":
            return 0

        logger.info(f"search word -> {pattern}.")

        # 現在動画テーブルが選択中の場合indexを保存
        index = 0
        if self.values["-TABLE-"]:
            index = min([int(v) for v in self.values["-TABLE-"]])

        # マイリスト内の動画情報を探索
        records = self.mylist_info_db.SelectFromMylistURL(mylist_url)
        match_index_list = []
        for i, r in enumerate(records):
            if re.search(pattern, r["title"]):
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
            logger.info(f"search result -> {len(match_index_list)} mylist(s) found.")
            self.window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
        else:
            logger.info(f"search result -> Nothing mylist(s) found.")
            self.window["-INPUT2-"].update(value="該当なし")

        return 0


class ProcessMylistSearchClear(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "強調表示を解除")

    def Run(self, mw):
        # "強調表示を解除::-MR-"
        # マイリスト右クリックで「強調表示を解除」が選択された場合
        # 現在表示中のマイリストの表示をもとに戻す
        UpdateMylistShow(mw.window, mw.mylist_db)


class ProcessVideoSearchClear(ProcessBase.ProcessBase):

    def __init__(self):
        super().__init__(True, True, "強調表示を解除")

    def Run(self, mw):
        # "強調表示を解除::-TR-"
        # 動画テーブル右クリックで「強調表示を解除」が選択された場合
        # 現在表示中の動画テーブルの表示をもとに戻す
        self.window = mw.window
        self.values = mw.values
        self.mylist_db = mw.mylist_db
        self.mylist_info_db = mw.mylist_info_db

        # マイリストURL取得
        mylist_url = self.window["-INPUT1-"].get()
        if mylist_url == "":
            return 0

        UpdateTableShow(self.window, self.mylist_db, self.mylist_info_db, mylist_url)


if __name__ == "__main__":
    from NNMM import MainWindow
    mw = MainWindow.MainWindow()
    mw.Run()
