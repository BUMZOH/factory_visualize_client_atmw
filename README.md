# Factory Production Dashboard

工場設備の生産・稼働データを確認するためのTkinter製ダッシュボードアプリです。

SQLiteデータベースから設備ごとのデータを取得し、日別の集計グラフと設備1台ごとの詳細タイムラインを表示します。

## 主な機能

### 日別画面

対象エリアと対象日を指定して、次の4種類のグラフを2×2で表示します。

-   定時内の機械稼働状況
-   定時内・定時外の機械稼働時間
-   機械別の生産実績・目標
-   機械別のアラーム発生数

横軸には設備番号と設備種類を2段で表示します。

設備の表示順、設備番号、設備種類は `factory_machine_layout.json`
で管理します。

### 詳細画面

設備番号と対象日を指定して、設備1台分のステータスタイムラインを表示します。

画像が画面より大きい場合は、縦・横スクロールで確認できます。

## ファイル構成

``` text
app.py
├─ tab_daily.py
│  ├─ chart_regular_time_status.py
│  ├─ chart_operating_time.py
│  ├─ chart_production.py
│  └─ chart_alarm_count.py
├─ tab_detail.py
│  └─ chart_status_timeline.py
├─ style.py
├─ factory_machine_layout.json
└─ run.bat
```

  ----------------------------------------------------------------------------------
  ファイル                            内容
  ----------------------------------- ----------------------------------------------
  `app.py`                            メインウィンドウ、サイドバー、画面切替

  `tab_daily.py`                      日別画面のUIと4グラフの管理

  `tab_detail.py`                     設備1台の詳細画面

  `chart_regular_time_status.py`      定時内の設備状態を積み上げ表示

  `chart_operating_time.py`           定時内・定時外の稼働時間を表示

  `chart_production.py`               生産実績と目標生産数を表示

  `chart_alarm_count.py`              アラーム発生数を表示

  `chart_status_timeline.py`          設備1台・1日分のタイムライン画像を生成

  `factory_machine_layout.json`       エリアごとの設備番号・設備種類・表示順を定義

  `style.py`                          Tkinter / ttk の共通スタイル

  `run.bat`                           アプリ起動用バッチファイル
  ----------------------------------------------------------------------------------

## 設備レイアウト設定

`factory_machine_layout.json` にエリアごとの設備を定義します。

``` json
{
    "factory1": {
        "machine_numbers": [1, 3, 4],
        "machine_types": ["KDP", "KDP", "KDP"]
    }
}
```

`machine_numbers` と `machine_types`
は同じ順番で対応させ、要素数も一致させてください。

JSONに記述した設備番号の順番が、そのまま日別グラフの表示順になります。

## 使用ライブラリ

-   tkinter / ttk
-   matplotlib
-   Pillow
-   sqlite3（Python標準ライブラリ）

詳細タイムラインの生成では、既存ライブラリ `common_lib_mw` の
`create_ope_graph` を使用しています。

## データベース

各グラフはSQLiteデータベースの `operation_data`
テーブルからデータを取得します。

現在のコードではデータベースの保存場所をネットワークパスで指定しています。

環境を変更する場合は、各チャートモジュールの `DB_PATH`
を確認してください。

## 起動

通常は `run.bat` から起動します。

Pythonから直接起動する場合：

``` bash
python app.py
```

## プログラム構成

左側のサイドバーから「日別」「詳細」の画面を切り替えます。

画面UIは `XXX_tab.py`、グラフや表示部品は `XXX_chart.py`
に分離しています。

UIとデータ取得・描画処理の役割を分けることで、機能追加や修正をしやすい構成にしています。

## 現在のバージョン

`Ver.20261007-1`
