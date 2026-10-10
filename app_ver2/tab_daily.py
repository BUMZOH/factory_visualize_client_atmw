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

from chart_regular_time_status import RegularTimeMachineStatusChart
from chart_operating_time import MachineOperatingTimeChart
from chart_production import MachineProductionChart
from chart_alarm_count import MachineAlarmCountChart
from style import apply_style

plt.rcParams["font.family"] = "Yu Gothic"
plt.rcParams["axes.unicode_minus"] = False


# ================================================
#   Settings
# ================================================
PAGE_TITLE = "■ 日別"
BASE_DIR = Path(__file__).resolve().parent
LAYOUT_PATH = BASE_DIR / "factory_machine_layout.json"

# 配置順：左上、右上、左下、右下
CHART_CLASSES = [
    RegularTimeMachineStatusChart,
    MachineOperatingTimeChart,
    MachineProductionChart,
    MachineAlarmCountChart,
]


class DailyTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)

        # Load area definitions once at startup.
        self.factory_machine_layout = {}
        try:
            with LAYOUT_PATH.open(encoding="utf-8") as file:
                layout = json.load(file)
            if not isinstance(layout, dict):
                raise ValueError("エリア定義はJSONオブジェクトにしてください。")
            for area, data in layout.items():
                machine_numbers = data["machine_numbers"]
                machine_types = data["machine_types"]

                if len(machine_numbers) != len(machine_types):
                    raise ValueError(
                        f"{area}: machine_numbersとmachine_typesの要素数が一致しません。"
                    )
            self.factory_machine_layout = layout
        except (OSError, ValueError, KeyError) as error:
            messagebox.showerror("エリア設定エラー", str(error), parent=self)

        # Title
        title_frame = ttk.Frame(self, padding=10)
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text=PAGE_TITLE, style="Title.TLabel").pack(anchor=tk.W)
        ttk.Separator(title_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(8, 0))

        # Search conditions
        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="対象エリア:").grid(row=0, column=0, padx=5)
        self.area_combo = ttk.Combobox(
            search_frame,
            values=list(self.factory_machine_layout.keys()),
            state="readonly",
            width=24,
            font=("Yu Gothic", 12),
        )
        self.area_combo.grid(row=0, column=1, padx=5)
        self.area_combo.set("選択なし")
        self.area_combo.bind("<<ComboboxSelected>>", self.search)
        self.area_combo.bind("<Return>", self.search)

        ttk.Label(search_frame, text="対象日:").grid(row=0, column=2, padx=(15, 5))
        self.date_entry = ttk.Entry(search_frame, width=12, font=("Yu Gothic", 12))
        self.date_entry.grid(row=0, column=3, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.bind("<Return>", self.search)
        self.date_entry.bind("<Up>", lambda event: self.change_date(self.date_entry, -1))
        self.date_entry.bind("<Down>", lambda event: self.change_date(self.date_entry, 1))
        self.date_entry.bind("<Control-Up>", lambda event: self.change_month(self.date_entry, -1))
        self.date_entry.bind("<Control-Down>", lambda event: self.change_month(self.date_entry, 1))

        self.search_button = ttk.Button(search_frame, text="検索", command=self.search)
        self.search_button.grid(row=0, column=4, padx=(15, 5))
        self.search_button.bind("<Return>", self.search)

        self.capture_button = ttk.Button(search_frame, text="キャプチャ",command=self.capture_window)
        self.capture_button.grid(row=0, column=5, padx=(60, 5))

        # Four charts in a 2 x 2 grid
        self.chart_frame = ttk.Frame(self)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        for index in range(2):
            self.chart_frame.rowconfigure(index, weight=1, uniform="chart_rows")
            self.chart_frame.columnconfigure(index, weight=1, uniform="chart_columns")

        self.figures = []
        self.canvases = []
        for index, chart_class in enumerate(CHART_CLASSES):
            frame = ttk.Frame(self.chart_frame, padding=5)
            frame.grid(row=index // 2, column=index % 2, sticky="nsew")
            # Canvasの要求サイズによらず、各セルを均等に伸縮させる。
            frame.grid_propagate(False)
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            figure = chart_class(figsize=(5, 3), dpi=100)
            canvas = FigureCanvasTkAgg(figure, master=frame)
            canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
            self.figures.append(figure)
            self.canvases.append(canvas)

    def search(self, event=None) -> None:
        """Validate shared conditions and update all four charts."""
        try:
            area = self.area_combo.get()
            if area not in self.factory_machine_layout:
                raise ValueError("対象エリアを選択してください。")

            area_data = self.factory_machine_layout[area]

            db_file = area_data["db_file"]
            machine_numbers = area_data["machine_numbers"]
            machine_types = area_data["machine_types"]
            date_text = self.date_entry.get().strip()
            date = datetime.strptime(date_text, "%Y-%m-%d")
            if date.strftime("%Y-%m-%d") != date_text:
                raise ValueError("対象日はYYYY-MM-DD形式で入力してください。")
        except ValueError as error:
            messagebox.showwarning("入力エラー", str(error), parent=self)
            return

        # Disable the search button while processing.
        self.search_button.config(text="処理中...", state=tk.DISABLED)
        self.update_idletasks()

        try:
            for figure, canvas in zip(self.figures, self.canvases):
                figure.update(
                    machine_numbers,
                    machine_types,
                    date_text,
                    db_file,
                )
                canvas.draw()
        except (sqlite3.Error, FileNotFoundError, ValueError, struct.error) as error:
            messagebox.showerror("データ取得エラー", str(error), parent=self)
        finally:
            self.search_button.config(text="検索", state=tk.NORMAL)

    def change_date(self, entry: ttk.Entry, days: int) -> str:
        """Up: previous day. Down: next day."""
        try:
            date = datetime.strptime(entry.get().strip(), "%Y-%m-%d")
            date += timedelta(days=days)
            entry.delete(0, tk.END)
            entry.insert(0, date.strftime("%Y-%m-%d"))
        except ValueError:
            pass
        return "break"

    def change_month(self, entry: ttk.Entry, direction: int) -> str:
        """Change the month and set the day to 1."""
        try:
            date = datetime.strptime(entry.get().strip(), "%Y-%m-%d")
            if direction == -1:
                if date.day == 1:
                    date -= timedelta(days=1)
                date = date.replace(day=1)
            elif direction == 1:
                date = (date.replace(day=1) + timedelta(days=32)).replace(day=1)
            else:
                return "break"
            entry.delete(0, tk.END)
            entry.insert(0, date.strftime("%Y-%m-%d"))
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
    root.title("Daily Dashboard")
    root.geometry("1400x850")
    root.minsize(1200, 800)
    daily_tab = DailyTab(root)
    daily_tab.pack(fill=tk.BOTH, expand=True)

    def on_close() -> None:
        daily_tab.close_charts()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
