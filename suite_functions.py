from tkinter import Frame, Tk, IntVar


def fix_resolution_issue():
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)


def resize_main(window, width, height):
    width, height = round(window.winfo_screenwidth() / width), \
        round(window.winfo_screenheight() / height)
    x = (window.winfo_screenwidth() - width) // 2
    y = (window.winfo_screenheight() - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


main: Tk | None = None
rows: IntVar | None = None
columns: IntVar | None = None


def initiate_grid():
    from tkinter import IntVar
    global rows, columns

    rows = IntVar()
    columns = IntVar()

    def update_rows():
        for a in range(main.grid_size()[1]):
            main.rowconfigure(a, weight=0)

        for a in range(rows.get()):
            main.rowconfigure(a, weight=1)

    def update_columns():
        for a in range(main.grid_size()[0]):
            main.columnconfigure(a, weight=0)

        for a in range(columns.get()):
            main.columnconfigure(a, weight=1)

    rows.trace("w", lambda *_: update_rows())
    columns.trace("w", lambda *_: update_columns())


def custom_rows(*rows_):
    rows.set(len(rows_))
    for i, r in enumerate(rows_):
        main.rowconfigure(i, weight=r)


def custom_columns(*columns_):
    columns.set(len(columns_))
    for i, c in enumerate(columns_):
        main.columnconfigure(i, weight=c)


class ScrollingFrame(Frame):
    def __init__(self, frame_kwargs=None, **kwargs):
        if frame_kwargs is None:
            frame_kwargs = {}
        from tkinter import Canvas, Scrollbar

        self.frame = Frame(**frame_kwargs)
        self.frame.grid_propagate(False)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        self.canvas = Canvas(self.frame, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = Scrollbar(self.frame, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind_all("<MouseWheel>", self.mouse_scroll)
        self.canvas.bind("<Enter>", lambda _: self.canvas.bind_all("<MouseWheel>", self.mouse_scroll))
        self.canvas.bind("<Leave>", lambda _: self.canvas.unbind_all("<MouseWheel>"))

        super().__init__(self.canvas, **kwargs)
        self.id = self.canvas.create_window((0, 0), window=self, anchor="nw")

        self.canvas.bind("<Configure>", lambda event: (self.canvas.configure(scrollregion=self.canvas.bbox("all")),
                                                       self.canvas.itemconfig(self.id, width=event.width)))
        self.bind("<Configure>", lambda _: (self.canvas.configure(scrollregion=self.canvas.bbox("all")),
                                            self.canvas.configure(background=self.cget("background"))))

    def mouse_scroll(self, event):
        from tkinter import TclError

        try:
            current_scroll = self.canvas.yview()
            step_size = 0.045
            move = -step_size if event.delta > 0 else step_size
            new_scroll = current_scroll[0] + move
            self.canvas.yview_moveto(max(0.0, min(1.0, new_scroll)))

        except TclError:
            self.canvas.unbind_all("<MouseWheel>")


class Border(Frame):
    def __init__(self, frame_kwargs=None, **grid_kwargs):
        super().__init__(background="#000000", width=1, **{} if frame_kwargs is None else frame_kwargs)
        if len(grid_kwargs) > 0:
            self.grid(**grid_kwargs)


class QFrame(Frame):
    def __init__(self, **kwargs):
        super().__init__()
        self.grid(**kwargs)


class ToolTip(object):
    """
    Shamefully copied from my python module :(
    """
    def __init__(self, widget, text, wait_time=250, x_offset=25, y_offset=5, **kwargs):
        self.wait_time = wait_time
        self.widget = widget
        self.text = text
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.kwargs = kwargs
        self.id = None
        self.tw = None
        self.positioned = False

        self.widget.bind("<Enter>", lambda _: self.enter(), add=True)
        self.widget.bind("<Leave>", lambda _: self.leave(), add=True)
        self.widget.bind("<ButtonPress>", lambda _: self.leave(), add=True)

    def enter(self):
        self.schedule()

    def leave(self):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.wait_time, self.showtip)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def showtip(self):
        from tkinter import Toplevel, Label, LEFT, SOLID
        if not self.tw:
            self.tw = Toplevel(self.widget)
            self.tw.wm_overrideredirect(True)

        if not self.positioned:
            self.update_tooltip_position()
            self.positioned = True

        label = Label(self.tw, text=self.text() if callable(self.text) else self.text,
                      justify=self.kwargs.get("justify", LEFT),
                      background=self.kwargs.get("bg", "#ffffff"),
                      foreground=self.kwargs.get("fg", "#000000"),
                      font=self.kwargs.get("font", None),
                      relief=self.kwargs.get("relief", SOLID),
                      borderwidth=self.kwargs.get("borderwidth", 1),
                      wraplength=self.kwargs.get("wraplength", 180))
        label.pack(ipadx=1)

    def update_tooltip_position(self):
        x = self.widget.winfo_pointerx() + (self.x_offset() if callable(self.x_offset) else self.x_offset)
        y = self.widget.winfo_pointery() + (self.y_offset() if callable(self.y_offset) else self.y_offset)
        self.tw.wm_geometry(f"+{x}+{y}")

    def hidetip(self):
        if self.tw:
            self.tw.destroy()
            self.tw = None
            self.positioned = False
