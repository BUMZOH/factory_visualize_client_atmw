import json
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk


# ================================================
#   Settings
# ================================================
BASE_DIR = Path(__file__).resolve().parent
DB_DIR = Path(
    r"\\192.168.2.1\共有ファイル\M-光和共有ファイル"
    r"\P_ProductControl\operation_data"
)
LAYOUT_PATH = BASE_DIR / "factory_machine_layout.json"

TABLE_COLUMNS = {
    "datetime": {
        "text": "Datetime",
        "width": 200,
        "anchor": tk.CENTER,
    },
    "message": {
        "text": "Message",
        "width": 700,
        "anchor": tk.W,
    },
}


# ================================================
#   Functions
# ================================================
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


# ================================================
#   Alarm table
# ================================================
class AlarmTable(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.tree = ttk.Treeview(
            self,
            columns=tuple(TABLE_COLUMNS.keys()),
            show="headings",
            height=10,
        )

        scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.tree.yview,
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set,
        )

        for column_id, settings in TABLE_COLUMNS.items():
            self.tree.heading(
                column_id,
                text=settings["text"],
            )

            self.tree.column(
                column_id,
                width=settings["width"],
                anchor=settings["anchor"],
            )

        self.tree.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
        )

        scrollbar.pack(
            side=tk.RIGHT,
            fill=tk.Y,
        )

    def update(
        self,
        machine_no: int,
        production_date: str,
    ) -> None:
        """機械番号と日付からアラーム履歴を表示する。"""
        db_file = get_db_file(machine_no)

        if db_file == "machine_operation.db":
            db_path = DB_DIR / db_file
            rows = self._get_shine_factory_data(
                db_path,
                machine_no,
                production_date,
            )
        else:
            rows = []

        self._update_table(rows)

    def _get_shine_factory_data(
        self,
        db_path: Path,
        machine_no: int,
        production_date: str,
    ) -> list[tuple]:
        """新江工場DBから指定日のアラーム履歴を取得する。"""
        with sqlite3.connect(db_path) as connection:
            rows = connection.execute(
                """
                SELECT
                    DateTime,
                    Message
                FROM alarm_history
                WHERE MachineNo = ?
                  AND DateTime >= ?
                  AND DateTime < datetime(?, '+1 day')
                ORDER BY DateTime ASC
                """,
                (
                    machine_no,
                    production_date,
                    production_date,
                ),
            ).fetchall()

        return rows

    def _update_table(self, rows: list[tuple]) -> None:
        """テーブルを更新する。"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            self.tree.insert(
                "",
                tk.END,
                values=row,
            )


# ================================================
#   Test
# ================================================
if __name__ == "__main__":
    TEST_MACHINE_NO = 55
    TEST_PRODUCTION_DATE = "2026-04-29"

    root = tk.Tk()
    root.title("Alarm Table Test")
    root.geometry("1000x500")

    table = AlarmTable(root)
    table.pack(
        fill=tk.BOTH,
        expand=True,
        padx=10,
        pady=10,
    )

    table.update(
        machine_no=TEST_MACHINE_NO,
        production_date=TEST_PRODUCTION_DATE,
    )

    root.mainloop()