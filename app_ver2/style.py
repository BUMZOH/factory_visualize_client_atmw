from tkinter import ttk


def apply_style() -> None:
    """Apply common widget styles."""
    style = ttk.Style()

    # Navigation frame
    style.configure(
        "Nav.TFrame",
        background="#1f2937",
    )

    # Navigation title
    style.configure(
        "NavTitle.TLabel",
        background="#1f2937",
        foreground="white",
        font=("Yu Gothic", 12, "bold"),
    )

    style.configure(
        "Version.TLabel",
        background="#1f2937",
        foreground="#d1d5db",
        font=("Yu Gothic", 11),
    )

    # Page title
    style.configure(
        "Title.TLabel",
        font=("Yu Gothic", 16, "bold"),
        foreground="#1f2937",
    )

    # Label
    style.configure(
        "TLabel",
        font=("Yu Gothic", 12),
    )

    # Entry
    style.configure(
        "TEntry",
        padding=(5, 5),
    )

    # Combobox
    style.configure(
        "TCombobox",
        padding=(5, 5),
    )

    # Combobox dropdown list
    style.master.option_add(
        "*TCombobox*Listbox.font",
        ("Yu Gothic", 12),
    )

    # Button
    style.configure(
        "TButton",
        font=("Yu Gothic", 12),
        padding=(10, 5),
    )

    # Notebook tab
    style.configure(
        "TNotebook.Tab",
        font=("Yu Gothic", 12),
        padding=(10, 5),
    )

    # Treeview
    style.configure(
        "Treeview",
        font=("Yu Gothic", 12),
        rowheight=30,
    )

    # Treeview heading
    style.configure(
        "Treeview.Heading",
        font=("Yu Gothic", 12, "bold"),
    )





# ================================================
# Notes
# ================================================
# The font size of text inside Entry and Combobox
# cannot be set using ttk.Style.
# Set the font when creating each widget.
#
# Example:
# ttk.Entry(
#     parent,
#     font=("Yu Gothic", 12),
# )
#
# ttk.Combobox(
#     parent,
#     font=("Yu Gothic", 12),
# )

