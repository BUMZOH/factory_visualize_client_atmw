"""設備別の定時内自動運転時間・材料切れ時間・段替え時間・故障時間・アラーム時間・刃具交換時間を積み上げ表示する。"""
import sqlite3
import struct
from datetime import datetime
from pathlib import Path

from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter


# ================================================
#   Settings
# ================================================
BASE_DIR = Path(__file__).resolve().parent
# DB_PATH = BASE_DIR / "main_factory_production_data.db"
DB_PATH = Path(r"\\192.168.2.1\共有ファイル\M-光和共有ファイル\P_ProductControl\operation_data\main_factory_production_data.db")

CHART_TITLE = "定時内の機械稼働状況"
CHART_X_LABEL = "設備番号"
CHART_Y_LABEL = "定時時間に対する割合（%）"
AUTO_COLOR = "yellowgreen"
MATERIAL_OUT_COLOR = "yellow"
CHANGEOVER_COLOR = "tab:blue"
BREAKDOWN_COLOR = "tab:red"
ALARM_COLOR = "tab:pink"
TOOL_CHANGE_COLOR = "tab:cyan"

# index=10が4:00。8:00～16:59の540個を定時として扱う。
REGULAR_START = 10 + 4 * 60   # index=250（8:00）
REGULAR_END = 10 + 13 * 60   # index=790（17:00、含めない）
REGULAR_TIME = 540   # 540分を100%とする
CHANGEOVER_CODE = 2
BREAKDOWN_CODE = 3
ALARM_CODE = 20
TOOL_CHANGE_CODE = 1


# ================================================
#   Chart
# ================================================
class RegularTimeMachineStatusChart(Figure):
    def update(
        self,
        machine_numbers: list[int],
        machine_types: list[str],
        production_date: str,
    ) -> None:
        """指定した1生産日の時間を設備別に表示する。

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
        if not DB_PATH.is_file():
            raise FileNotFoundError(DB_PATH)

        placeholders = ", ".join("?" for _ in machine_numbers)
        # 読み取り専用で開く。DBファイルの新規作成や更新は行わない。
        conn = sqlite3.connect(DB_PATH)
        try:
            rows = conn.execute(
                f"""
                SELECT machine_no,
                       regular_auto_time,
                       regular_material_out_time,
                       all_data
                FROM operation_data
                WHERE machine_no IN ({placeholders})
                  AND production_date = ?
                """,
                (*machine_numbers, production_date),
            ).fetchall()
        finally:
            conn.close()

        time_by_machine = {}
        for machine_no, auto_time, material_time, blob_data in rows:
            # 保存プログラムと同じ形式：リトルエンディアンの16ビット整数1500個。
            data = struct.unpack("<1500H", blob_data)
            changeover_time = data[REGULAR_START:REGULAR_END].count(CHANGEOVER_CODE)
            breakdown_time = data[REGULAR_START:REGULAR_END].count(BREAKDOWN_CODE)
            alarm_time = data[REGULAR_START:REGULAR_END].count(ALARM_CODE)
            tool_change_time = data[REGULAR_START:REGULAR_END].count(TOOL_CHANGE_CODE)
            time_by_machine[machine_no] = (
                auto_time, material_time, changeover_time, breakdown_time,
                alarm_time, tool_change_time,
            )
        auto_times = [time_by_machine.get(n, (0, 0, 0, 0, 0, 0))[0] for n in machine_numbers]
        material_times = [time_by_machine.get(n, (0, 0, 0, 0, 0, 0))[1] for n in machine_numbers]
        changeover_times = [time_by_machine.get(n, (0, 0, 0, 0, 0, 0))[2] for n in machine_numbers]
        breakdown_times = [time_by_machine.get(n, (0, 0, 0, 0, 0, 0))[3] for n in machine_numbers]
        alarm_times = [time_by_machine.get(n, (0, 0, 0, 0, 0, 0))[4] for n in machine_numbers]
        tool_change_times = [time_by_machine.get(n, (0, 0, 0, 0, 0, 0))[5] for n in machine_numbers]
        # 定時540分を100%として、各状態の時間を割合に換算する。
        auto_times = [t / REGULAR_TIME * 100 for t in auto_times]
        material_times = [t / REGULAR_TIME * 100 for t in material_times]
        changeover_times = [t / REGULAR_TIME * 100 for t in changeover_times]
        tool_change_times = [t / REGULAR_TIME * 100 for t in tool_change_times]
        alarm_times = [t / REGULAR_TIME * 100 for t in alarm_times]
        breakdown_times = [t / REGULAR_TIME * 100 for t in breakdown_times]
        positions = list(range(len(machine_numbers)))

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
        ax.bar(
            positions,
            changeover_times,
            bottom=[a + m for a, m in zip(auto_times, material_times)],
            color=CHANGEOVER_COLOR,
            label="段替え",
            edgecolor="gray",
            linewidth=1,
        )
        tool_change_bottom = [
            a + m + c
            for a, m, c in zip(auto_times, material_times, changeover_times)
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
        ax.bar(
            positions,
            breakdown_times,
            bottom=[b + a for b, a in zip(alarm_bottom, alarm_times)],
            color=BREAKDOWN_COLOR,
            label="故障",
            edgecolor="gray",
            linewidth=1,
        )
        # 各積み上げ要素の中央に割合を整数表示する（0の要素は省略）。
        for bars in ax.containers:
            ax.bar_label(
                bars,
                labels=[f"{bar.get_height():.0f}%" if bar.get_height() > 0 else "" for bar in bars],
                label_type="center",
                fontsize=9,
            )

        ax.set_xticks(
            positions,
            [f"{number}\n{machine_type}" for number, machine_type in zip(machine_numbers, machine_types)],
        )
        ax.set_title(f"{CHART_TITLE}({production_date})", loc="left", pad=24)
        ax.set_xlabel(CHART_X_LABEL)
        ax.set_ylabel(CHART_Y_LABEL)
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax.axhline(y=80, color="red", linestyle=":", linewidth=1.5)
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

        for x, machine_no in zip(positions, machine_numbers):
            if machine_no not in time_by_machine:
                ax.annotate(
                    "データなし", (x, 0), xytext=(0, 5),
                    textcoords="offset points", ha="center", fontsize=9,
                )
        self.tight_layout()


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "Yu Gothic"
    plt.rcParams["axes.unicode_minus"] = False

    machine_numbers = [
        1, 3, 4, 6, 7, 10, 12, 13, 14, 17, 30, 32, 40
    ]

    machine_types = [
        "KDP", "KDP", "KDP", "KDP", "KDP", "KDP", "KDP",
        "KDP", "KDP", "KDP", "KDP", "KDP", "KDPN",
    ]

    # 単体確認ではplt.show()用にpyplot経由で生成する。
    # Tkinterに組み込む場合: figure = RegularTimeMachineStatusChart()
    figure = plt.figure(FigureClass=RegularTimeMachineStatusChart)
    figure.update(
        machine_numbers=machine_numbers,
        machine_types=machine_types,
        production_date="2026-10-06",
    )

    plt.show()
