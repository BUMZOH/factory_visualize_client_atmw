"""指定した1台の設備について、定時内・定時外の稼働時間を期間表示する。"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from common_lib_mw import opdata_generator
from matplotlib.figure import Figure


# ================================================
#   Settings
# ================================================
DB_DIR = Path(
    r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl"
    r"\operation_data"
)

CHART_TITLE = "定時内・定時外の機械稼働時間"
CHART_X_LABEL = "日付"
CHART_Y_LABEL = "稼働時間（分）"
REGULAR_COLOR = "yellowgreen"
OUTSIDE_REGULAR_COLOR = "darkorange"
REGULAR_TIME = 432  # 定時8:00～17:00の基準時間の80%
FULL_REGULAR_TIME = 540  # 定時8:00～17:00の9時間


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
class MachineOperatingTimePeriodChart(Figure):
    def update(
        self,
        machine_no: int,
        start_date: str,
        end_date: str,
        db_file: str,
    ) -> None:
        """指定した1台の設備について、指定期間の稼働時間を表示する。"""

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
            time_by_date = self._get_main_factory_data(
                db_path,
                machine_no,
                start_date,
                end_date,
            )
        elif db_file == "machine_operation.db":
            time_by_date = self._get_shine_factory_data(
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
            time_by_date,
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
                       regular_auto_time,
                       all_auto_time
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
            production_date: (
                regular_time,
                all_time - regular_time,
            )
            for production_date, regular_time, all_time in rows
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
                       all_data
                FROM operation_data
                WHERE machine_no = ?
                  AND date BETWEEN ? AND ?
                ORDER BY date
                """,
                (machine_no, start_date, end_date),
            ).fetchall()
        finally:
            conn.close()

        time_by_date = {}

        for production_date, all_data_text in rows:
            data = [int(value) for value in all_data_text.split(",")]

            regular_time = opdata_generator.get_run_time(data)
            all_time = opdata_generator.get_all_run_time(data)
            outside_regular_time = all_time - regular_time

            time_by_date[production_date] = (
                regular_time,
                outside_regular_time,
            )

        return time_by_date

    def _draw_chart(
        self,
        machine_no: int,
        dates: list[str],
        start_date: str,
        end_date: str,
        time_by_date: dict,
    ) -> None:
        default = (0, 0)

        regular_times = [
            time_by_date.get(date, default)[0] for date in dates
        ]
        outside_regular_times = [
            time_by_date.get(date, default)[1] for date in dates
        ]

        positions = list(range(len(dates)))

        self.clear()
        ax = self.add_subplot(111)

        ax.bar(
            positions,
            regular_times,
            color=REGULAR_COLOR,
            label="定時内稼働時間",
            edgecolor="gray",
            linewidth=1,
        )

        ax.bar(
            positions,
            outside_regular_times,
            bottom=regular_times,
            color=OUTSIDE_REGULAR_COLOR,
            label="定時外稼働時間",
            edgecolor="gray",
            linewidth=1,
        )

        # 各要素の中央に時間を整数表示する（0の要素は省略）。
        for bars in ax.containers:
            ax.bar_label(
                bars,
                labels=[
                    f"{bar.get_height():.0f}"
                    if bar.get_height() > 0
                    else ""
                    for bar in bars
                ],
                label_type="center",
                fontsize=9,
            )

        # 棒の上に定時内＋定時外の合計稼働時間を表示する。
        for x, date, regular_time, outside_time in zip(
            positions,
            dates,
            regular_times,
            outside_regular_times,
        ):
            if date in time_by_date:
                total_time = regular_time + outside_time

                ax.annotate(
                    f"{total_time:.0f}",
                    (x, total_time),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
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

        max_total = max(
            regular + outside
            for regular, outside in zip(
                regular_times,
                outside_regular_times,
            )
        )

        ax.set_ylim(
            0,
            max(FULL_REGULAR_TIME, max_total) * 1.1,
        )

        ax.axhline(
            y=REGULAR_TIME,
            color="red",
            linestyle=":",
            linewidth=1.5,
        )

        ax.axhline(
            y=FULL_REGULAR_TIME,
            color="black",
            linewidth=0.5,
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
            if date not in time_by_date:
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

        # 対象期間の定時内・定時外・総合計をグラフ左下に表示する。
        total_regular_time = sum(regular_times)
        total_outside_regular_time = sum(outside_regular_times)
        total_time = total_regular_time + total_outside_regular_time

        self.tight_layout(rect=(0, 0.10, 1, 1))

        self.text(
            0.08,
            0.08,
            f"定時内合計 = {total_regular_time:,.0f}分 "
            f"({total_regular_time / 60:.1f}h)    "
            f"定時外合計 = {total_outside_regular_time:,.0f}分 "
            f"({total_outside_regular_time / 60:.1f}h)    "
            f"総合計 = {total_time:,.0f}分 ({total_time / 60:.1f}h)",
            ha="left",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "Yu Gothic"
    plt.rcParams["axes.unicode_minus"] = False

    factory = "shine"  # "main" or "shine" で切り替え

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
        FigureClass=MachineOperatingTimePeriodChart
    )
    figure.update(
        machine_no=machine_no,
        start_date=start_date,
        end_date=end_date,
        db_file=db_file,
    )

    plt.show()