"""指定した1台の設備について、生産実績と目標生産数を期間表示する。"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from matplotlib.figure import Figure


# ================================================
#   Settings
# ================================================
DB_DIR = Path(
    r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl"
    r"\operation_data"
)

CHART_TITLE = "生産実績・目標"
CHART_X_LABEL = "日付"
CHART_Y_LABEL = "生産数"
ACTUAL_COLOR = "tab:cyan"
TARGET_COLOR = "red"


def get_date_range(start_date: str, end_date: str) -> list[str]:
    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    if start > end:
        raise ValueError("開始日は終了日以前にしてください")

    dates = []
    current = start

    while current <= end:
        dates.append(current.isoformat())
        current += timedelta(days=1)

    return dates


# ================================================
#   Chart
# ================================================
class MachineProductionPeriodChart(Figure):
    def update(
        self,
        machine_no: int,
        start_date: str,
        end_date: str,
        db_file: str,
    ) -> None:
        """指定した1台の設備について、指定期間の生産実績と目標を表示する。"""

        start_date = datetime.strptime(
            start_date, "%Y-%m-%d"
        ).date().isoformat()

        end_date = datetime.strptime(
            end_date, "%Y-%m-%d"
        ).date().isoformat()

        dates = get_date_range(start_date, end_date)

        db_path = DB_DIR / db_file
        if not db_path.is_file():
            raise FileNotFoundError(db_path)

        if db_file == "main_factory_production_data.db":
            production_by_date = self._get_main_factory_data(
                db_path,
                machine_no,
                start_date,
                end_date,
            )
        elif db_file == "machine_operation.db":
            production_by_date = self._get_shine_factory_data(
                db_path,
                machine_no,
                start_date,
                end_date,
            )
        else:
            raise ValueError(f"未対応のDBです: {db_file}")

        self._draw_chart(
            machine_no,
            dates,
            start_date,
            end_date,
            production_by_date,
        )

    def _get_main_factory_data(
        self,
        db_path: Path,
        machine_no: int,
        start_date: str,
        end_date: str,
    ) -> dict:
        conn = sqlite3.connect(db_path)

        try:
            rows = conn.execute(
                """
                SELECT production_date,
                       actual_production,
                       target_production
                FROM operation_data
                WHERE machine_no = ?
                  AND production_date BETWEEN ? AND ?
                ORDER BY production_date
                """,
                (machine_no, start_date, end_date),
            ).fetchall()
        finally:
            conn.close()

        return {
            production_date: (actual, target)
            for production_date, actual, target in rows
        }

    def _get_shine_factory_data(
        self,
        db_path: Path,
        machine_no: int,
        start_date: str,
        end_date: str,
    ) -> dict:
        conn = sqlite3.connect(db_path)

        try:
            rows = conn.execute(
                """
                SELECT date,
                       actual_qty,
                       target_qty
                FROM operation_data
                WHERE machine_no = ?
                  AND date BETWEEN ? AND ?
                ORDER BY date
                """,
                (machine_no, start_date, end_date),
            ).fetchall()
        finally:
            conn.close()

        return {
            production_date: (actual, target)
            for production_date, actual, target in rows
        }

    def _draw_chart(
        self,
        machine_no: int,
        dates: list[str],
        start_date: str,
        end_date: str,
        production_by_date: dict,
    ) -> None:
        actual_values = [
            production_by_date.get(date, (0, 0))[0]
            for date in dates
        ]

        # データのない日は折れ線を途切れさせる。
        target_values = [
            production_by_date.get(date, (0, float("nan")))[1]
            for date in dates
        ]

        positions = list(range(len(dates)))

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
                f"{value:.0f}" if date in production_by_date else ""
                for date, value in zip(dates, actual_values)
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

        # 横軸には指定期間の全日付を表示する。
        date_labels = [
            datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d")
            for date in dates
        ]

        ax.set_xticks(
            positions,
            date_labels,
            rotation=90,
        )

        # 土曜日を青、日曜日を赤で表示する。
        for label, date in zip(ax.get_xticklabels(), dates):
            weekday = datetime.strptime(date, "%Y-%m-%d").weekday()

            if weekday == 5:
                label.set_color("blue")
            elif weekday == 6:
                label.set_color("red")

        ax.set_title(
            f"{CHART_TITLE} 設備{machine_no} "
            f"({start_date} ～ {end_date})",
            loc="left",
            pad=24,
        )
        ax.set_xlabel(CHART_X_LABEL)
        ax.set_ylabel(CHART_Y_LABEL)

        max_value = max(
            [0]
            + actual_values
            + [
                values[1]
                for values in production_by_date.values()
            ]
        )

        ax.set_ylim(
            0,
            max_value * 1.1 if max_value > 0 else 1,
        )

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

        # DBにレコードが存在しない日も横軸に残す。
        for x, date in zip(positions, dates):
            if date not in production_by_date:
                ax.annotate(
                    "データなし",
                    (x, 0),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    rotation=90,
                )

        # 対象期間の生産数合計を左下に表示する。
        total_production = sum(actual_values)

        # 対象期間の生産数合計をグラフ左下に表示する。
        total_production = sum(actual_values)

        self.tight_layout(rect=(0, 0.10, 1, 1))

        self.text(
            0.08,
            0.08,
            f"生産数合計 = {total_production:,.0f}",
            ha="left",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "Yu Gothic"
    plt.rcParams["axes.unicode_minus"] = False

    factory = "main"  # "main" or "shine" で切り替え

    if factory == "main":
        machine_no = 1
        start_date = "2026-09-01"
        end_date = "2026-09-30"
        db_file = "main_factory_production_data.db"

    elif factory == "shine":
        machine_no = 15
        start_date = "2026-09-01"
        end_date = "2026-09-30"
        db_file = "machine_operation.db"

    else:
        raise ValueError(f"未対応の工場です: {factory}")

    figure = plt.figure(
        FigureClass=MachineProductionPeriodChart
    )
    figure.update(
        machine_no=machine_no,
        start_date=start_date,
        end_date=end_date,
        db_file=db_file,
    )

    plt.show()