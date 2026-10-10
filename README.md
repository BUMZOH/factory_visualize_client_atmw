# Factory Production Dashboard

工場設備の1日単位の稼働状況・生産実績・アラーム情報を確認するための
Tkinterダッシュボードです。

エリア単位で複数設備を比較する「日別」画面と、設備1台を詳しく確認する
「詳細」画面を備えています。

現在は次の2種類のデータベースに対応しています。

-   `main_factory_production_data.db`
-   `machine_operation.db`

設備・エリアと使用するデータベースの対応は `factory_machine_layout.json`
で管理します。

------------------------------------------------------------------------

## 1. 主な機能

### 日別画面

対象エリアと対象日を指定し、設備ごとの状態を4種類のグラフで表示します。

1.  定時内の機械稼働状況
2.  定時内・定時外の機械稼働時間
3.  機械別の生産実績・目標
4.  機械別のアラーム発生数

各グラフは独立した `chart_*.py` として実装し、 `tab_daily.py`
が4つのグラフを2×2でまとめて表示します。

### 詳細画面

設備番号と対象日を指定し、設備1台の詳細情報を表示します。

-   1日の設備ステータスタイムライン
-   アラーム履歴
-   横スクロールによるタイムライン確認

タイムラインは `chart_status_timeline.py`、 アラーム履歴は
`table_daily_alarm.py` が担当します。

### キャプチャ

「日別」「詳細」の両画面に「キャプチャ」ボタンがあります。

現在表示しているアプリウィンドウ全体をPNG形式で保存します。

保存先：

``` text
C:\Users\<ユーザー名>\Pictures
```

ファイル名：

``` text
capture_YYYYMMDD_HHMMSS.png
```

`self.winfo_toplevel()` から最上位ウィンドウを取得するため、
各タブの単独起動時だけでなく `app.py` から起動した場合も使用できます。

------------------------------------------------------------------------

## 2. 画面構成

``` text
Factory Production Dashboard
│
├─ 日別
│   ├─ 対象エリア
│   ├─ 対象日
│   ├─ 検索
│   ├─ キャプチャ
│   │
│   └─ 2×2グラフ
│       ├─ 定時内の機械稼働状況
│       ├─ 定時内・定時外の機械稼働時間
│       ├─ 機械別の生産実績・目標
│       └─ 機械別のアラーム発生数
│
└─ 詳細
    ├─ 対象機械
    ├─ 対象日
    ├─ 検索
    ├─ キャプチャ
    │
    ├─ ステータスタイムライン
    │
    └─ アラーム履歴
```

------------------------------------------------------------------------

## 3. プログラム構成

``` text
app.py
│
├─ tab_daily.py
│   ├─ chart_regular_time_status.py
│   ├─ chart_operating_time.py
│   ├─ chart_production.py
│   └─ chart_alarm_count.py
│
├─ tab_detail.py
│   ├─ chart_status_timeline.py
│   └─ table_daily_alarm.py
│
├─ factory_machine_layout.json
├─ style.py
└─ run.bat
```

基本方針は、

``` text
chart / table
      ↓
     tab
      ↓
    app.py
```

です。

グラフやテーブルを小さな独立部品として作成し、タブで1画面にまとめ、
最後に `app.py` で複数画面を統合します。

この構造により、各部品を単独で確認しながら開発できます。

------------------------------------------------------------------------

## 4. ファイル一覧

  --------------------------------------------------------------------------------
  ファイル                            役割
  ----------------------------------- --------------------------------------------
  `app.py`                            アプリ全体、左サイドナビ、ページ切替

  `tab_daily.py`                      日別画面、検索条件、4グラフの配置

  `tab_detail.py`                     詳細画面、タイムラインとアラーム履歴の配置

  `chart_regular_time_status.py`      定時内の設備ステータス積み上げグラフ

  `chart_operating_time.py`           定時内・定時外の稼働時間グラフ

  `chart_production.py`               生産実績・目標グラフ

  `chart_alarm_count.py`              アラーム発生数グラフ

  `chart_status_timeline.py`          設備1台・1日のタイムライン画像生成

  `table_daily_alarm.py`              設備1台・1日のアラーム履歴表示

  `factory_machine_layout.json`       エリア、設備番号、設備種類、DBの定義

  `style.py`                          ttk共通スタイル

  `run.bat`                           仮想環境を使用したアプリ起動
  --------------------------------------------------------------------------------

------------------------------------------------------------------------

## 5. app.py

`app.py` はアプリ全体をまとめる最上位ファイルです。

ウィンドウ設定：

``` text
タイトル : Factory Production Dashboard
サイズ   : 1600 x 950
バージョン: Ver.20261010-1
```

左側のナビゲーションから次のページを切り替えます。

``` text
日別
詳細
```

各ページは `place()` で同じ領域に重ねて配置し、 `tkraise()`
で表示ページを切り替えます。

終了時は各ページの `close_charts()` を呼び出してから
Tkinterウィンドウを破棄します。

------------------------------------------------------------------------

## 6. factory_machine_layout.json

設備構成はPythonコードへ直接書かず、 `factory_machine_layout.json`
で管理します。

各エリアには次の情報を設定します。

``` json
{
    "AreaName": {
        "db_file": "database.db",
        "machine_numbers": [1, 2, 3],
        "machine_types": ["TYPE1", "TYPE2", "TYPE3"]
    }
}
```

### db_file

そのエリアが使用するデータベースです。

``` text
main_factory_production_data.db
machine_operation.db
```

### machine_numbers

エリアに所属する設備番号です。

### machine_types

設備番号に対応する設備種類です。

`machine_numbers` と `machine_types`
は同じ順序・同じ要素数で設定します。

現在は本社工場の複数エリアと、新江工場のRD、KAL/TAP、検査系エリアが
登録されています。

------------------------------------------------------------------------

## 7. 2種類のDBへの対応

本アプリでは、同じ画面から2種類のDBを扱います。

``` text
main_factory_production_data.db
machine_operation.db
```

日別画面では、選択したエリアの `db_file` を
`factory_machine_layout.json` から取得し、各チャートへ渡します。

各チャートは、

``` python
if db_file == "main_factory_production_data.db":
    ...
elif db_file == "machine_operation.db":
    ...
```

のようにDBごとの取得処理を分離し、その後の描画処理を共通化しています。

つまり、

``` text
DBごとのデータ取得
        ↓
共通形式へ整理
        ↓
共通の描画処理
```

という構造です。

------------------------------------------------------------------------

## 8. 日別画面

`tab_daily.py` は対象エリア・対象日を受け取り、
4つのチャートをまとめて更新します。

各チャートには共通して次の情報を渡します。

``` python
figure.update(
    machine_numbers,
    machine_types,
    date_text,
    db_file,
)
```

### 8.1 定時内の機械稼働状況

`chart_regular_time_status.py`

定時時間を540分として、各状態の時間を積み上げ表示します。

主な状態：

-   自動運転
-   材料切れ
-   段替え
-   故障
-   アラーム
-   刃具交換

本社工場DBではBLOBの `all_data` と集計済みカラムを使用します。

`machine_operation.db` ではカンマ区切りTEXTの `all_data`
を整数配列へ変換し、 `common_lib_mw.opdata_generator`
を使用して各時間を取得します。

### 8.2 定時内・定時外の機械稼働時間

`chart_operating_time.py`

自動運転時間を、

-   定時内稼働時間
-   定時外稼働時間

に分けて積み上げ表示します。

定時外稼働時間は、

``` text
全自動運転時間 - 定時内自動運転時間
```

で求めます。

### 8.3 機械別の生産実績・目標

`chart_production.py`

-   生産実績：棒グラフ
-   目標生産数：折れ線

として表示します。

DBごとに異なるカラム名を内部で吸収し、
描画側では同じ形式として扱います。

### 8.4 機械別のアラーム発生数

`chart_alarm_count.py`

設備ごとのアラーム発生数を棒グラフで表示します。

DBごとに、

``` text
main_factory_production_data.db : alarm_number
machine_operation.db            : alarm_num
```

を読み分けます。

------------------------------------------------------------------------

## 9. 詳細画面

`tab_detail.py` は設備1台・対象日1日を指定して詳細を表示します。

検索条件：

``` text
対象機械
対象日
```

検索すると、

``` text
MachineStatusTimeline
        +
AlarmTable
```

の両方を同じ条件で更新します。

------------------------------------------------------------------------

## 10. タイムライン

`chart_status_timeline.py`

設備番号から `factory_machine_layout.json` を逆引きし、
使用するDBを自動判定します。

呼び出し側はDBを意識せず、

``` python
timeline.update(machine_no, production_date)
```

だけで使用できます。

処理イメージ：

``` text
machine_no
    ↓
factory_machine_layout.json
    ↓
db_file
    │
    ├─ main_factory_production_data.db
    │      ↓
    │   BLOB取得
    │      ↓
    │   1500形式 → 3330形式
    │
    └─ machine_operation.db
           ↓
        TEXT取得
           ↓
        3330個の整数へ変換
    ↓
create_ope_graph.get_ope_graph()
    ↓
Pillow画像
```

本社工場の1500個形式は、既存グラフ関数で使用する3330個形式へ変換します。

新江工場側の `all_data` は3330個のカンマ区切りTEXTとして取得します。

------------------------------------------------------------------------

## 11. アラーム履歴

`table_daily_alarm.py`

設備番号と日付を指定して、その日1日のアラーム履歴を表示します。

表示項目：

``` text
Datetime
Message
```

`AlarmNo` はDBに存在しますが、画面には表示しません。

### 対応DB

アラーム履歴の `alarm_history` テーブルは `machine_operation.db`
のみに存在するため、

``` text
machine_operation.db
    → alarm_historyを検索

main_factory_production_data.db
    → アラーム履歴は表示しない
```

という動作です。

検索条件は設備番号と1日単位の日付です。

------------------------------------------------------------------------

## 12. 日付・設備番号の操作

### 日付

日付Entryでは次のキー操作が使用できます。

  キー         動作
  ------------ ---------
  `↑`          前日
  `↓`          翌日
  `Ctrl + ↑`   前月1日
  `Ctrl + ↓`   翌月1日
  `Enter`      検索

### 詳細画面の設備番号

  キー      動作
  --------- -------------
  `↑`       設備番号 +1
  `↓`       設備番号 -1
  `Enter`   検索

設備番号は1～99の範囲で扱います。

------------------------------------------------------------------------

## 13. 必要なPythonライブラリ

コード上で使用している主な外部ライブラリは次のとおりです。

``` text
matplotlib
Pillow
```

Tkinter、sqlite3、json、struct、datetime、pathlib は
Python標準ライブラリです。

また、設備データ処理用としてプロジェクト環境から次を使用します。

``` text
common_lib_mw.opdata_generator
common_lib_mw.create_ope_graph
```

------------------------------------------------------------------------

## 14. 起動方法

### run.batから起動

通常は `run.bat` を実行します。

`run.bat` は自身のフォルダへ移動したあと、
親フォルダの仮想環境を使用して `app.py` を起動します。

想定構成：

``` text
親フォルダ
├─ .venv
│   └─ Scripts
│       └─ python.exe
│
└─ アプリフォルダ
    ├─ run.bat
    ├─ app.py
    └─ ...
```

仮想環境が存在しない場合はエラーを表示して終了します。

### Pythonから直接起動

``` bash
python app.py
```

------------------------------------------------------------------------

## 15. DB配置

現在のコードではDBフォルダとして次の共有フォルダを参照します。

``` text
\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl\operation_data
```

このフォルダ内の、

``` text
main_factory_production_data.db
machine_operation.db
```

を使用します。

そのため、アプリを使用するPCから共有フォルダへアクセスできる必要があります。

------------------------------------------------------------------------

## 16. 開発時の単独テスト

各部品はできるだけ単独で確認できる構造にしています。

例：

``` text
chart_regular_time_status.py
chart_operating_time.py
chart_production.py
chart_alarm_count.py
chart_status_timeline.py
table_daily_alarm.py
tab_daily.py
tab_detail.py
```

チャート部品を単独確認し、その後タブへ組み込み、 最後に `app.py`
から確認する流れを基本とします。

``` text
部品単独テスト
      ↓
タブ単独テスト
      ↓
app.py統合テスト
```

DB対応の変更時もこの順番で確認することで、
問題の発生箇所を切り分けやすくなります。

------------------------------------------------------------------------

## 17. 設計方針

このアプリでは、できるだけ役割を小さく分けています。

### chart

DBから必要なデータを取得し、グラフを描画する部品。

### table

DBから必要なデータを取得し、表として表示する部品。

### tab

検索条件や画面レイアウトを担当し、 chart / table
を組み合わせて1画面を作る部品。

### app.py

複数のtabをまとめ、アプリ全体のナビゲーションと終了処理を担当します。

``` text
データ取得・表示部品
        ↓
      tab
        ↓
     app.py
```

DBごとの差異も、できるだけchart / table側へ閉じ込めます。

そのため上位の `tab_daily.py`、`tab_detail.py`、`app.py` は
DB内部の細かな違いを意識せずに利用できます。

------------------------------------------------------------------------

## 18. 現在の状態

2026-10-10時点で、次の動作を確認済みです。

-   日別画面の4グラフ表示
-   本社工場DB対応
-   新江工場DB対応
-   JSONによるエリア・設備・DB管理
-   詳細画面のタイムライン表示
-   設備番号からのDB自動判定
-   `machine_operation.db` のアラーム履歴表示
-   本社工場設備ではアラーム履歴を空表示
-   日別画面のキャプチャ
-   詳細画面のキャプチャ
-   各タブ単独起動時のキャプチャ
-   `app.py` 起動時のキャプチャ
-   `app.py` からの日別・詳細画面表示

現在のアプリバージョン：

``` text
Ver.20261010-1
```

------------------------------------------------------------------------

## 19. 今後変更するときの基本ルール

設備やエリアを追加するときは、まず `factory_machine_layout.json`
の追加・変更を検討します。

新しいグラフを追加するときは、

``` text
chart_xxx.py
    ↓
tab_xxx.py
    ↓
app.py
```

の順に組み込みます。

DBごとに構造が異なる場合は、上位画面へ条件分岐を増やすのではなく、
可能な限り各chart / table内部でDB差を吸収します。

この方針を維持することで、画面側をシンプルに保ちながら
対応設備や表示内容を拡張できます。
