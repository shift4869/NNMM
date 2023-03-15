# coding: utf-8
import logging.config
import re
from logging import INFO, getLogger
from pathlib import Path

from NNMM.MylistDBController import *


def SaveMylist(mylist_db: MylistDBController, save_file_path: str) -> int:
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


def LoadMylist(mylist_db: MylistDBController, load_file_path: str) -> int:
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


if __name__ == "__main__":
    db_fullpath = Path("NNMM_DB.db")
    mylist_db = MylistDBController(db_fullpath=str(db_fullpath))
    file_path = Path("result.csv")

    # SaveMylist(mylist_db, file_path)
    LoadMylist(mylist_db, file_path)

    pass
