# coding: utf-8
import logging.config
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import GetMyListInfo
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *

# 左ペイン
treedata = sg.TreeData()
treedata.Insert("", "k1", "t1", values=[])
tree_style = {
    "data": treedata,
    "headings": [],
    "auto_size_columns": False,
    "num_rows": 2400,
    "col0_width": 32,
    "key": "-TREE-",
    "show_expanded": False,
    "enable_events": False,
    "justification": "left",
}
l_pane = [
    [sg.Listbox(["willow8713さんの投稿動画", "moco78さんの投稿動画", "エラー値"], key="-LIST-", enable_events=False, size=(40, 48), auto_size_text=True)],
    # [sg.Tree(**tree_style)]
    [sg.Button("  +  ", key="-CREATE-"), sg.Button("  -  ", key="-DELETE-"), sg.Input("", key="-INPUT2-", size=(30, 10))],
]

# 右ペイン
table_cols_name = [" No. ", "   動画ID   ", "              動画名              ", "    投稿者    ", "  状況  ", "   投稿日時   "]
cols_width = [20, 20, 20, 20, 80, 80]
def_data = [["", "", "", "", "", ""]]
right_click_menu = ["Unused", ["再生", "---", "視聴済にする", "未視聴にする"]]
table_style = {
    "values": def_data,
    "headings": table_cols_name,
    "max_col_width": 500,
    # "def_col_width": 72 // len(cols_width),
    "def_col_width": cols_width,
    # "size": (1000, 1000),
    "num_rows": 2400,
    "auto_size_columns": True,
    "bind_return_key": True,
    "justification": "left",
    "key": "-TABLE-",
    "right_click_menu": right_click_menu,
}
t = sg.Table(**table_style)
ip = sg.Input("", key="-INPUT1-", size=(84, 100))
r_pane = [
    [ip, sg.Button("更新", key="-UPDATE-"), sg.Button("終了", key="-EXIT-")],
    [sg.Column([[t]], expand_x=True)],
]

# マイリスト一覧
db_fullpath = Path("NNMM_DB.db")
mylist_db = MylistDBController(db_fullpath=str(db_fullpath))
mylist_info_db = MylistInfoDBController(db_fullpath=str(db_fullpath))


def GuiMain():
    # 対象URL例サンプル
    target_url_example = {
        "willow8713さんの投稿動画": "https://www.nicovideo.jp/user/12899156/video",
        "moco78さんの投稿動画": "https://www.nicovideo.jp/user/1594318/video",
        "エラー値": "https://www.nicovideo.jp/user/error_address/video",
    }

    # ウィンドウのレイアウト
    mf = sg.Frame("F1",
                  [
                      [sg.Column(l_pane, expand_x=True), sg.Column(r_pane, expand_x=True, element_justification="right")]
                  ], size=(1070, 100))
    layout = [
        [mf],
    ]

    # ウィンドウオブジェクトの作成
    window = sg.Window("NNMM", layout, size=(1070, 900), finalize=True, resizable=True)
    # window["-TREE-"].bind("<Double-Button1>", "-LIST_D-")
    window["-LIST-"].bind("<Double-Button-1>", "+DOUBLE CLICK+")

    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    logger = getLogger("root")
    logger.setLevel(INFO)

    # listbox初期化
    m_list = mylist_db.Select()
    for m in m_list:
        if m["is_include_new"] == 1:
            m["listname"] = "*:" + m["listname"]
    list_data = [m["listname"] for m in m_list]
    # list_data = sg.TreeData()
    # for r in m_list:
    #     list_data.Insert("", r["listname"], "*" + r["listname"], values=[])
    window["-LIST-"].update(values=list_data)

    # def_data = [["y", "0", "[ゆっくり実況]\u3000大神\u3000絶景版\u3000その87", "0", "00", "0"]]
    def_data = [[]]
    window["-TABLE-"].update(values=def_data)

    # イベントのループ
    while True:
        # イベントの読み込み
        event, values = window.read()
        # print(event, values)
        if event in [sg.WIN_CLOSED, "-EXIT-"]:
            # ウィンドウの×ボタンが押されれば終了
            break
        if event == "視聴済にする":
            # テーブル右クリックで視聴済にするが選択された場合
            def_data = window["-TABLE-"].Values  # 現在のtableの全リスト
            for v in values["-TABLE-"]:
                row = int(v)

                # DB更新
                selected = def_data[row]
                record = mylist_info_db.SelectFromMovieID(selected[1])[0]
                record["status"] = ""
                record = mylist_info_db.Upsert(record["movie_id"], record["title"], record["username"],
                                               record["status"], record["uploaded_at"], record["url"],
                                               record["created_at"])

                # テーブル更新
                def_data[row][4] = ""
            window["-TABLE-"].update(values=def_data)
        if event == "未視聴にする":
            # テーブル右クリックで未視聴にするが選択された場合
            row = int(values["-TABLE-"][0])
            def_data = window["-TABLE-"].Values  # 現在のtableの全リスト

            # DB更新
            selected = def_data[row]
            record = mylist_info_db.SelectFromMovieID(selected[1])[0]
            record["status"] = "未視聴"
            record = mylist_info_db.Upsert(record["movie_id"], record["title"], record["username"],
                                           record["status"], record["uploaded_at"], record["url"],
                                           record["created_at"])

            # テーブル更新
            def_data[row][4] = "未視聴"
            window["-TABLE-"].update(values=def_data)
        if event == "再生":
            # テーブル右クリックで再生が選択された場合
            row = int(values["-TABLE-"][0])
            def_data = window["-TABLE-"].Values  # 現在のtableの全リスト
            selected = def_data[row]
            url = mylist_info_db.SelectFromMovieID(selected[1])[0].get("url")
            cmd = "C:/Program Files (x86)/Mozilla Firefox/firefox.exe"
            sp = sg.execute_command_subprocess(cmd, url)
            print(sg.execute_get_results(sp)[0])
        if event == "-LIST-+DOUBLE CLICK+":
            # リストボックスの項目がダブルクリックされた場合（単一）
            v = values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値
            def_data = window["-TABLE-"].Values  # 現在のtableの全リスト

            if v[:2] == "*:":
                v = v[2:]
            record = mylist_db.SelectFromListname(v)[0]
            username = record.get("username")
            target_url = record.get("url")
            window["-INPUT1-"].update(value=target_url)  # 対象マイリスのアドレスをテキストボックスに表示

            # DBからロード
            m_list = mylist_info_db.SelectFromUsername(username)
            def_data = []
            for i, m in enumerate(m_list):
                a = [i + 1, m["movie_id"], m["title"], m["username"], m["status"], m["uploaded_at"]]
                def_data.append(a)
            window["-TABLE-"].update(values=def_data)
        if event == "-UPDATE-":
            # 右上の更新ボタンが押された場合
            mylist_url = values["-INPUT1-"]

            window["-INPUT2-"].update(value="ロード中")
            window.refresh()

            # DBからロード
            record = mylist_db.SelectFromURL(mylist_url)[0]
            username = record.get("username")
            m_list = mylist_info_db.SelectFromUsername(username)
            prev_movieid_list = [m["movie_id"] for m in m_list]

            # 右ペインのテーブルに表示するマイリスト情報を取得
            def_data = []
            table_cols = ["no", "id", "title", "username", "status", "uploaded", "url"]
            now_movie_list = GetMyListInfo.GetMyListInfo(mylist_url)
            now_movieid_list = [m["movie_id"] for m in now_movie_list]

            window["-INPUT2-"].update(value="")

            # 状況ステータスを調べる
            status_check_list = []
            for i, n in enumerate(now_movieid_list):
                if n in prev_movieid_list:
                    status_check_list.append(m_list[i]["status"])
                else:
                    status_check_list.append("未視聴")

            # 右ペインのテーブルにマイリスト情報を表示
            for m, s in zip(now_movie_list, status_check_list):
                m["status"] = s
                a = [m["no"], m["movie_id"], m["title"], m["username"], m["status"], m["uploaded"]]
                def_data.append(a)
            window["-TABLE-"].update(values=def_data)

            # DBに格納
            for m in now_movie_list:
                movie_id = m["movie_id"]
                title = m["title"]
                username = m["username"]
                status = m["status"]
                uploaded_at = m["uploaded"]
                url = m["url"]

                td_format = "%Y/%m/%d %H:%M"
                dts_format = "%Y-%m-%d %H:%M:%S"
                dst = datetime.now().strftime(dts_format)
                created_at = dst
                mylist_info_db.Upsert(movie_id, title, username, status, uploaded_at, url, created_at)

            # 左のマイリストlistboxの表示を更新する
            # 一つでも未視聴の動画が含まれる場合はマークを追加する
            pass
        if event == "-CREATE-":
            # 左下、マイリスト追加ボタンが押された場合
            mylist_url = values["-INPUT1-"]

            # 右上のテキストボックスにも左下のテキストボックスにも
            # URLが入力されていない場合何もしない
            if mylist_url == "":
                mylist_url = values["-INPUT2-"]
                if mylist_url == "":
                    continue

            # 既存マイリストと重複していた場合何もしない
            prev_mylist = mylist_db.SelectFromURL(mylist_url)
            if prev_mylist:
                continue

            # 確認
            # res = sg.popup_ok_cancel(mylist_url + "\nマイリスト追加しますか？")
            # if res == "Cancel":
            #     continue

            # マイリスト情報収集
            # 右ペインのテーブルに表示するマイリスト情報を取得
            window["-INPUT2-"].update(value="ロード中")
            window.refresh()
            def_data = []
            table_cols = ["no", "movie_id", "title", "username", "status", "uploaded", "url"]
            now_movie_list = GetMyListInfo.GetMyListInfo(mylist_url)
            s_record = now_movie_list[0]
            window["-INPUT2-"].update(value="")

            # 新規マイリスト追加
            username = s_record["username"]
            type = "uploaded"  # タイプは投稿動画固定（TODO）
            listname = f"{username}さんの投稿動画"
            is_include_new = True

            td_format = "%Y/%m/%d %H:%M"
            dts_format = "%Y-%m-%d %H:%M:%S"
            dst = datetime.now().strftime(dts_format)

            mylist_db.Upsert(username, type, listname, mylist_url, dst, is_include_new)

            # listbox更新
            list_data = window["-LIST-"].Values
            n_record = mylist_db.SelectFromURL(mylist_url)
            list_data.append(n_record[0]["listname"])
            window["-LIST-"].update(values=list_data)

            # 右ペインのテーブルにマイリスト情報を表示
            for m in now_movie_list:
                m["status"] = "未視聴"  # 新規追加なのですべて未視聴
                a = [m["no"], m["movie_id"], m["title"], m["username"], m["status"], m["uploaded"]]
                def_data.append(a)
            window["-TABLE-"].update(values=def_data)
            
            # DBに格納
            for m in now_movie_list:
                movie_id = m["movie_id"]
                title = m["title"]
                username = m["username"]
                status = m["status"]
                uploaded_at = m["uploaded"]
                url = m["url"]

                td_format = "%Y/%m/%d %H:%M"
                dts_format = "%Y-%m-%d %H:%M:%S"
                dst = datetime.now().strftime(dts_format)
                created_at = dst
                mylist_info_db.Upsert(movie_id, title, username, status, uploaded_at, url, created_at)

    # ウィンドウ終了処理
    window.close()
    return 0


if __name__ == "__main__":
    GuiMain()
