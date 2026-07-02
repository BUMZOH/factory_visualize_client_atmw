# SQLite BLOB（uint16）データ取得関数

## 概要

SQLiteのBLOB列`all_data`を取得し、16bit符号なし整数のリストへ変換する方法をまとめます。

## 完成コード

``` python
import sqlite3
import struct

def get_all_data(
        db_path: str,
        machine_no: int,
        production_date: str
) -> list[int]:
    """
    指定した機械番号・生産日の all_data(BLOB) を取得する

    Args:
        db_path: SQLiteデータベースファイル
        machine_no: 機械番号
        production_date: 生産日 (YYYY-MM-DD)

    Returns:
        list[int]: uint16データのリスト

    Raises:
        ValueError: データが存在しない場合
    """
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT all_data
            FROM operation_data
            WHERE machine_no = ?
            AND production_date = ?
            """,
            (machine_no, production_date),
        )

        row = cur.fetchone()

    if row is None:
        raise ValueError(
            f"データがありません "
            f"(machine_no={machine_no}, production_date={production_date})"
        )
    
    blob = row[0]

    # uint16の個数
    count = len(blob) // 2

    # リストへ変換（リトルエンディアン）
    return list(struct.unpack(f"<{count}H", blob))


if __name__ == '__main__':
    values = get_all_data(
        "main_factory_production_data.db",
        machine_no=1,
        production_date="2026-07-01"
    )
    print(values[:20])
    print(len(values))





```

## 解説

### データ取得

-   `with sqlite3.connect()`で安全に接続します。
-   `machine_no`と`production_date`を条件に検索します。
-   データが存在しない場合は`ValueError`を送出します。

### BLOBの構造

SQLiteのBLOBは`bytes`型です。
今回は16bit=2Byteのデータが連続して格納されているため、

``` python
count = len(blob) // 2
```

でデータ数を求めています。

### struct.unpack

``` python
struct.unpack(f"<{count}H", blob)
```

-   `<` : リトルエンディアン
-   `H` : 16bit符号なし整数

としてBLOB全体を一括変換します。

### エンディアンについて

DBファイルだけを見てもリトルエンディアンかビッグエンディアンかは判定できません。
保存したプログラムやデータ仕様から判断します。

## 今回の学び

-   BLOBはByte列として保存される
-   uint16は2Byteなので`len(blob)//2`
-   `struct.unpack()`は高速で保守しやすい
-   DB単体からエンディアンは判断できない
-   `with`文を使うと接続を自動でクローズできる
