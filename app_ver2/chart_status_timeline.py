"""DBから1日分の機械ステータスを取得して、Pillowのタイムライン画像を作る。"""
import json
import sqlite3
import struct
from datetime import datetime
from pathlib import Path

from PIL import Image
from common_lib_mw import create_ope_graph

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = Path(r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl\operation_data")
LAYOUT_PATH = BASE_DIR / "factory_machine_layout.json"

# ----- FUNCTIONS ----------------------------------------
def get_db_file(machine_no: int) -> str:
    """設備番号から使用するDBファイル名を取得する。"""
    with LAYOUT_PATH.open(encoding="utf-8") as file:
        layout = json.load(file)

    for area_data in layout.values():
        if machine_no in area_data["machine_numbers"]:
            return area_data["db_file"]

    raise ValueError(
        f"設備{machine_no}: factory_machine_layout.jsonに定義されていません。"
    )


def data_convert_to_shine(data_1500: list[int]) -> list[int]:
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

        db_file = get_db_file(machine_no)
        db_path = DB_DIR / db_file

        if db_file == "main_factory_production_data.db":
            all_data = self._get_main_factory_data(
                db_path,
                machine_no,
                production_date,
            )
        elif db_file == "machine_operation.db":
            all_data = self._get_shine_factory_data(
                db_path,
                machine_no,
                production_date,
            )
        else:
            raise ValueError(f"未対応のDBです: {db_file}")

        if all_data is None:
            return None

        image = create_ope_graph.get_ope_graph(
            all_data,
            f"設備 {machine_no} / {production_date}",
        )

        if image is None:
            raise ValueError(
                f"設備{machine_no}: タイムライン画像を作成できませんでした。"
            )

        return image

    def _get_main_factory_data(
        self,
        db_path: Path,
        machine_no: int,
        production_date: str,
    ) -> list[int] | None:
        """本社工場DBから3330個形式のデータを取得する。"""
        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                "SELECT all_data FROM operation_data "
                "WHERE machine_no = ? AND production_date = ?",
                (machine_no, production_date),
            ).fetchone()

        if row is None:
            return None

        blob = row[0]

        if not isinstance(blob, bytes) or len(blob) < 1500 * 2 or len(blob) % 2:
            raise ValueError(
                f"設備{machine_no}: all_dataのデータ長が不正です。"
            )

        # リトルエンディアンの符号なし16bit整数。
        all_data_1500 = struct.unpack(f"<{len(blob) // 2}H", blob)

        return data_convert_to_shine(list(all_data_1500))

    def _get_shine_factory_data(
        self,
        db_path: Path,
        machine_no: int,
        production_date: str,
    ) -> list[int] | None:
        """新江工場DBから3330個形式のデータを取得する。"""
        with sqlite3.connect(db_path) as connection:
            row = connection.execute(
                "SELECT all_data FROM operation_data "
                "WHERE machine_no = ? AND date = ?",
                (machine_no, production_date),
            ).fetchone()

        if row is None:
            return None

        all_data_text = row[0]

        if not isinstance(all_data_text, str):
            raise ValueError(
                f"設備{machine_no}: all_dataのデータ形式が不正です。"
            )

        all_data = [
            int(value)
            for value in all_data_text.split(",")
        ]

        if len(all_data) != 3330:
            raise ValueError(
                f"設備{machine_no}: all_dataのデータ数が不正です。"
            )

        return all_data


if __name__ == "__main__":
    # 単独テスト：特定の設備1台・特定の日だけで画像を作成する。
    TEST_MACHINE_NO = 15
    TEST_PRODUCTION_DATE = "2026-10-06"

    timeline = MachineStatusTimeline()
    image = timeline.update(TEST_MACHINE_NO, TEST_PRODUCTION_DATE)
    if image is None:
        print(f"設備 {TEST_MACHINE_NO} / {TEST_PRODUCTION_DATE}: データなし")
    else:
        image.show()
