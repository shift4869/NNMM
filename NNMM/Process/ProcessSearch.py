# coding: utf-8
import re
from logging import INFO, getLogger

import PySimpleGUI as sg

from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *


logger = getLogger("root")
logger.setLevel(INFO)


def ProcessMylistSearch(window: sg.Window, values: dict, mylist_db: MylistDBController, mylist_info_db: MylistInfoDBController):
    # マイリスト右クリックで「検索」が選択された場合
    pattern = sg.popup_get_text("マイリスト名検索（正規表現可）")
    if pattern is None or pattern == "":
        return 0

    logger.info(f"search word -> {pattern}.")

    # 現在マイリストが選択中の場合indexを保存
    index = 0
    if window["-LIST-"].get_indexes():
        index = window["-LIST-"].get_indexes()[0]

    # マイリスト画面表示更新
    NEW_MARK = "*:"
    list_data = window["-LIST-"].Values
    m_list = mylist_db.Select()
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
    window["-LIST-"].update(values=list_data)

    # 新着マイリストの背景色とテキスト色を変更する
    # update(values=list_data)で更新されるとデフォルトに戻る？
    # 強調したいindexのみ適用すればそれ以外はデフォルトになる
    for i in include_new_index_list:
        window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

    # 検索でヒットした項目の背景色とテキスト色を変更する
    for i in match_index_list:
        window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light goldenrod")

    # indexをセットしてスクロール
    # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
    # window["-LIST-"].update(scroll_to_index=index)
    window["-LIST-"].Widget.see(index)
    window["-LIST-"].update(set_to_index=index)

    # 検索結果表示
    if len(match_index_list) > 0:
        logger.info(f"search result -> {len(match_index_list)} mylist(s) found.")
        window["-INPUT2-"].update(value=f"{len(match_index_list)}件ヒット！")
    else:
        logger.info(f"search result -> Nothing mylist(s) found.")
        window["-INPUT2-"].update(value="該当なし")

    return 0


if __name__ == "__main__":
    from NNMM import GuiMain
    GuiMain.GuiMain()
