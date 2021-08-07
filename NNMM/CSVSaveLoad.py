# coding: utf-8
import logging.config
import re
from bs4 import BeautifulSoup
from logging import INFO, getLogger
from pathlib import Path

import emoji
from sqlalchemy.sql.functions import user

from NNMM.MylistDBController import *


def SaveMylist(mylist_db, save_file_path):
    sd_path = Path(save_file_path)
    records = mylist_db.Select()
    mylist_cols = ["id", "username", "type", "listname", "url", "created_at", "is_include_new"]
    param_list = []
    with sd_path.open("w", encoding="utf-8") as fout:
        fout.write(",".join(mylist_cols) + "\n")
        for r in records:
            param_list = [str(r.get(s)) for s in mylist_cols]
            fout.write(",".join(param_list) + "\n")
    return 0


def SaveXML(directory_path):
    sd_path = Path(directory_path)
    r_path = sd_path.parent / "res.csv"
    mylist_cols = ["id", "username", "type", "listname", "url", "created_at", "is_include_new"]

    with r_path.open("w", encoding="utf-8") as fout:
        fout.write(",".join(mylist_cols) + "\n")
        file_list = list(sd_path.glob("**/*.xml"))
        sorted(file_list)
        for s in file_list:
            with s.open("r", encoding="utf-8") as fin:
                soup = BeautifulSoup(fin.read(), "lxml-xml")
                xml_channel = soup.find("channel")
                xml_title = xml_channel.find("title")
                xml_link = xml_channel.find("link")
                title = xml_title.text
                url = xml_link.text

                pattern = "^(.*)さんの投稿動画‐ニコニコ動画"
                username = re.findall(pattern, title)[0]
                username = re.sub(r'[\\/:*?"<>|]', "", username)
                username = emoji.get_emoji_regexp().sub("", username)

                td_format = "%Y/%m/%d %H:%M"
                dts_format = "%Y-%m-%d %H:%M:%S"
                dst = datetime.now().strftime(dts_format)
                param_list = ["", username, "uploaded", f"{username}さんの投稿動画", url, dst, "TRUE"]

                fout.write(",".join(param_list) + "\n")
    pass


def LoadMylist(mylist_db, load_file_path):
    sd_path = Path(load_file_path)
    mylist_cols = ["id", "username", "type", "listname", "url", "created_at", "is_include_new"]
    param_dict = {}
    with sd_path.open("r", encoding="utf-8") as fin:
        fin.readline()
        for line in fin:
            if line == "":
                break

            elements = re.split("[,\n]", line)[:-1]
            param_dict = dict(zip(mylist_cols, elements))
            r = mylist_db.SelectFromURL(param_dict["url"])
            if r:
                continue

            id_index = param_dict["id"]
            username = param_dict["username"]
            type = param_dict["type"]
            listname = param_dict["listname"]
            url = param_dict["url"]
            created_at = param_dict["created_at"]
            # td_format = "%Y/%m/%d %H:%M"
            # dts_format = "%Y-%m-%d %H:%M:%S"
            # dst = datetime.strptime(created_at, td_format).strftime(dts_format)
            dst = created_at
            is_include_new = param_dict["is_include_new"]
            mylist_db.Upsert(id_index, username, type, listname, url, dst, dst, False)
    return 0


if __name__ == "__main__":
    db_fullpath = Path("NNMM_DB.db")
    mylist_db = MylistDBController(db_fullpath=str(db_fullpath))
    file_path = Path("mylist.csv")
    # SaveMylist(mylist_db, file_path)
    LoadMylist(mylist_db, file_path)

    sd_path = Path("./sample/user/")
    # SaveXML(sd_path)
    pass
