import enum
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import PySimpleGUI as sg

from NNMM.model import Mylist
from NNMM.mylist_db_controller import MylistDBController


class Result(enum.Enum):
    success = enum.auto()
    failed = enum.auto()


class MylistType(enum.Enum):
    uploaded = "uploaded"
    mylist = "mylist"


class IncludeNewStatus(enum.Enum):
    yes = True
    no = False


def find_values(
    obj: Any,
    key: str,
    is_predict_one: bool = False,
    key_white_list: list[str] = None,
    key_black_list: list[str] = None,
) -> list | Any:
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
        mylist_db.upsert(
            r["id"],
            r["username"],
            r["mylistname"],
            r["type"],
            r["showname"],
            r["url"],
            r["created_at"],
            r["updated_at"],
            r["checked_at"],
            r["check_interval"],
            r["is_include_new"],
        )
    return 0


def get_mylist_type(url: str) -> MylistType | None:
    """マイリストのタイプを返す

    Args:
        url (str): 判定対象URL

    Returns:
        MylistType: マイリストのタイプ 以下のタイプのいずれでもない場合、Noneを返す
                    "uploaded": 投稿動画
                    "mylist": 通常のマイリスト
    """
    pattern = "^https://www.nicovideo.jp/user/[0-9]+/video$"
    if re.search(pattern, url):
        return MylistType.uploaded
    pattern = "^https://www.nicovideo.jp/user/[0-9]+/mylist/[0-9]+$"
    if re.search(pattern, url):
        return MylistType.mylist
    return None


def get_now_datetime() -> str:
    """タイムスタンプを返す

    Returns:
        str: 現在日時 "%Y-%m-%d %H:%M:%S" 形式
    """
    src_df = "%Y/%m/%d %H:%M"
    dst_df = "%Y-%m-%d %H:%M:%S"
    dst = datetime.now().strftime(dst_df)
    return dst


def is_mylist_include_new_video(table_list: list[list[str]]) -> bool | KeyError:
    """現在のテーブルリスト内に状況が未視聴のものが一つでも含まれているかを返す

    Args:
        table_list (list[list[str]]): テーブルリスト

    Returns:
        bool: 一つでも未視聴のものがあればTrue, そうでないならFalse
        KeyError: 引数のリストが不正
    """
    table_cols_name = [
        "No.",
        "動画ID",
        "動画名",
        "投稿者",
        "状況",
        "投稿日時",
        "登録日時",
        "動画URL",
        "所属マイリストURL",
        "マイリスト表示名",
        "マイリスト名",
    ]
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


def popup_get_text(
    message,
    title=None,
    default_text="",
    password_char="",
    size=(None, None),
    button_color=None,
    background_color=None,
    text_color=None,
    icon=None,
    font=None,
    no_titlebar=False,
    grab_anywhere=False,
    keep_on_top=None,
    location=(None, None),
    relative_location=(None, None),
    image=None,
    modal=True,
):
    """sg.popup_get_text のラッパー

    Notes:
        テキストボックスにデフォルトでフォーカスをセットする
        image はサポートしていないので利用するときは追加すること
    """
    layout = [
        [sg.Text(message, auto_size_text=True, text_color=text_color, background_color=background_color)],
        [sg.Input(default_text=default_text, size=size, key="-INPUT-", password_char=password_char, focus=True)],
        [sg.Button("Ok", size=(6, 1), bind_return_key=True), sg.Button("Cancel", size=(6, 1))],
    ]

    window = sg.Window(
        title=title or message,
        layout=layout,
        icon=icon,
        auto_size_text=True,
        button_color=button_color,
        no_titlebar=no_titlebar,
        background_color=background_color,
        grab_anywhere=grab_anywhere,
        keep_on_top=keep_on_top,
        location=location,
        relative_location=relative_location,
        finalize=True,
        modal=modal,
        font=font,
    )

    window["-INPUT-"].set_focus(True)

    button, values = window.read()
    window.close()
    del window
    if button != "Ok":
        return None
    else:
        path = values["-INPUT-"]
        return path


if __name__ == "__main__":
    pass
