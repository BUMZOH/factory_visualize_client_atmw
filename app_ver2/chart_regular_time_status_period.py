"""指定した1台の設備について、定時内の機械稼働状況を期間表示する。"""

import sqlite3
import struct
from datetime import datetime, timedelta
from pathlib import Path

from common_lib_mw import opdata_generator
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter


# ================================================
#   Settings
# ================================================
DB_DIR = Path(
    r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl"
    r"\operation_data"
)

CHART_TITLE = "定時内の機械稼働状況"
CHART_X_LABEL = "日付"
CHART_Y_LABEL = "定時時間に対する割合（%）"
AUTO_COLOR = "yellowgreen"
MATERIAL_OUT_COLOR = "yellow"
CHANGEOVER_COLOR = "tab:blue"
BREAKDOWN_COLOR = "tab:red"
ALARM_COLOR = "tab:pink"
TOOL_CHANGE_COLOR = "tab:cyan"

# index=10が4:00。8:00～16:59の540個を定時として扱う。
REGULAR_START = 10 + 4 * 60
REGULAR_END = 10 + 13 * 60
REGULAR_TIME = 540
CHANGEOVER_CODE = 2
BREAKDOWN_CODE = 3
ALARM_CODE = 20
TOOL_CHANGE_CODE = 1


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
class RegularTimeMachineStatusPeriodChart(Figure):
    def update(
        self,
        machine_no: int,
        start_date: str,
        end_date: str,
        db_file: str,
    ) -> None:
        """指定した1台の設備について、指定期間の稼働状況を表示する。"""

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
                       regular_material_out_time,
                       all_data
                FROM operation_data
                WHERE machine_no = ?
                  AND production_date BETWEEN ? AND ?
                ORDER BY production_date
                """,
                (machine_no, start_date, end_date),
            ).fetchall()
        finally:
            conn.close()

        time_by_date = {}

        for production_date, auto_time, material_time, blob_data in rows:
            data = struct.unpack("<1500H", blob_data)

            changeover_time = data[
                REGULAR_START:REGULAR_END
            ].count(CHANGEOVER_CODE)

            breakdown_time = data[
                REGULAR_START:REGULAR_END
            ].count(BREAKDOWN_CODE)

            alarm_time = data[
                REGULAR_START:REGULAR_END
            ].count(ALARM_CODE)

            tool_change_time = data[
                REGULAR_START:REGULAR_END
            ].count(TOOL_CHANGE_CODE)

            time_by_date[production_date] = (
                auto_time,
                material_time,
                changeover_time,
                breakdown_time,
                alarm_time,
                tool_change_time,
            )

        return time_by_date

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

            auto_time = opdata_generator.get_run_time(data)
            material_time = opdata_generator.get_wait_time(data)
            changeover_time = opdata_generator.get_changeover_time(data)
            breakdown_time = opdata_generator.get_breakdown_time(data)
            alarm_time = opdata_generator.get_alarm_time(data)
            tool_change_time = opdata_generator.get_toolchange_time(data)

            time_by_date[production_date] = (
                auto_time,
                material_time,
                changeover_time,
                breakdown_time,
                alarm_time,
                tool_change_time,
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
        default = (0, 0, 0, 0, 0, 0)

        auto_times = [
            time_by_date.get(date, default)[0] for date in dates
        ]
        material_times = [
            time_by_date.get(date, default)[1] for date in dates
        ]
        changeover_times = [
            time_by_date.get(date, default)[2] for date in dates
        ]
        breakdown_times = [
            time_by_date.get(date, default)[3] for date in dates
        ]
        alarm_times = [
            time_by_date.get(date, default)[4] for date in dates
        ]
        tool_change_times = [
            time_by_date.get(date, default)[5] for date in dates
        ]

        # 定時540分を100%として、各状態の時間を割合に換算する。
        auto_times = [t / REGULAR_TIME * 100 for t in auto_times]
        material_times = [t / REGULAR_TIME * 100 for t in material_times]
        changeover_times = [t / REGULAR_TIME * 100 for t in changeover_times]
        tool_change_times = [
            t / REGULAR_TIME * 100 for t in tool_change_times
        ]
        alarm_times = [t / REGULAR_TIME * 100 for t in alarm_times]
        breakdown_times = [t / REGULAR_TIME * 100 for t in breakdown_times]

        positions = list(range(len(dates)))

        self.clear()
        ax = self.add_subplot(111)

        ax.bar(
            positions,
            auto_times,
            color=AUTO_COLOR,
            label="自動運転",
            edgecolor="gray",
            linewidth=1,
        )

        ax.bar(
            positions,
            material_times,
            bottom=auto_times,
            color=MATERIAL_OUT_COLOR,
            label="材料切れ",
            edgecolor="gray",
            linewidth=1,
        )

        changeover_bottom = [
            a + m for a, m in zip(auto_times, material_times)
        ]

        ax.bar(
            positions,
            changeover_times,
            bottom=changeover_bottom,
            color=CHANGEOVER_COLOR,
            label="段替え",
            edgecolor="gray",
            linewidth=1,
        )

        tool_change_bottom = [
            b + c for b, c in zip(changeover_bottom, changeover_times)
        ]

        ax.bar(
            positions,
            tool_change_times,
            bottom=tool_change_bottom,
            color=TOOL_CHANGE_COLOR,
            label="刃具交換",
            edgecolor="gray",
            linewidth=1,
        )

        alarm_bottom = [
            b + t for b, t in zip(tool_change_bottom, tool_change_times)
        ]

        ax.bar(
            positions,
            alarm_times,
            bottom=alarm_bottom,
            color=ALARM_COLOR,
            label="アラーム",
            edgecolor="gray",
            linewidth=1,
        )

        breakdown_bottom = [
            b + a for b, a in zip(alarm_bottom, alarm_times)
        ]

        ax.bar(
            positions,
            breakdown_times,
            bottom=breakdown_bottom,
            color=BREAKDOWN_COLOR,
            label="故障",
            edgecolor="gray",
            linewidth=1,
        )

        # 各積み上げ要素の中央に割合を整数表示する。
        for bars in ax.containers:
            ax.bar_label(
                bars,
                labels=[
                    f"{bar.get_height():.0f}%"
                    if bar.get_height() > 0
                    else ""
                    for bar in bars
                ],
                label_type="center",
                fontsize=9,
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
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))

        ax.axhline(
            y=80,
            color="red",
            linestyle=":",
            linewidth=1.5,
        )

        ax.set_axisbelow(True)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(
            loc="lower right",
            bbox_to_anchor=(1, 1.02),
            ncol=6,
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

        self.tight_layout()


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
        FigureClass=RegularTimeMachineStatusPeriodChart
    )
    figure.update(
        machine_no=machine_no,
        start_date=start_date,
        end_date=end_date,
        db_file=db_file,
    )

    plt.show()