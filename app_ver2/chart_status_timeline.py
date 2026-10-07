"""DBから1日分の機械ステータスを取得して、Pillowのタイムライン画像を作る。"""
import sqlite3
import struct
from datetime import datetime
from pathlib import Path

from PIL import Image
from common_lib_mw import create_ope_graph

BASE_DIR = Path(__file__).resolve().parent
# DB_PATH = BASE_DIR / "main_factory_production_data.db"
DB_PATH = Path(r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl\operation_data\main_factory_production_data.db")


# ----- FUNCTIONS ----------------------------------------
def data_convert_to_sine(data_1500: list[int]) -> list[int]:
    """本社工場の1500個データを、既存グラフ関数用の3330個形式へ変換する。"""
    data_3330 = data_1500 + [0] * 1830

    data_3330[4] = data_1500[2]     # 生産数
    data_3330[5] = data_1500[3]     # 異常数
    data_3330[7] = data_1500[4]     # 目標数

    return data_3330


class MachineStatusTimeline:
    def update(self, machine_no: int, production_date: str) -> Image.Image | None:
        """1台・1日分の画像を返す。該当データがなければNone。"""
        if type(machine_no) is not int or not 1 <= machine_no <= 99:
            raise ValueError("対象機械は1〜99の整数を指定してください。")
        date = datetime.strptime(production_date, "%Y-%m-%d")
        if date.strftime("%Y-%m-%d") != production_date:
            raise ValueError("対象日はYYYY-MM-DD形式で入力してください。")

        with sqlite3.connect(DB_PATH) as connection:
            row = connection.execute(
                "SELECT all_data FROM operation_data "
                "WHERE machine_no = ? AND production_date = ?",
                (machine_no, production_date),
            ).fetchone()
        if row is None:
            return None

        blob = row[0]
        if not isinstance(blob, bytes) or len(blob) < 1500 * 2 or len(blob) % 2:
            raise ValueError(f"設備{machine_no}: all_dataのデータ長が不正です。")
        # リトルエンディアンの符号なし16bit整数。
        all_data_1500 = struct.unpack(f"<{len(blob) // 2}H", blob)
        all_data_3330 = data_convert_to_sine(list(all_data_1500))
        image = create_ope_graph.get_ope_graph(
            all_data_3330, f"設備 {machine_no} / {production_date}"
        )
        if image is None:
            raise ValueError(f"設備{machine_no}: タイムライン画像を作成できませんでした。")
        return image


if __name__ == "__main__":
    # 単独テスト：特定の設備1台・特定の日だけで画像を作成する。
    TEST_MACHINE_NO = 1
    TEST_PRODUCTION_DATE = "2026-10-06"

    timeline = MachineStatusTimeline()
    image = timeline.update(TEST_MACHINE_NO, TEST_PRODUCTION_DATE)
    if image is None:
        print(f"設備 {TEST_MACHINE_NO} / {TEST_PRODUCTION_DATE}: データなし")
    else:
        image.show()
