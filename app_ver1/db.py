import sqlite3
import struct
from pathlib import Path
from datetime import datetime, timedelta

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


def get_all_data_or_zeros(
        machine_no: int,
        production_date: str,
        data_length: int = 1500
) -> list[int]:
    """
    指定した機械番号・生産日の all_data を取得する。
    データが存在しない場合は、全要素0のリストを返す。
    """
    try:
        return get_all_data(machine_no, production_date)
    
    except ValueError:
        return [0] * data_length


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


def get_machine_no_list() -> list[int]:
    """
    operation_dataテーブルに存在する設備番号一覧を取得する

    Returns:
        list[int]
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute("""
            SELECT DISTINCT machine_no
            FROM operation_data
            ORDER BY machine_no
        """)

        rows = cur.fetchall()

    return [row[0] for row in rows]


def get_daily_trend_data(
        machine_no: int,
        base_date: str,
        display_days: int
) -> list[dict]:
    """
    指定設備の指定期間における日別推移データを取得する。
    actual_production / target_production / alarm_number は専用カラムから取得する。
    """

    base_dt = datetime.strptime(base_date, "%Y-%m-%d").date()
    start_dt = base_dt - timedelta(days=display_days - 1)

    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = base_dt.strftime("%Y-%m-%d")

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                production_date,
                actual_production,
                target_production,
                alarm_number
            FROM operation_data
            WHERE machine_no = ?
            AND production_date BETWEEN ? AND ?
            ORDER BY production_date
            """,
            (machine_no, start_date, end_date),
        )

        rows = cur.fetchall()

    data_map = {
        row[0]: {
            "production_date": row[0],
            "actual_count": row[1],
            "target_count": row[2],
            "alarm_count": row[3],
        }
        for row in rows
    }

    result = []

    for i in range(display_days):
        current_dt = start_dt + timedelta(days=i)
        production_date = current_dt.strftime("%Y-%m-%d")

        result.append(
            data_map.get(
                production_date,
                {
                    "production_date": production_date,
                    "actual_count": None,
                    "target_count": None,
                    "alarm_count": None,
                }
            )
        )

    return result



if __name__ == '__main__':

    # print(get_machine_no_list()
    print(get_daily_trend_data(1,"2026-07-01",10))
    exit()

    values = get_1day_status_data(
        machine_no=1,
        production_date="2026-07-01"
    )
    print(values[:20])
    print(len(values))

    from common_lib_mw import create_ope_graph as cog
    img = cog.get_ope_graph(values, title="SAMPLE")
    # cog.save_img("sample.png", img)



