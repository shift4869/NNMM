import enum
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import PySimpleGUI as sg

from NNMM.model import Mylist
from NNMM.mylist_db_controller import MylistDBController
from NNMM.mylist_info_db_controller import MylistInfoDBController


class Result(enum.Enum):
    success = enum.auto()
    failed = enum.auto()


def find_values(obj: Any,
                key: str,
                is_predict_one: bool = False,
                key_white_list: list[str] = None,
                key_black_list: list[str] = None) -> list | Any:
    if not key_white_list:
        key_white_list = []
    if not key_black_list:
        key_black_list = []

    def _inner_helper(inner_obj: Any, inner_key: str, inner_result: list) -> list:
        if isinstance(inner_obj, dict) and (inner_dict := inner_obj):
            for k, v in inner_dict.items():
                if k == inner_key:
                    inner_result.append(v)
                if key_white_list and (k not in key_white_list):
                    continue
                if k in key_black_list:
                    continue
                inner_result.extend(_inner_helper(v, inner_key, []))
        if isinstance(inner_obj, list) and (inner_list := inner_obj):
            for element in inner_list:
                inner_result.extend(_inner_helper(element, inner_key, []))
        return inner_result

    result = _inner_helper(obj, key, [])
    if not is_predict_one:
        return result

    if len(result) < 1:
        raise ValueError(f"Value of key='{key}' is not found.")
    if len(result) > 1:
        raise ValueError(f"Value of key='{key}' are multiple found.")
    return result[0]

def save_mylist(mylist_db: MylistDBController, save_file_path: str) -> int:
    """MylistDBの内容をcsvファイルに書き出す

    Args:
        mylist_db (MylistDBController): 書き出す対象のマイリストDB
        save_file_path (str): 保存先パス

    Returns:
        int: 成功時0
    """
    sd_path = Path(save_file_path)
    records = mylist_db.select()
    mylist_cols = Mylist.__table__.c.keys()
    param_list = []

    # BOMつきutf-8で書き込むことによりExcelでも開けるcsvを出力する
    with sd_path.open("w", encoding="utf_8_sig") as fout:
        fout.write(",".join(mylist_cols) + "\n")  # 項目行書き込み
        for r in records:
            param_list = [str(r.get(s)) for s in mylist_cols]
            fout.write(",".join(param_list) + "\n")
    return 0

def load_mylist(mylist_db: MylistDBController, load_file_path: str) -> int:
    """書き出したcsvファイルからMylistDBへレコードを反映させる

    Args:
        mylist_db (MylistDBController): 反映させる対象のマイリストDB
        load_file_path (str): 入力ファイルパス

    Returns:
        int: 成功時0, データ不整合-1
    """
    sd_path = Path(load_file_path)
    mylist_cols = Mylist.__table__.c.keys()

    records = []
    with sd_path.open("r", encoding="utf_8_sig") as fin:
        fin.readline()  # 項目行読み飛ばし
        for line in fin:
            if line == "":
                break

            elements = re.split("[,\n]", line)[:-1]

            # データ列の個数が不整合
            if len(mylist_cols) != len(elements):
                return -1

            param_dict = dict(zip(mylist_cols, elements))
            r = mylist_db.select_from_url(param_dict["url"])
            if r:
                continue  # 既に存在しているなら登録せずに処理続行

            # 型変換
            param_dict["id"] = int(param_dict["id"])
            param_dict["is_include_new"] = True if param_dict["is_include_new"] == "True" else False
            records.append(param_dict)

    # THINK::Mylistにもrecords一括Upsertのメソッドを作る？
    for r in records:
        mylist_db.upsert(r["id"], r["username"], r["mylistname"], r["type"], r["showname"], r["url"],
                         r["created_at"], r["updated_at"], r["checked_at"], r["check_interval"], r["is_include_new"])
    return 0

def get_mylist_type(url: str) -> str:
    """マイリストのタイプを返す

    Args:
        url (str): 判定対象URL

    Returns:
        str: マイリストのタイプ 以下のタイプのいずれでもない場合、空文字列を返す
             "uploaded": 投稿動画
             "mylist": 通常のマイリスト
    """
    pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
    if re.search(pattern, url):
        return "uploaded"
    pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
    if re.search(pattern, url):
        return "mylist"
    return ""

def get_now_datetime() -> str:
    """タイムスタンプを返す

    Returns:
        str: 現在日時 "%Y-%m-%d %H:%M:%S" 形式
    """
    src_df = "%Y/%m/%d %H:%M"
    dst_df = "%Y-%m-%d %H:%M:%S"
    dst = datetime.now().strftime(dst_df)
    return dst

def is_mylist_include_new_video(table_list: list[list]) -> bool | KeyError:
    """現在のテーブルリスト内に状況が未視聴のものが一つでも含まれているかを返す

    Args:
        table_list (list[list]): テーブルリスト

    Returns:
        bool: 一つでも未視聴のものがあればTrue, そうでないならFalse
        KeyError: 引数のリストが不正
    """
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    STATUS_INDEX = 4

    # 空リストならFalse
    if len(table_list) == 0:
        return False

    # リスト内のリストの要素数が少ないならKeyError
    if len(table_list[0]) < STATUS_INDEX + 1:
        raise KeyError

    # 状況部分が想定ステータスでない場合 -> 項目名の並びが不正の場合KeyError
    if not all([v[STATUS_INDEX] in ["", "未視聴"] for v in table_list]):
        raise KeyError

    # 一つでも未視聴のものがあればTrue, そうでないならFalse
    return any([v[STATUS_INDEX] == "未視聴" for v in table_list])

def interval_translate(interval_str: str) -> int:
    """インターバルを解釈する関数

    Note:
        次のいずれかが想定されている
        ["n分","n時間","n日","n週間","nヶ月"]

    Args:
        interval_str (str): インターバルを表す文字列

    Returns:
        int: 成功時 分[min]を表す数値、失敗時 -1
    """
    pattern = "^([0-9]+)分$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0])

    pattern = "^([0-9]+)時間$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0]) * 60

    pattern = "^([0-9]+)日$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0]) * 60 * 24

    pattern = "^([0-9]+)週間$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0]) * 60 * 24 * 7

    pattern = "^([0-9]+)ヶ月$"
    if re.findall(pattern, interval_str):
        return int(re.findall(pattern, interval_str)[0]) * 60 * 24 * 31  # 月は正確ではない28,29,30,31
    return -1

def popup_get_text(message, title=None, default_text='', password_char='', size=(None, None), button_color=None,
                   background_color=None, text_color=None, icon=None, font=None, no_titlebar=False,
                   grab_anywhere=False, keep_on_top=None, location=(None, None), relative_location=(None, None), image=None, modal=True):
    """sg.popup_get_text のラッパー

    Notes:
        テキストボックスにデフォルトでフォーカスをセットする
        image はサポートしていないので利用するときは追加すること
    """
    layout = [[sg.Text(message, auto_size_text=True, text_color=text_color, background_color=background_color)],
              [sg.Input(default_text=default_text, size=size, key="-INPUT-", password_char=password_char, focus=True)],
              [sg.Button("Ok", size=(6, 1), bind_return_key=True), sg.Button("Cancel", size=(6, 1))]]

    window = sg.Window(title=title or message, layout=layout, icon=icon, auto_size_text=True, button_color=button_color, no_titlebar=no_titlebar,
                       background_color=background_color, grab_anywhere=grab_anywhere, keep_on_top=keep_on_top, location=location, relative_location=relative_location, finalize=True, modal=modal, font=font)

    window["-INPUT-"].set_focus(True)

    button, values = window.read()
    window.close()
    del window
    if button != "Ok":
        return None
    else:
        path = values["-INPUT-"]
        return path

def update_mylist_pane(window: sg.Window, mylist_db: MylistDBController) -> int:
    """マイリストペインの表示を更新する

    Args:
        window (sg.Window): pysimpleguiのwindowオブジェクト
        mylist_db (MylistDBController): マイリストDBコントローラー

    Returns:
        int: 成功時0
    """
    # 現在選択中のマイリストがある場合そのindexを保存
    index = 0
    if window["-LIST-"].get_indexes():
        index = window["-LIST-"].get_indexes()[0]

    # マイリスト画面表示更新
    NEW_MARK = "*:"
    list_data = window["-LIST-"].Values
    m_list = mylist_db.select()
    include_new_index_list = []
    for i, m in enumerate(m_list):
        if m["is_include_new"]:
            m["showname"] = NEW_MARK + m["showname"]
            include_new_index_list.append(i)
    list_data = [m["showname"] for m in m_list]
    window["-LIST-"].update(values=list_data)

    # 新着マイリストの背景色とテキスト色を変更する
    # update(values=list_data)で更新されるとデフォルトに戻る？
    # 強調したいindexのみ適用すればそれ以外はデフォルトになる
    for i in include_new_index_list:
        window["-LIST-"].Widget.itemconfig(i, fg="black", bg="light pink")

    # indexをセットしてスクロール
    # scroll_to_indexは強制的にindexを一番上に表示するのでWidget.seeを使用
    # window["-LIST-"].update(scroll_to_index=index)
    window["-LIST-"].Widget.see(index)
    window["-LIST-"].update(set_to_index=index)
    return 0

def update_table_pane(window: sg.Window, mylist_db: MylistDBController, mylist_info_db: MylistInfoDBController, mylist_url: str = "") -> int:
    """テーブルリストペインの表示を更新する

    Args:
        window (sg.Window): pysimpleguiのwindowオブジェクト
        mylist_db (MylistDBController): マイリストDBコントローラー
        mylist_info_db (MylistInfoDBController): 動画情報DBコントローラー
        mylist_url (str): 表示対象マイリスト

    Returns:
        int: 成功時0, エラー時-1
    """
    # 表示対象マイリストが空白の場合は
    # 右上のテキストボックスに表示されている現在のマイリストURLを設定する(window["-INPUT1-"])
    if mylist_url == "":
        mylist_url = window["-INPUT1-"].get()

    index = 0
    def_data = []
    table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "登録日時", "動画URL", "所属マイリストURL", "マイリスト表示名", "マイリスト名"]
    if mylist_url == "":
        # 引数も右上のテキストボックスも空白の場合
        # 現在表示しているテーブルの表示をリフレッシュする処理のみ行う
        def_data = window["-TABLE-"].Values  # 現在のtableの全リスト

        # 現在選択中のマイリストがある場合そのindexを保存
        index = 0
        if window["-LIST-"].get_indexes():
            index = window["-LIST-"].get_indexes()[0]
    else:
        # 現在のマイリストURLからlistboxのindexを求める
        m_list = mylist_db.select()
        mylist_url_list = [m["url"] for m in m_list]
        for i, url in enumerate(mylist_url_list):
            if mylist_url == url:
                index = i
                break

        # 現在のマイリストURLからテーブル情報を求める
        records = mylist_info_db.select_from_mylist_url(mylist_url)
        for i, m in enumerate(records):
            a = [i + 1, m["video_id"], m["title"], m["username"], m["status"], m["uploaded_at"], m["registered_at"], m["video_url"], m["mylist_url"]]
            def_data.append(a)

    # 画面更新
    # window["-LIST-"].update(set_to_index=index)
    window["-LIST-"].Widget.see(index)
    window["-TABLE-"].update(values=def_data)
    if len(def_data) > 0:
        window["-TABLE-"].update(select_rows=[0])
    # 1行目は背景色がリセットされないので個別に指定してdefaultの色で上書き
    window["-TABLE-"].update(row_colors=[(0, "", "")])
    return 0


if __name__ == "__main__":
    pass
