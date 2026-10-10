"""指定した1生産日の設備別アラーム発生数を表示する。"""

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

CHART_TITLE = "機械別のアラーム発生数"
CHART_X_LABEL = "設備番号"
CHART_Y_LABEL = "アラーム発生数（回）"
CHART_COLOR = "tab:pink"
REFERENCE_COUNT = 20


# ================================================
#   Chart
# ================================================
class MachineAlarmCountChart(Figure):
    def update(
        self,
        machine_numbers: list[int],
        machine_types: list[str],
        production_date: str,
        db_file: str,
    ) -> None:
        """指定した1生産日のアラーム発生数を設備別に表示する。

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
            count_by_machine = self._get_main_factory_data(
                db_path,
                machine_numbers,
                production_date,
            )
        elif db_file == "machine_operation.db":
            count_by_machine = self._get_shine_factory_data(
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
            count_by_machine,
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
                       alarm_number
                FROM operation_data
                WHERE machine_no IN ({placeholders})
                  AND production_date = ?
                """,
                (*machine_numbers, production_date),
            ).fetchall()
        finally:
            conn.close()

        return dict(rows)

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
                       alarm_num
                FROM operation_data
                WHERE machine_no IN ({placeholders})
                  AND date = ?
                """,
                (*machine_numbers, production_date),
            ).fetchall()
        finally:
            conn.close()

        return dict(rows)

    def _draw_chart(
        self,
        machine_numbers: list[int],
        machine_types: list[str],
        production_date: str,
        count_by_machine: dict,
    ) -> None:
        alarm_counts = [
            count_by_machine.get(n, 0)
            for n in machine_numbers
        ]
        positions = list(range(len(machine_numbers)))

        self.clear()
        ax = self.add_subplot(111)

        bars = ax.bar(
            positions,
            alarm_counts,
            color=CHART_COLOR,
            label="アラーム発生数",
            edgecolor="gray",
            linewidth=1,
        )
        ax.bar_label(
            bars,
            labels=[
                f"{value:.0f}" if machine_no in count_by_machine else ""
                for machine_no, value in zip(
                    machine_numbers,
                    alarm_counts,
                )
            ],
            padding=3,
            fontsize=9,
        )

        ax.axhline(
            y=REFERENCE_COUNT,
            color="red",
            linestyle=":",
            linewidth=1.5,
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
        ax.set_title(f"{CHART_TITLE}({production_date})", loc="left", pad=24)
        ax.set_xlabel(CHART_X_LABEL)
        ax.set_ylabel(CHART_Y_LABEL)

        max_value = max(REFERENCE_COUNT, max(alarm_counts))
        ax.set_ylim(0, max_value * 1.1)
        ax.yaxis.get_major_locator().set_params(integer=True)
        ax.set_axisbelow(True)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(
            loc="lower right",
            bbox_to_anchor=(1, 1.02),
            ncol=1,
            borderaxespad=0,
            fontsize=9,
            handlelength=1.2,
            handletextpad=0.4,
            columnspacing=1.0,
            frameon=False,
        )

        for x, machine_no in zip(positions, machine_numbers):
            if machine_no not in count_by_machine:
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
    # Tkinterに組み込む場合: figure = MachineAlarmCountChart()
    figure = plt.figure(FigureClass=MachineAlarmCountChart)
    figure.update(
        machine_numbers=machine_numbers,
        machine_types=machine_types,
        production_date=production_date,
        db_file=db_file,
    )

    plt.show()