import enum
import re
from datetime import datetime
from logging import Logger
from pathlib import Path
from typing import Any

from PySide6.QtCore import QDateTime, QDir, QLibraryInfo, QSysInfo, Qt, QTimer, Slot, qVersion
from PySide6.QtGui import QCursor, QDesktopServices, QGuiApplication, QIcon, QKeySequence, QShortcut, QStandardItem
from PySide6.QtGui import QStandardItemModel, QTextCursor
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QCommandLinkButton, QDateTimeEdit, QDial, QDialog
from PySide6.QtWidgets import QDialogButtonBox, QFileSystemModel, QGridLayout, QGroupBox, QHBoxLayout, QInputDialog
from PySide6.QtWidgets import QLabel, QLineEdit, QListView, QMenu, QMessageBox, QPlainTextEdit, QProgressBar
from PySide6.QtWidgets import QPushButton, QRadioButton, QScrollBar, QSizePolicy, QSlider, QSpinBox, QStyleFactory
from PySide6.QtWidgets import QTableWidget, QTabWidget, QTextBrowser, QTextEdit, QToolBox, QToolButton, QTreeView
from PySide6.QtWidgets import QVBoxLayout, QWidget

from nnmm.model import Mylist
from nnmm.mylist_db_controller import MylistDBController

window_cache: QDialog = None


class CustomLogger(Logger):
    def __init__(self, name, level=0):
        super().__init__(name, level)

    def info(self, msg: str, *args, **kwargs):
        # コンソールとファイル出力
        if "stacklevel" not in kwargs:
            # 呼び出し元の行番号を採用するためにstacklevelを設定
            kwargs["stacklevel"] = 2
        super().info(msg, *args, **kwargs)

        # GUI画面表示
        global window_cache
        window = window_cache
        if window and isinstance(window, QDialog):
            # windowが指定されていたらキャッシュとして保存
            if not window_cache:
                window_cache = window
        else:
            # windowが指定されていない場合
            if window_cache:
                # キャッシュがあるならそれを採用
                window = window_cache
            else:
                # そうでない場合、画面更新は何もせず終了
                return

        if not isinstance(window, QDialog):
            return
        textarea: QTextEdit = window.textarea
        # old_text = textarea.document().toPlainText()
        now_datetime = get_now_datetime()
        textarea.append(f"{now_datetime} {msg}")
        textarea.moveCursor(QTextCursor.MoveOperation.End)
        textarea.update()
        # window.repaint()

    def error(self, msg: str, *args, **kwargs):
        # コンソールとファイル出力
        if "stacklevel" not in kwargs:
            # 呼び出し元の行番号を採用するためにstacklevelを設定
            kwargs["stacklevel"] = 2
        super().error(msg, *args, **kwargs)

        # GUI画面表示
        global window_cache
        window = window_cache
        if window:
            # windowが指定されていたらキャッシュとして保存
            if not window_cache:
                window_cache = window
        else:
            # windowが指定されていない場合
            if window_cache:
                # キャッシュがあるならそれを採用
                window = window_cache
            else:
                # そうでない場合、画面更新は何もせず終了
                return
        textarea: QTextEdit = window.textarea
        # old_text = textarea.document().toPlainText()
        now_datetime = get_now_datetime()
        textarea.append(f"{now_datetime} {msg}")
        textarea.moveCursor(QTextCursor.MoveOperation.End)
        textarea.update()
        # window.repaint()


class Result(enum.Enum):
    success = enum.auto()
    failed = enum.auto()


class MylistType(enum.Enum):
    none = None
    uploaded = "uploaded"
    mylist = "mylist"
    series = "series"


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


def save_mylist(mylist_db: MylistDBController, save_file_path: str) -> Result:
    """MylistDBの内容をcsvファイルに書き出す

    Args:
        mylist_db (MylistDBController): 書き出す対象のマイリストDB
        save_file_path (str): 保存先パス

    Returns:
        Result: 成功時Result.success
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
    return Result.success


def load_mylist(mylist_db: MylistDBController, load_file_path: str) -> Result:
    """書き出したcsvファイルからMylistDBへレコードを反映させる

    Args:
        mylist_db (MylistDBController): 反映させる対象のマイリストDB
        load_file_path (str): 入力ファイルパス

    Returns:
        Result: 成功時Result.success, データ不整合Result.failed
    """
    sd_path = Path(load_file_path)
    mylist_cols = Mylist.__table__.c.keys()

    records = []
    lines = str(sd_path.read_text(encoding="utf_8_sig"))
    line_list = re.split("[\n]", lines)[1:]  # 項目行は読み飛ばす
    for line in line_list:
        elements = re.split("[,]", line)

        # データ列の個数が不整合
        if len(mylist_cols) != len(elements):
            continue 

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
            r["check_failed_count"],
            r["is_include_new"],
        )
    return Result.success


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


def popup_get_text(message: str, title: str = None) -> str | None:
    """ユーザーにテキストを問い合わせるポップアップを表示する

    Args:
        message (str): 表示メッセージ
        title (str): タイトル

    Returns:
        str: 成功時 ユーザーが入力した文字列、キャンセル時 None
    """
    input_text, result = QInputDialog.getText(None, title, message)

    if result:
        return input_text
    else:
        return None


def popup(message: str, title: str = None, ok_cancel: bool = False) -> str | None:
    """ユーザーにメッセージを伝えるポップアップを表示する

    Args:
        message (str): 表示メッセージ
        title (str): タイトル
        ok_cancel (bool): yes/noを問い合わせるかのフラグ

    Returns:
        str: 成功時 ユーザーが入力した "OK" または "Cancel" 文字列、指定しない場合は None
    """
    msgbox = QMessageBox()
    msgbox.setText(message)
    if title:
        msgbox.setWindowTitle(title)
    else:
        # 空白指定するとデフォルト値の "python" が表示されるため
        # 半角スペースのみをタイトルとして表示する
        msgbox.setWindowTitle(" ")

    if ok_cancel:
        msgbox.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    result = msgbox.exec()

    if ok_cancel:
        if result == QMessageBox.StandardButton.Ok:
            return "OK"
        elif result == QMessageBox.StandardButton.Cancel:
            return "Cancel"
    return None


if __name__ == "__main__":
    pass
