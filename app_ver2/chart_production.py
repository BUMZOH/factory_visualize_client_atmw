"""指定した1生産日の設備別生産実績と目標生産数を表示する。"""

import sqlite3
from datetime import datetime
from pathlib import Path

from matplotlib.figure import Figure


# ================================================
#   Settings
# ================================================
DB_DIR = Path(
    r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl"
    r"\operation_data"
)

CHART_TITLE = "機械別の生産実績・目標"
CHART_X_LABEL = "設備番号"
CHART_Y_LABEL = "生産数"
ACTUAL_COLOR = "tab:cyan"
TARGET_COLOR = "red"


def add_weekday(date_text: str) -> str:
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    date = datetime.strptime(date_text, "%Y-%m-%d")
    weekday = weekdays[date.weekday()]

    return f"{date_text}({weekday})"


# ================================================
#   Chart
# ================================================
class MachineProductionChart(Figure):
    def update(
        self,
        machine_numbers: list[int],
        machine_types: list[str],
        production_date: str,
        db_file: str,
    ) -> None:
        """指定した1生産日の生産実績と目標生産数を設備別に表示する。

        設備は指定順で表示する。
        レコードがない設備は「データなし」と表示する。
        当日のレコードは取得途中の値を含む。
        """
        production_date = datetime.strptime(
            production_date, "%Y-%m-%d"
        ).date().isoformat()

        # 重複を除き、指定した設備の順番を保つ。
        machine_numbers = list(dict.fromkeys(machine_numbers))
        if not machine_numbers:
            raise ValueError("設備番号を1台以上指定してください")

        db_path = DB_DIR / db_file
        if not db_path.is_file():
            raise FileNotFoundError(db_path)

        if db_file == "main_factory_production_data.db":
            production_by_machine = self._get_main_factory_data(
                db_path,
                machine_numbers,
                production_date,
            )
        elif db_file == "machine_operation.db":
            production_by_machine = self._get_shine_factory_data(
                db_path,
                machine_numbers,
                production_date,
            )
        else:
            raise ValueError(f"未対応のDBです: {db_file}")

        self._draw_chart(
            machine_numbers,
            machine_types,
            production_date,
            production_by_machine,
        )

    def _get_main_factory_data(
        self,
        db_path: Path,
        machine_numbers: list[int],
        production_date: str,
    ) -> dict:
        placeholders = ", ".join("?" for _ in machine_numbers)

        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute(
                f"""
                SELECT machine_no,
                       actual_production,
                       target_production
                FROM operation_data
                WHERE machine_no IN ({placeholders})
                  AND production_date = ?
                """,
                (*machine_numbers, production_date),
            ).fetchall()
        finally:
            conn.close()

        return {
            machine_no: (actual, target)
            for machine_no, actual, target in rows
        }

    def _get_shine_factory_data(
        self,
        db_path: Path,
        machine_numbers: list[int],
        production_date: str,
    ) -> dict:
        placeholders = ", ".join("?" for _ in machine_numbers)

        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute(
                f"""
                SELECT machine_no,
                       actual_qty,
                       target_qty
                FROM operation_data
                WHERE machine_no IN ({placeholders})
                  AND date = ?
                """,
                (*machine_numbers, production_date),
            ).fetchall()
        finally:
            conn.close()

        return {
            machine_no: (actual, target)
            for machine_no, actual, target in rows
        }

    def _draw_chart(
        self,
        machine_numbers: list[int],
        machine_types: list[str],
        production_date: str,
        production_by_machine: dict,
    ) -> None:
        actual_values = [
            production_by_machine.get(n, (0, 0))[0]
            for n in machine_numbers
        ]

        # データのない設備は折れ線を途切れさせる。
        target_values = [
            production_by_machine.get(n, (0, float("nan")))[1]
            for n in machine_numbers
        ]
        positions = list(range(len(machine_numbers)))

        self.clear()
        ax = self.add_subplot(111)

        bars = ax.bar(
            positions,
            actual_values,
            color=ACTUAL_COLOR,
            label="生産実績",
            edgecolor="gray",
            linewidth=1,
        )
        ax.bar_label(
            bars,
            labels=[
                f"{value:.0f}" if machine_no in production_by_machine else ""
                for machine_no, value in zip(
                    machine_numbers,
                    actual_values,
                )
            ],
            padding=3,
            fontsize=9,
        )

        ax.plot(
            positions,
            target_values,
            color=TARGET_COLOR,
            linestyle=":",
            marker="o",
            markersize=4,
            linewidth=1.5,
            label="目標生産数",
        )

        # 目標生産数を折れ線の各点の上に赤字で表示する。
        for x, machine_no, target in zip(
            positions,
            machine_numbers,
            target_values,
        ):
            if machine_no in production_by_machine:
                ax.annotate(
                    f"{target:.0f}",
                    (x, target),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    color=TARGET_COLOR,
                    fontsize=9,
                )

        ax.set_xticks(
            positions,
            [
                f"{number}\n{machine_type}"
                for number, machine_type in zip(
                    machine_numbers,
                    machine_types,
                )
            ],
        )
        display_date = add_weekday(production_date)
        ax.set_title(f"{CHART_TITLE} {display_date}", loc="left", pad=24)
        ax.set_xlabel(CHART_X_LABEL)
        ax.set_ylabel(CHART_Y_LABEL)

        max_value = max(
            [0]
            + actual_values
            + [
                values[1]
                for values in production_by_machine.values()
            ]
        )
        ax.set_ylim(0, max_value * 1.1 if max_value > 0 else 1)
        ax.set_axisbelow(True)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(
            loc="lower right",
            bbox_to_anchor=(1, 1.02),
            ncol=2,
            borderaxespad=0,
            fontsize=9,
            handlelength=1.2,
            handletextpad=0.4,
            columnspacing=1.0,
            frameon=False,
        )

        for x, machine_no in zip(positions, machine_numbers):
            if machine_no not in production_by_machine:
                ax.annotate(
                    "データなし",
                    (x, 0),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha="center",
                    fontsize=9,
                )

        self.tight_layout()


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "Yu Gothic"
    plt.rcParams["axes.unicode_minus"] = False

    factory = "main"  # "main" or "shine" で切り替え

    if factory == "main":
        machine_numbers = [
            1, 3, 4, 6, 7, 10, 12, 13, 14, 17, 30, 32, 40
        ]
        machine_types = [
            "KDP", "KDP", "KDP", "KDP", "KDP", "KDP", "KDP",
            "KDP", "KDP", "KDP", "KDP", "KDP", "KDPN",
        ]
        production_date = "2026-10-06"
        db_file = "main_factory_production_data.db"

    elif factory == "shine":
        machine_numbers = [15, 20, 21, 22, 23]
        machine_types = ["TUBA", "TUBA", "STUD", "TUBA", "STUD"]
        production_date = "2026-02-05"
        db_file = "machine_operation.db"

    else:
        raise ValueError(f"未対応の工場です: {factory}")

    # 単体確認ではplt.show()用にpyplot経由で生成する。
    # Tkinterに組み込む場合: figure = MachineProductionChart()
    figure = plt.figure(FigureClass=MachineProductionChart)
    figure.update(
        machine_numbers=machine_numbers,
        machine_types=machine_types,
        production_date=production_date,
        db_file=db_file,
    )

    plt.show()