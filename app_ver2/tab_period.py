import json
import sqlite3
import struct
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import ImageGrab

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from chart_alarm_count_period import MachineAlarmCountPeriodChart
from chart_operating_time_period import MachineOperatingTimePeriodChart
from chart_production_period import MachineProductionPeriodChart
from chart_regular_time_status_period import (
    RegularTimeMachineStatusPeriodChart,
)
from style import apply_style


plt.rcParams["font.family"] = "Yu Gothic"
plt.rcParams["axes.unicode_minus"] = False


# ================================================
#   Settings
# ================================================
PAGE_TITLE = "■ 期間"
BASE_DIR = Path(__file__).resolve().parent
LAYOUT_PATH = BASE_DIR / "factory_machine_layout.json"

# 配置順：左上、右上、左下、右下
CHART_CLASSES = [
    RegularTimeMachineStatusPeriodChart,
    MachineOperatingTimePeriodChart,
    MachineProductionPeriodChart,
    MachineAlarmCountPeriodChart,
]


# ================================================
#   Period tab
# ================================================
class PeriodTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)

        # Load machine definitions once at startup.
        self.factory_machine_layout = {}

        try:
            with LAYOUT_PATH.open(encoding="utf-8") as file:
                layout = json.load(file)

            if not isinstance(layout, dict):
                raise ValueError(
                    "エリア定義はJSONオブジェクトにしてください。"
                )

            for area, data in layout.items():
                machine_numbers = data["machine_numbers"]
                machine_types = data["machine_types"]
                db_file = data["db_file"]

                if len(machine_numbers) != len(machine_types):
                    raise ValueError(
                        f"{area}: machine_numbersとmachine_typesの"
                        "要素数が一致しません。"
                    )

                if not db_file:
                    raise ValueError(
                        f"{area}: db_fileが設定されていません。"
                    )

            self.factory_machine_layout = layout

        except (OSError, ValueError, KeyError) as error:
            messagebox.showerror(
                "エリア設定エラー",
                str(error),
                parent=self,
            )

        # Initial conditions
        today = datetime.today()
        first_day = today.replace(day=1)
        next_month = (
            first_day + timedelta(days=32)
        ).replace(day=1)
        last_day = next_month - timedelta(days=1)

        # Title
        title_frame = ttk.Frame(self, padding=10)
        title_frame.pack(fill=tk.X)

        ttk.Label(
            title_frame,
            text=PAGE_TITLE,
            style="Title.TLabel",
        ).pack(anchor=tk.W)

        ttk.Separator(
            title_frame,
            orient=tk.HORIZONTAL,
        ).pack(fill=tk.X, pady=(8, 0))

        # Search conditions
        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill=tk.X)

        ttk.Label(
            search_frame,
            text="機械番号:",
        ).grid(row=0, column=0, padx=5)

        self.machine_entry = ttk.Entry(
            search_frame,
            width=8,
            font=("Yu Gothic", 12),
        )
        self.machine_entry.grid(row=0, column=1, padx=5)
        self.machine_entry.insert(0, "1")
        self.machine_entry.bind("<Return>", self.search)
        self.machine_entry.bind(
            "<Up>",
            lambda event: self.change_machine(-1),
        )
        self.machine_entry.bind(
            "<Down>",
            lambda event: self.change_machine(1),
        )

        ttk.Label(
            search_frame,
            text="開始期間:",
        ).grid(row=0, column=2, padx=(15, 5))

        self.start_date_entry = ttk.Entry(
            search_frame,
            width=12,
            font=("Yu Gothic", 12),
        )
        self.start_date_entry.grid(row=0, column=3, padx=5)
        self.start_date_entry.insert(
            0,
            first_day.strftime("%Y-%m-%d"),
        )
        self.start_date_entry.bind("<Return>", self.search)
        self.start_date_entry.bind(
            "<Up>",
            lambda event: self.change_date(
                self.start_date_entry,
                -1,
            ),
        )
        self.start_date_entry.bind(
            "<Down>",
            lambda event: self.change_date(
                self.start_date_entry,
                1,
            ),
        )
        self.start_date_entry.bind(
            "<Control-Up>",
            lambda event: self.change_month(
                self.start_date_entry,
                -1,
            ),
        )
        self.start_date_entry.bind(
            "<Control-Down>",
            lambda event: self.change_month(
                self.start_date_entry,
                1,
            ),
        )

        ttk.Label(
            search_frame,
            text="終了期間:",
        ).grid(row=0, column=4, padx=(15, 5))

        self.end_date_entry = ttk.Entry(
            search_frame,
            width=12,
            font=("Yu Gothic", 12),
        )
        self.end_date_entry.grid(row=0, column=5, padx=5)
        self.end_date_entry.insert(
            0,
            last_day.strftime("%Y-%m-%d"),
        )
        self.end_date_entry.bind("<Return>", self.search)
        self.end_date_entry.bind(
            "<Up>",
            lambda event: self.change_date(
                self.end_date_entry,
                -1,
            ),
        )
        self.end_date_entry.bind(
            "<Down>",
            lambda event: self.change_date(
                self.end_date_entry,
                1,
            ),
        )
        self.end_date_entry.bind(
            "<Control-Up>",
            lambda event: self.change_month(
                self.end_date_entry,
                -1,
            ),
        )
        self.end_date_entry.bind(
            "<Control-Down>",
            lambda event: self.change_month(
                self.end_date_entry,
                1,
            ),
        )

        self.search_button = ttk.Button(
            search_frame,
            text="検索",
            command=self.search,
        )
        self.search_button.grid(
            row=0,
            column=6,
            padx=(15, 5),
        )
        self.search_button.bind("<Return>", self.search)

        self.capture_button = ttk.Button(
            search_frame,
            text="キャプチャ",
            command=self.capture_window,
        )
        self.capture_button.grid(
            row=0,
            column=7,
            padx=(60, 5),
        )

        # Four charts in a 2 x 2 grid
        self.chart_frame = ttk.Frame(self)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        for index in range(2):
            self.chart_frame.rowconfigure(
                index,
                weight=1,
                uniform="chart_rows",
            )
            self.chart_frame.columnconfigure(
                index,
                weight=1,
                uniform="chart_columns",
            )

        self.figures = []
        self.canvases = []

        for index, chart_class in enumerate(CHART_CLASSES):
            frame = ttk.Frame(
                self.chart_frame,
                padding=5,
            )
            frame.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
            )

            # Canvasの要求サイズによらず、各セルを均等に伸縮させる。
            frame.grid_propagate(False)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)

            figure = chart_class(
                figsize=(5, 3),
                dpi=100,
            )
            canvas = FigureCanvasTkAgg(
                figure,
                master=frame,
            )
            canvas.get_tk_widget().grid(
                row=0,
                column=0,
                sticky="nsew",
            )

            self.figures.append(figure)
            self.canvases.append(canvas)

    def search(self, event=None) -> None:
        """Validate shared conditions and update all four charts."""
        try:
            machine_text = self.machine_entry.get().strip()

            if not machine_text:
                raise ValueError("機械番号を入力してください。")

            machine_no = int(machine_text)

            if machine_no < 1:
                raise ValueError(
                    "機械番号は1以上で入力してください。"
                )

            db_file = self.get_db_file(machine_no)

            start_date_text = self.start_date_entry.get().strip()
            end_date_text = self.end_date_entry.get().strip()

            start_date = datetime.strptime(
                start_date_text,
                "%Y-%m-%d",
            )
            end_date = datetime.strptime(
                end_date_text,
                "%Y-%m-%d",
            )

            if start_date.strftime("%Y-%m-%d") != start_date_text:
                raise ValueError(
                    "開始期間はYYYY-MM-DD形式で入力してください。"
                )

            if end_date.strftime("%Y-%m-%d") != end_date_text:
                raise ValueError(
                    "終了期間はYYYY-MM-DD形式で入力してください。"
                )

            if start_date > end_date:
                raise ValueError(
                    "開始期間は終了期間以前にしてください。"
                )

        except ValueError as error:
            messagebox.showwarning(
                "入力エラー",
                str(error),
                parent=self,
            )
            return

        # Disable the search button while processing.
        self.search_button.config(
            text="処理中...",
            state=tk.DISABLED,
        )
        self.update_idletasks()

        try:
            for figure, canvas in zip(
                self.figures,
                self.canvases,
            ):
                figure.update(
                    machine_no,
                    start_date_text,
                    end_date_text,
                    db_file,
                )
                canvas.draw()

        except (
            sqlite3.Error,
            FileNotFoundError,
            ValueError,
            struct.error,
        ) as error:
            messagebox.showerror(
                "データ取得エラー",
                str(error),
                parent=self,
            )

        finally:
            self.search_button.config(
                text="検索",
                state=tk.NORMAL,
            )

    def get_db_file(self, machine_no: int) -> str:
        """機械番号から使用するDBファイルを取得する。"""
        for area_data in self.factory_machine_layout.values():
            if machine_no in area_data["machine_numbers"]:
                return area_data["db_file"]

        raise ValueError(
            f"機械番号 {machine_no} はエリア定義に登録されていません。"
        )

    def change_machine(self, direction: int) -> str:
        """Up: previous machine. Down: next machine."""
        try:
            machine_no = int(self.machine_entry.get().strip())
            machine_no += direction

            if machine_no < 1:
                machine_no = 1

            self.machine_entry.delete(0, tk.END)
            self.machine_entry.insert(0, str(machine_no))

        except ValueError:
            pass

        return "break"

    def change_date(
        self,
        entry: ttk.Entry,
        days: int,
    ) -> str:
        """Up: previous day. Down: next day."""
        try:
            date = datetime.strptime(
                entry.get().strip(),
                "%Y-%m-%d",
            )
            date += timedelta(days=days)

            entry.delete(0, tk.END)
            entry.insert(
                0,
                date.strftime("%Y-%m-%d"),
            )

        except ValueError:
            pass

        return "break"

    def change_month(
        self,
        entry: ttk.Entry,
        direction: int,
    ) -> str:
        """Change the month and set the day to 1."""
        try:
            date = datetime.strptime(
                entry.get().strip(),
                "%Y-%m-%d",
            )

            if direction == -1:
                if date.day == 1:
                    date -= timedelta(days=1)

                date = date.replace(day=1)

            elif direction == 1:
                date = (
                    date.replace(day=1)
                    + timedelta(days=32)
                ).replace(day=1)

            else:
                return "break"

            entry.delete(0, tk.END)
            entry.insert(
                0,
                date.strftime("%Y-%m-%d"),
            )

        except ValueError:
            pass

        return "break"

    def close_charts(self) -> None:
        """Close all figures owned by this page."""
        for figure in self.figures:
            plt.close(figure)

    def capture_window(self) -> None:
        """アプリウィンドウをキャプチャしてPicturesフォルダへ保存する。"""
        window = self.winfo_toplevel()

        x = window.winfo_rootx()
        y = window.winfo_rooty()
        width = window.winfo_width()
        height = window.winfo_height()

        bbox = (
            x,
            y,
            x + width,
            y + height,
        )

        pictures_dir = Path.home() / "Pictures"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = pictures_dir / f"capture_{timestamp}.png"

        image = ImageGrab.grab(bbox=bbox)
        image.save(file_path)

        messagebox.showinfo(
            "キャプチャ",
            f"保存しました。\n\n{file_path}",
            parent=self,
        )


if __name__ == "__main__":
    root = tk.Tk()

    apply_style()

    root.title("Period Dashboard")
    root.geometry("1400x850")
    root.minsize(1200, 800)

    period_tab = PeriodTab(root)
    period_tab.pack(
        fill=tk.BOTH,
        expand=True,
    )

    def on_close() -> None:
        period_tab.close_charts()
        root.destroy()

    root.protocol(
        "WM_DELETE_WINDOW",
        on_close,
    )
    root.mainloop()