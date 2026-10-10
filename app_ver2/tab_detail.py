import sqlite3
import tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import ImageGrab, ImageTk
from chart_status_timeline import MachineStatusTimeline
from style import apply_style


# ================================================
#   Settings
# ================================================
PAGE_TITLE = "■ 詳細"

class DetailTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=10)

        # Title
        title_frame = ttk.Frame(self, padding=10)
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text=PAGE_TITLE, style="Title.TLabel").pack(anchor=tk.W)
        ttk.Separator(title_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(8, 0))

        # Search conditions
        search_frame = ttk.Frame(self, padding=10)
        search_frame.pack(fill=tk.X)

        ttk.Label(search_frame, text="対象機械:").grid(row=0, column=0, padx=5)
        self.machine_entry = ttk.Entry(search_frame, width=8, font=("Yu Gothic", 12))
        self.machine_entry.grid(row=0, column=1, padx=5)
        self.machine_entry.bind("<Return>", self.search)
        self.machine_entry.bind("<Up>", lambda event: self.change_machine(1))
        self.machine_entry.bind("<Down>", lambda event: self.change_machine(-1))

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

        self.capture_button = ttk.Button(search_frame, text="キャプチャ", command=self.capture_window)
        self.capture_button.grid(row=0, column=5, padx=(40, 5))

        # 1台分の画像を原寸で表示する。縦横スクロール対応。
        chart_frame = ttk.Frame(self)
        chart_frame.pack(fill=tk.BOTH, expand=True)
        chart_frame.rowconfigure(0, weight=1)
        chart_frame.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(chart_frame, background="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        y_scroll = ttk.Scrollbar(chart_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(chart_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.image = None  # PhotoImageの参照を保持する。
        self.timeline = MachineStatusTimeline()

    def search(self, event=None) -> None:
        """Validate one machine and one date, then display its timeline."""
        try:
            machine_text = self.machine_entry.get().strip()
            if not machine_text.isdecimal() or not 1 <= int(machine_text) <= 99:
                raise ValueError("対象機械は1〜99の整数を1つ入力してください。")
            machine_no = int(machine_text)
            date_text = self.date_entry.get().strip()
            date = datetime.strptime(date_text, "%Y-%m-%d")
            if date.strftime("%Y-%m-%d") != date_text:
                raise ValueError("対象日はYYYY-MM-DD形式で入力してください。")
        except ValueError as error:
            messagebox.showwarning("入力エラー", str(error), parent=self)
            return

        self.show_timeline(machine_no, date_text)

    def show_timeline(self, machine_no: int, production_date: str) -> None:
        """タイムライン部品へ検索条件を渡し、返された画像を表示する。"""
        try:
            image = self.timeline.update(machine_no, production_date)
            photo = ImageTk.PhotoImage(image, master=self.canvas) if image is not None else None
        except (sqlite3.Error, OSError, ValueError) as error:
            messagebox.showerror("データ取得エラー", str(error), parent=self)
            return

        self.canvas.delete("all")
        self.image = photo
        if photo is None:
            self.canvas.create_text(
                30, 25, anchor="nw", font=("Yu Gothic", 12),
                text=f"設備 {machine_no} / {production_date}: データなし",
            )
            self.canvas.configure(scrollregion=(0, 0, 1600, 80))
        else:
            self.canvas.create_image(0, 0, anchor="nw", image=photo)
            self.canvas.configure(scrollregion=(0, 0, photo.width(), photo.height()))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

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



    def change_machine(self, direction: int) -> str:
        """Up: +1. Down: -1. Keep the machine number between 1 and 99."""
        text = self.machine_entry.get().strip()
        if text.isdecimal():
            machine_no = max(1, min(99, int(text) + direction))
        else:
            machine_no = 1
        self.machine_entry.delete(0, tk.END)
        self.machine_entry.insert(0, str(machine_no))
        return "break"

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
        """app.pyの終了処理と同じAPIに合わせて画像を解放する。"""
        self.canvas.delete("all")
        self.image = None


if __name__ == "__main__":
    # 単独テスト：この2項目だけ変更する。
    TEST_MACHINE_NO = 1
    TEST_PRODUCTION_DATE = "2026-10-06"

    root = tk.Tk()
    apply_style()
    root.title("Machine Timeline")
    root.geometry("1600x700")
    detail_tab = DetailTab(root)
    detail_tab.pack(fill=tk.BOTH, expand=True)
    detail_tab.machine_entry.insert(0, str(TEST_MACHINE_NO))
    detail_tab.date_entry.delete(0, tk.END)
    detail_tab.date_entry.insert(0, TEST_PRODUCTION_DATE)
    # 通常の組込み時は自動検索しない。単独テストのみ指定の1台を表示。
    root.after_idle(lambda: detail_tab.show_timeline(TEST_MACHINE_NO, TEST_PRODUCTION_DATE))

    def on_close() -> None:
        detail_tab.close_charts()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
