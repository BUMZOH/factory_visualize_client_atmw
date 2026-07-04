# APP_NAME:稼働データ見える化
import sqlite3
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
from PIL import Image
import subprocess


# オリジナルモジュール
from common import create_ope_graph as crg

# =====================================================
# 設定
# =====================================================
# DB_PATH = Path("machine_data.db")     # ForTest
DB_PATH = Path(r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl"
           r"\operation_data\machine_operation.db")
OUTPUT_DIR = Path(r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\T_TPM関連"
              r"\C_チャレンジ賞再挑戦(2025年10月より)\K_個別改善\日別稼働グラフ")

def user_input(mc_selected:str)->tuple:
    # 機械番号入力
    if mc_selected:
        machine_input = input(f"対象機械は？(デフォルト={mc_selected})：")
    else:
        machine_input = input(f"対象機械は？(デフォルト=なし)：")

    if machine_input:
        machine_no = int(machine_input)
    else:
        machine_no = int(mc_selected)

    # 対象日&表示日数の入力
    target_day = input("対象日は？(デフォルト=昨日)：")
    days_input = input("表示日数は？(デフォルト=30)：")

    if target_day=="":
        # デフォルトは昨日
        end_date = pd.Timestamp.today().date() - pd.Timedelta(days=1)
    else:
        target_day = normalize_date_str(target_day) # 入力値正規化
        end_date = pd.to_datetime(target_day).date()

    # 対象期間 開始日格納
    if days_input=="":
        days_input = '30'   # デフォルトは30日分
    display_days = int(days_input)
    
    start_date = end_date - pd.Timedelta(days=display_days)

    # SQL用に文字列へ変換
    start_date = start_date.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")

    print(f"対象機械: {machine_no}")
    print(f"表示期間: {start_date} ～ {end_date}")
    
    return (machine_no, start_date, end_date)


def normalize_date_str(s:str) -> str:
    """ユーザ入力の日付を YYYY-MM-DDに正規化する"""
    s = s.strip()           # 空白削除
    s = s.replace("/", "-") # スラッシュ→ハイフン変換
    parts = s.split("-")    # ハイフン分割(listへ)

    # 年・月・日の判定
    if len(parts)==2:
        # 入力値が2つの場合
        year = date.today().year
        month, day = parts
    elif len(parts)==3:
        # 入力値が3つの場合
        year, month, day = parts
    else:
        raise ValueError("日付形式が不正です")
    
    # date()でチェック（バリデーション）
    d = date(int(year), int(month), int(day))

    return d.strftime("%Y-%m-%d")


def disp_ope_graph(machine_no, start_date, end_date, img):
    # SQLiteからデータ取得 ---------------------------------------
    conn = sqlite3.connect(DB_PATH)

    sql = """
    SELECT
        date,
        actual_qty,
        target_qty,
        alarm_num
    FROM operation_data
    WHERE machine_no = ?
    AND date BETWEEN ? AND ?
    ORDER BY date
    """

    df = pd.read_sql_query(
        sql,
        conn,
        params=(machine_no, start_date, end_date)
    )

    conn.close()

    if df.empty:
        print(f"MC{machine_no}: 対象期間の稼働データなし")
        return


    # dfをグラフ用に整形 ------------------------------------------
    # 日付型へ変換
    df["date"] = pd.to_datetime(df["date"])

    # 2026-03-01 ～ 2026-03-31 の全日付を作成(データがない日は NaN になる)
    # (以下の処理超重要→Obsidian参照)
    all_dates = pd.date_range(start=start_date, end=end_date, freq="D")

    df_full = (
        df.set_index("date")
        .reindex(all_dates)
        .rename_axis("date")
        .reset_index()
    )
    # print(df_full)  #debug

    # 表示用の日付文字列
    df_full["date_label"] = df_full["date"].dt.strftime("%Y-%m-%d")


    # 一覧表を表示
    # print(df_full[["date_label", "actual_qty"]])  # アラーム履歴が見づらくなるから非表示


    # =====================================================
    # matplotlibで棒グラフ表示（上中下 3段）
    # =====================================================
    plt.rcParams["font.family"] = "MS Gothic"

    # 2行1列のサブプロット
    fig, (ax1, ax2, ax3) = plt.subplots(
        3, 1,
        figsize=(14, 10),
        gridspec_kw={'height_ratios': [1, 1, 2]},
        constrained_layout=True
    )
    ax1.sharex(ax2)     # グラフ同士だけX軸共有
    ax1.tick_params(labelbottom=False)# 上のグラフのXラベル消す
    ax2.tick_params(axis="x", labelrotation=90) # 下のグラフだけX軸ラベルを回転

    
    # -------------------------------
    # 上：actual_qty
    # -------------------------------
    ax1.bar(
        df_full["date_label"],
        df_full["actual_qty"],
        color=get_colors(df_full,'tab:green')
    )
    # print(get_colors(df_full,'tab:green'))    # ForDebug

    # 目標ライン
    target = df_full["target_qty"].dropna().iloc[-1]
    ax1.axhline(
        y=target,
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"目標: {target}"
    )

    ax1.set_title(f"MC{machine_no} 日別 生産数 (基準日={end_date})")
    ax1.set_ylabel("生産数")
    ax1.legend()

    # -------------------------------
    # 中：alarm_num（ピンク）
    # -------------------------------
    ax2.bar(
        df_full["date_label"],
        df_full["alarm_num"],
        color=get_colors(df_full,'pink')
    )

    ax2.set_title(f"MC{machine_no} 日別 アラーム数 (基準日={end_date})")
    ax2.set_xlabel("日付")
    ax2.set_ylabel("アラーム数")


    # -------------------------------
    # 下：稼働グラフ
    # -------------------------------
    if img:
        ax3.imshow(img)
        ax3.axis("off")


    # -------------------------------
    # 上：actual_qty に数値表示
    # -------------------------------
    for i, v in enumerate(df_full["actual_qty"]):
        if pd.notna(v):  # NaNは表示しない
            ax1.text(
                i, v + 100,          # 少し上にずらす
                f"{int(v)}",
                ha="center",
                va="bottom",
                fontsize=8
            )

    # -------------------------------
    # 下：alarm_num に数値表示
    # -------------------------------
    for i, v in enumerate(df_full["alarm_num"]):
        if pd.notna(v):
            ax2.text(
                i, v + 1,            # 小さい値なので少しだけ上へ
                f"{int(v)}",
                ha="center",
                va="bottom",
                fontsize=8
            )
    
    # 以下がないと最終日(指定日)にデータがないとき(NaN)にX軸範囲が自動で狭くなる
    ax2.set_xlim(df_full["date_label"].min(), df_full["date_label"].max())

    # ウィンドウ最大化で表示(不要ならFalseへ)
    if True:
        manager = plt.get_current_fig_manager()
        manager.window.state('zoomed')

    plt.show()

def get_colors(df: pd.DataFrame, normal_color: str) -> list:
    """土日だけ灰色にする色リストを取得
       (dfに"date"カラムがあることが前提)
    """
    colors = [
        "gray" if d.weekday() >= 5 else normal_color
        for d in df["date"]
    ]
    return colors


def disp_alarm_hist(mc_no, start_date, end_date) -> pd.DataFrame:
    # =====================================================
    # SQLiteからアラームデータ取得&コンソールへ表示
    # =====================================================
    # アラーム履歴は時分秒まで考慮する
    # 対象の日付のみ表示に変更する(後でリファクタリングする予定)

    start_date = end_date + ' 00:00:00' # 変更箇所(最終日だけにする)
    end_date += ' 23:59:59'

    sql = f"""
    SELECT
        MachineNo,
        DateTime,
        AlarmNo,
        Message
    FROM alarm_history
    WHERE MachineNo = ?
    AND DateTime BETWEEN ? AND ?
    ORDER BY DateTime ASC
    """
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        sql,
        conn,
        params=(mc_no, start_date, end_date)
    )
    conn.close()

    if not df.empty:
        print(df.to_string())   # to_string()で全数表示となる
        # <注意> 上記結果はVS Code実行時に全て表示されないことがある
        # 　　　 (VS Codeターミナルは表示制限がある)
    else:
        print("(アラーム履歴データはありません)")

    return df


def get_mc_status_data(mc_no, op_date):
    """ DBファイルから稼働データ(3330個)を取得 """
    conn = sqlite3.connect(DB_PATH)

    sql = """
    SELECT
        all_data
    FROM operation_data
    WHERE machine_no = ?
    AND date = ?
    """

    df = pd.read_sql_query(
        sql,
        conn,
        params=(mc_no, op_date)
    )
    conn.close()

    if not df.empty:
        ret_val = df.iloc[0,0].split(",")   # 単一テキストをカンマで分離(list化)
        ret_val = [int(x) for x in ret_val] # 全要素 int変換
    else:
        # データがない場合
        ret_val = []

    return ret_val


def output_img_and_df(mc_no: int, date: str, img: Image.Image, df: pd.DataFrame) ->None:
    """ 稼働ステータスグラフとアラーム履歴をデスクトップに保存する

    Args:
        mc_no (int): 機械番号
        date (str): 対象日(期間最終日)
        img (Image.Image): 稼働ステータスグラフ
        df (pd.DataFrame): アラーム履歴データ
    """

    if not OUTPUT_DIR.exists():
        raise FileNotFoundError(
            f"出力用フォルダが存在しません\n"
            f"({OUTPUT_DIR})"
        )

    IMG_PATH = OUTPUT_DIR / f"MC{mc_no}_{date}_OpeGraph.png"
    CSV_PATH = OUTPUT_DIR / f"MC{mc_no}_{date}_AlmHist.csv"

    OUTPUT_DIR.mkdir(exist_ok=True)

    # 稼働ステータスグラフ保存
    img_ext = extend_image(img)
    img_ext.save(IMG_PATH)
    
    # アラーム履歴CSV出力
    if not df.empty:
        df.to_csv(CSV_PATH, encoding='shift-jis')

    # フォルダを開く
    subprocess.Popen(["explorer", str(OUTPUT_DIR)])


def extend_image(img: Image.Image) -> Image.Image:
    """与えられたイメージの下に300pxの余白を追加する

    Args:
        img (Image.Image): _description_

    Returns:
        Image.Image: _description_
    """
    # 元画像サイズ
    width, height = img.size

    # 下に追加する白領域の高さ
    add_height = 300

    # 新しい画像作成（白背景）
    new_img = Image.new(
        mode="RGB",
        size=(width, height + add_height),
        color="white"
    )

    # 元画像を貼り付け
    new_img.paste(img, (0, 0))

    return new_img




#---- メインプロセス -------------------------------------------
VERSION = '1.04'
LAST_UPDATE = '2026-5-11'
print(f"""
=====================================================================
    新江工場 設備稼働状況見える化プログラム
      
    Version.{VERSION} / Last Update on {LAST_UPDATE}

=====================================================================
""")

mc_selected = ""    # 前回表示した機械No

# Main Loop ----------
while True:
    # ユーザ入力
    mc_no, st_date, ed_date = user_input(mc_selected)
    mc_selected = mc_no # 次回デフォルト値のための記憶

    # アラームデータ表示(コンソールへ)
    df_alm = disp_alarm_hist(mc_no, st_date, ed_date)
    
    print("(続ける場合はグラフウィンドウを閉じてください)")
    
    # 日別稼働データ(3330個)＆グラフ取得
    opdata = get_mc_status_data(mc_no, ed_date)
    title = f"稼働状況グラフ：MC{mc_no} on {ed_date}"
    if opdata:
        img = crg.get_ope_graph(opdata, title)
    else:
        img = None

    # グラフ作成＆表示(グラフ閉じるまでここで止まる)
    disp_ope_graph(mc_no, st_date, ed_date, img)

    # データ出力確認
    if img:
        res = input('データ出力しますか?(y/n : デフォルト=n):')
        if res=='y':
            output_img_and_df(mc_no, ed_date, img, df_alm)
            print('データ出力しました（フォルダを開きます）')



    res = input('\n\n処理を繰り返しますか？(y/n : デフォルト=y):')
    if res == 'y' or res =="":
        continue
    else:
        print('--- アプリを終了します ---')
        break



"""
----- 更新履歴 ------------------------------------------------



2026.5.11
データ出力場所をデスクトップからファイルサーバへ変更
出力後に保存フォルダを自動でオープンさせる
表示不具合修正
稼働ステータスグラフに目標生産数表示(create_ope_graphを修正)

2026.5.7
ステータスグラフとアラーム履歴を出力する機能を追加

2026.5.6
共有ファイル内データ(CSVファイル)のSQLite登録処理を廃止
理由は、新江工場監視PCがPLC→共有ファイルの処理のついでに実行するため

"""