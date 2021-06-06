# coding: utf-8
import logging.config
import time
import threading
from logging import INFO, getLogger
from pathlib import Path

import PySimpleGUI as sg

from NNMM import GetMyListInfo
from NNMM import GuiFunction
from NNMM.MylistDBController import *
from NNMM.MylistInfoDBController import *
from NNMM.GuiFunction import *

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
    [sg.Button("  +  ", key="-CREATE-"), sg.Button("  -  ", key="-DELETE-"), sg.Button(" all ", key="-ALL_UPDATE-"),
     sg.Input("", key="-INPUT2-", size=(24, 10))],
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
        if m["is_include_new"]:
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

            # 視聴済になったことでマイリストの新着表示を消すかどうか判定する
            if not IsMylistIncludeNewMovie(window["-TABLE-"].Values):
                # マイリストDB更新
                mylist_url = values["-INPUT1-"]
                record = mylist_db.SelectFromURL(mylist_url)[0]
                record["is_include_new"] = False  # 新着マークを更新
                # record["listname"] = record["listname"][2:]  # *:を削除
                mylist_db.Upsert(record["username"], record["type"], record["listname"],
                                 record["url"], record["created_at"], record["is_include_new"])

                # マイリスト画面表示更新
                UpdateMylistShow(window, mylist_db)
        if event == "未視聴にする":
            # テーブル右クリックで未視聴にするが選択された場合
            def_data = window["-TABLE-"].Values  # 現在のtableの全リスト
            for v in values["-TABLE-"]:
                row = int(v)

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

            # 未視聴になったことでマイリストの新着表示を表示する
            # 未視聴にしたので必ず新着あり扱いになる
            # マイリストDB更新
            mylist_url = values["-INPUT1-"]
            record = mylist_db.SelectFromURL(mylist_url)[0]
            record["is_include_new"] = True
            mylist_db.Upsert(record["username"], record["type"], record["listname"],
                             record["url"], record["created_at"], record["is_include_new"])

            # マイリスト画面表示更新
            UpdateMylistShow(window, mylist_db)
        if event == "再生":
            # テーブル右クリックで再生が選択された場合
            if not values["-TABLE-"]:
                continue
            row = int(values["-TABLE-"][0])
            def_data = window["-TABLE-"].Values  # 現在のtableの全リスト
            selected = def_data[row]

            # 視聴済にする
            table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "URL"]
            if def_data[row][4] != "":
                def_data[row][4] = ""
                window["-TABLE-"].update(values=def_data)

            # 視聴済になったことでマイリストの新着表示を消すかどうか判定する
            if not IsMylistIncludeNewMovie(window["-TABLE-"].Values):
                # マイリストDB更新
                mylist_url = values["-INPUT1-"]
                record = mylist_db.SelectFromURL(mylist_url)[0]
                record["is_include_new"] = False  # 新着マークを更新
                # record["listname"] = record["listname"][2:]  # *:を削除
                mylist_db.Upsert(record["username"], record["type"], record["listname"],
                                 record["url"], record["created_at"], record["is_include_new"])

                # マイリスト画面表示更新
                UpdateMylistShow(window, mylist_db)

            # ブラウザに動画urlを渡す
            url = mylist_info_db.SelectFromMovieID(selected[1])[0].get("url")
            cmd = "C:/Program Files (x86)/Mozilla Firefox/firefox.exe"
            sp = sg.execute_command_subprocess(cmd, url)
            # print(sg.execute_get_results(sp)[0])
        if event == "-LIST-+DOUBLE CLICK+":
            # リストボックスの項目がダブルクリックされた場合（単一）
            v = values["-LIST-"][0]  # ダブルクリックされたlistboxの選択値
            def_data = window["-TABLE-"].Values  # 現在のtableの全リスト

            if v[:2] == "*:":
                v = v[2:]
            record = mylist_db.SelectFromListname(v)[0]
            username = record.get("username")
            mylist_url = record.get("url")
            window["-INPUT1-"].update(value=mylist_url)  # 対象マイリスのアドレスをテキストボックスに表示

            # テーブル更新
            UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)
        if event == "-UPDATE-":
            # 右上の更新ボタンが押された場合
            mylist_url = values["-INPUT1-"]

            # 左下の表示変更
            window["-INPUT2-"].update(value="ロード中")
            window.refresh()

            # マイリストレコードから現在のマイリスト情報を取得する
            # AsyncHTMLSessionでページ情報をレンダリングして解釈する
            # マルチスレッド処理
            record = mylist_db.SelectFromURL(mylist_url)[0]
            threading.Thread(target=GuiFunction.UpdateMylistInfoThread, args=(window, mylist_db, mylist_info_db, record), daemon=True).start()
        if event == "-UPDATE_THREAD_DONE-":
            # -UPDATE-のマルチスレッド処理が終わった後の処理
            # 左下の表示を戻す
            window["-INPUT2-"].update(value="")

            # テーブルの表示を更新する
            mylist_url = values["-INPUT1-"]
            if mylist_url != "":
                UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)
            window.refresh()
            
            # マイリストの新着表示を表示するかどうか判定する
            def_data = window["-TABLE-"].Values  # 現在のtableの全リスト

            # 左のマイリストlistboxの表示を更新する
            # 一つでも未視聴の動画が含まれる場合はマイリストに進捗マークを追加する
            if IsMylistIncludeNewMovie(def_data):
                record = mylist_db.SelectFromURL(mylist_url)[0]
                # マイリストDB更新
                record["is_include_new"] = True  # 新着マークを更新
                mylist_db.Upsert(record["username"], record["type"], record["listname"],
                                 record["url"], record["created_at"], record["is_include_new"])

            # マイリスト画面表示更新
            UpdateMylistShow(window, mylist_db)
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
            # TODO::async
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

            # マイリスト画面表示更新
            UpdateMylistShow(window, mylist_db)
            
            # DBに格納
            for m in now_movie_list:
                movie_id = m["movie_id"]
                title = m["title"]
                username = m["username"]
                status = "未視聴"  # 初追加時はすべて未視聴扱い
                uploaded_at = m["uploaded"]
                url = m["url"]

                td_format = "%Y/%m/%d %H:%M"
                dts_format = "%Y-%m-%d %H:%M:%S"
                dst = datetime.now().strftime(dts_format)
                created_at = dst
                mylist_info_db.Upsert(movie_id, title, username, status, uploaded_at, url, created_at)

            # テーブルの表示を更新する
            UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)
        if event == "-ALL_UPDATE-":
            # 左下のすべて更新ボタンが押された場合
            window["-INPUT2-"].update(value="全てのマイリストを更新中")
            window.refresh()
            # 存在するすべてのマイリストから現在のマイリスト情報を取得する
            # AsyncHTMLSessionでページ情報をレンダリングして解釈する
            # マルチスレッド処理
            threading.Thread(target=GuiFunction.UpdateAllMylistInfoThread,
                             args=(window, mylist_db, mylist_info_db), daemon=True).start()
        if event == "-ALL_UPDATE_THREAD_DONE-":
            # -ALL_UPDATE-のマルチスレッド処理が終わった後の処理
            # 左下の表示を戻す
            window["-INPUT2-"].update(value="")

            # テーブルの表示を更新する
            mylist_url = values["-INPUT1-"]
            if mylist_url != "":
                UpdateTableShow(window, mylist_db, mylist_info_db, mylist_url)

            # マイリストの新着表示を表示するかどうか判定する
            m_list = mylist_db.Select()
            for m in m_list:
                username = m["username"]
                movie_list = mylist_info_db.SelectFromUsername(username)
                table_cols_name = ["No.", "動画ID", "動画名", "投稿者", "状況", "投稿日時", "URL"]
                def_data = []
                for i, t in enumerate(movie_list):
                    a = [i + 1, t["movie_id"], t["title"], t["username"], t["status"], t["uploaded_at"]]
                    def_data.append(a)

                # 左のマイリストlistboxの表示を更新する
                # 一つでも未視聴の動画が含まれる場合はマイリストに進捗マークを追加する
                if IsMylistIncludeNewMovie(def_data):
                    # マイリストDB更新
                    m["is_include_new"] = True  # 新着マークを更新
                    mylist_db.Upsert(m["username"], m["type"], m["listname"],
                                     m["url"], m["created_at"], m["is_include_new"])

            # マイリスト画面表示更新
            UpdateMylistShow(window, mylist_db)

    # ウィンドウ終了処理
    window.close()
    return 0


if __name__ == "__main__":
    GuiMain()
