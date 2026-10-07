import tkinter as tk
from tkinter import ttk

from tab_daily import DailyTab
from tab_detail import DetailTab
from style import apply_style


# ================================================
#   Settings
# ================================================
WINDOW_TITLE = "Factory Production Dashboard"
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 950

APP_VERSION = "Ver.20261007-1"

NAV_BUTTONS = [
    ("日別", DailyTab),
    ("詳細", DetailTab),
]


# ================================================
#   Main window
# ================================================
root = tk.Tk()

apply_style()

root.title(WINDOW_TITLE)
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")


# ================================================
#   Navigation frame
# ================================================
nav_frame = ttk.Frame(
    root,
    width=160,
    # borderwidth=1,
    # relief="solid",
    style="Nav.TFrame",
    padding=10,
)

nav_frame.pack(
    side=tk.LEFT,
    fill=tk.Y,
)

nav_frame.pack_propagate(False)


# ================================================
#   Main frame
# ================================================
main_frame = ttk.Frame(
    root,
    # borderwidth=1,
    # relief="solid",
)

main_frame.pack(
    side=tk.LEFT,
    fill=tk.BOTH,
    expand=True,
)


# ================================================
#   Pages
# ================================================
pages = []

for _, page_class in NAV_BUTTONS:
    page = page_class(main_frame)
    page.place(
        x=0,
        y=0,
        relwidth=1,
        relheight=1,
    )
    pages.append(page)


# ================================================
#   Page switching
# ================================================
def show_page(page):
    page.tkraise()


# ================================================
#   Navigation title
# ================================================
ttk.Label(
    nav_frame,
    text="MENU",
    style="NavTitle.TLabel",
).pack(
    padx=10,
    pady=(30, 5),
)


# ================================================
#   Navigation buttons
# ================================================
for (button_text, _), page in zip(NAV_BUTTONS, pages):
    button = ttk.Button(
        nav_frame,
        text=button_text,
        command=lambda p=page: show_page(p),
    )

    button.pack(
        fill=tk.X,
        padx=10,
        pady=5,
    )

show_page(pages[0])


# ================================================
#   Version
# ================================================
version_label = ttk.Label(
    nav_frame,
    text=APP_VERSION,
    style="Version.TLabel",
)

version_label.pack(
    side=tk.BOTTOM,
    pady=10,
)


# ================================================
#   Close
# ================================================
def on_close() -> None:
    """Close matplotlib and destroy the Tkinter window."""
    for page in pages:
        page.close_charts()

    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)


# ================================================
#   Start
# ================================================
root.mainloop()