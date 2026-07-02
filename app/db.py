import sqlite3
import struct
from pathlib import Path

DB_PATH = Path(r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl\operation_data\main_factory_production_data.db")


def get_all_data(
        machine_no: int,
        production_date: str
) -> list[int]:
    """
    指定した機械番号・生産日の all_data(BLOB) を取得する

    Args:
        machine_no: 機械番号
        production_date: 生産日 (YYYY-MM-DD)

    Returns:
        list[int]: uint16データのリスト

    Raises:
        ValueError: データが存在しない場合
    """
    with sqlite3.connect(DB_PATH) as conn:
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


def get_1day_status_data(
        machine_no: int,
        production_date: str
) -> list[int]:
    """
    指定した機械番号・生産日の ステータスデータ(1440個) を取得する
    (注意: get_all_dataメソッドは全データ1500個を返す)

    Args:
        machine_no: 機械番号
        production_date: 生産日 (YYYY-MM-DD)
    Returns:
        list[int]: uint16データのリスト
    """
    values = get_all_data(machine_no, production_date)

    return values[10:1450]



if __name__ == '__main__':

    values = get_1day_status_data(
        machine_no=1,
        production_date="2026-07-01"
    )
    print(values[:20])
    print(len(values))

    from common_lib_mw import create_ope_graph as cog
    img = cog.get_ope_graph(values, title="SAMPLE")
    # cog.save_img("sample.png", img)



