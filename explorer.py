from tkinter import *
from os.path import isdir, basename, join, isfile, dirname, exists, expanduser
from os import listdir, stat, makedirs, rename
from tkinter.messagebox import showerror
from math import floor, log
from magic import Magic
from json import dump, load as load_json
from subprocess import run

import suite_functions as x_fun
from suite_functions import *

fix_resolution_issue()

main = Tk()
resize_main(main, 2, 2)
main.title("Alia Explorer")
main.iconbitmap("explorer.ico")
main.protocol("WM_DELETE_WINDOW", lambda: (save(), main.destroy()))

x_fun.main = main
initiate_grid()


def try_open(path=None):
    if path is None:
        path = user_settings["current_dir"]

    def open_path():
        if isdir(path):
            children = explorer.winfo_children()
            contents = [f for f in listdir(path) if isdir(join(path, f))] + ["|s"] + \
                       [f for f in listdir(path) if isfile(join(path, f))]

            if dirname(path) != path:
                contents.insert(0, dirname(path))

            class Link(Label):
                def __init__(self, f_path, index_):
                    self.f_path = f_path

                    name = basename(f_path) if basename(f_path) else f_path

                    super().__init__(explorer, text=". . ." if f_path == dirname(path) else f"{"> " if isdir(f_path) 
                                     else ""}{name}", background=explorer.cget("background"), justify="left",
                                     foreground="#a0a0a0" if not can_open(f_path) else
                                     "#505050" if isdir(f_path) and f_path != dirname(path) else "#000000")
                    self.pack(anchor="w", padx=(10, 0))

                    if isdir(f_path):
                        self.bind("<Double-Button-1>", lambda _: try_open(f_path))
                        self.bind("<Button-1>", lambda _: try_preview(f_path) if selected != self.f_path else
                                  try_open(f_path))
                        self.bind("<Button-3>", lambda _: try_menu(f_path, self))

                    else:
                        self.bind("<Double-Button-1>", lambda _: try_open(f_path))
                        self.bind("<Button-1>", lambda _: try_preview(f_path) if selected != self.f_path else
                                  try_open(f_path))
                        self.bind("<Button-3>", lambda _: try_menu(f_path, self))
                        main.bind("<F2>", lambda event: try_menu(f_path, self, "rename") if
                                  main.winfo_containing(event.x_root, event.y_root) == self else None, add=index_ != 1)

                    for j in ["<Enter>", "<Leave>", "<Button-1>"]:
                        self.bind(j, lambda _: check_all_widgets(), add=True)

                    tooltip = [f"Name: {name}"]

                    if isdir(f_path):
                        tooltip.append("Size: N/A")

                    else:
                        tooltip.append(f"Size: {convert_size(stat(f_path).st_size)}")

                    tooltip.append("Double click to open")

                    ToolTip(self, "\n".join(tooltip), wraplength=350)

                def highlight_colour(self):
                    hovered_over = main.winfo_containing(*main.winfo_pointerxy()) == self
                    is_selected = selected == self.f_path
                    accessible = can_open(self.f_path)

                    colours = {
                        (True, False): "#c0c0c0",
                        (False, True): "#ffff00",
                        (True, True): "#cccc00",
                        (False, False): explorer.cget("background")
                    }

                    return colours[(is_selected, hovered_over)]

            for i in range(max(len(children), len(contents))):
                if len(children) > i:
                    children[i].destroy()

                if len(contents) > i:
                    if contents[i] == "|s":
                        Border(frame_kwargs={"master": explorer}).pack(fill="x", pady=5)

                    else:
                        Link(join(path, contents[i]), i)

            check_all_widgets()

            explorer.canvas.yview_moveto(0.0)

            display_path.set(path)
            user_settings["current_dir"] = path

        else:
            print(f"Opening {basename(path)}")

    try:
        open_path()
    except Exception as e:
        showerror(main.title(), f"{e}")


def try_preview(path):
    def preview_path():
        global selected

        selected = path

        children = preview.winfo_children()
        widgets = {
            Label(preview, text=f"{basename(path)}", font="TkDefaultFont 12", wraplength=preview.winfo_width()): {}
        }

        if isdir(path):
            pass

        else:
            file_type = Magic(mime=True).from_file(path)

            file_extension = basename(path).split(".")[-1]
            if file_extension == path:
                file_extension = "N/A"
            else:
                file_extension = f".{file_extension}"

            widgets |= {Label(preview, text=f"File type: {file_type}\nFile extension: {file_extension}"): {}}

            if file_extension in [".txt", ".md", ".py", ".json", ".bat"]:
                file_contents = open(path, "r", encoding="utf-8").read()

                char_limit = user_settings["char_limit"]

                if len(file_contents) > char_limit:
                    formatted_contents = file_contents[:char_limit] + "..."
                else:
                    formatted_contents = file_contents

                widgets |= {
                    Border({"master": preview}): dict(pady=10, fill="x"),
                    Label(preview, text=formatted_contents, wraplength=preview.winfo_width(), padx=5, justify="left",
                          background="#ffffff"): {}
                }

        for i in range(max(len(children), len(widgets))):
            if len(children) > i:
                children[i].destroy()

            if len(widgets) > i:
                list(widgets)[i].pack(**widgets[list(widgets)[i]])

        preview.canvas.yview_moveto(0.0)

    try:
        preview_path()
    except Exception as e:
        showerror(main.title(), f"{e}")


def convert_size(size_bytes):
    """
    Once again an exact copy of the code used in Seeker.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size_bytes, 1024)))
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def try_menu(path, link, command=None):
    def open_menu():
        menu = Toplevel()
        menu.geometry(f"+{main.winfo_pointerx()}+{main.winfo_pointery()}")
        menu.overrideredirect(True)
        menu.focus_force()
        menu.bind("<FocusOut>", lambda _: menu.destroy())
        menu.bind("<ButtonRelease-1>", lambda _: menu.destroy())

        def f_rename():
            new_name = StringVar(value=basename(path))
            entry = Entry(explorer, textvariable=new_name, background="#fafafa")
            entry.pack(after=link, anchor="w", padx=(10, 0))
            link.destroy()
            entry.focus_force()

            if "." in new_name.get():
                entry.icursor(new_name.get().rfind("."))
                entry.selection_to(new_name.get().rfind("."))
            else:
                entry.icursor(len(new_name.get()))
                entry.selection_to(len(new_name.get()))

            def do_rename():
                rename(path, join(dirname(path), new_name.get()))
                try_open()

            entry.bind("<Return>", lambda _: do_rename())
            main.bind("<Button-1>", lambda event: try_open() if event.widget != entry else None)
            entry.bind("<Escape>", lambda _: try_open())
            entry.bind("<F2>", lambda _: try_open())
            entry.bind("<Right>", lambda _: (entry.icursor(entry.index("insert") - 1), entry.unbind("<Right>"),
                                             entry.unbind("<Left>")))
            entry.bind("<Left>", lambda _: (entry.icursor(entry.index("insert") + 1), entry.unbind("<Right>"),
                                            entry.unbind("<Left>")))

        Button(menu, text="Rename", command=f_rename).pack(fill="x")

        Button(menu, text="Open in Default App", command=lambda: run(["start", "", path], shell=True)).pack(fill="x")

        if isdir(path):
            pass

        else:
            pass

        if command == "rename":
            f_rename()
            menu.destroy()

    try:
        open_menu()
    except Exception as e:
        showerror(main.title(), f"{e}")


def save():
    def save_serializer(obj):
        if isinstance(obj, StringVar):
            return obj.get()

        raise TypeError("Type not serializable")

    dump(user_settings, open(join(master_folder_path, "user_settings.json"), "w"), default=save_serializer)


def load():
    global user_settings

    def settings_parser(dct):
        for key, value in dct.items():
            if key in ["example"]:
                try:
                    dct[key] = StringVar(value=value)
                except (ValueError, TypeError):
                    pass

        return dct

    if (exists(join(master_folder_path, "user_settings.json")) and
            open(join(master_folder_path, "user_settings.json")).read()):
        user_settings |= load_json(open(join(master_folder_path, "user_settings.json")), object_hook=settings_parser)

    try_open(user_settings["current_dir"])


# noinspection PyUnresolvedReferences
def check_all_widgets():
    [w.configure(**{"background": w.highlight_colour()}) for w in explorer.winfo_children() if
     hasattr(w, "highlight_colour")]


def can_open(path):
    if isdir(path):
        try:
            listdir(path)
            return True
        except PermissionError:
            return False
    else:
        try:
            open(path)
            return True
        except (PermissionError, OSError):
            return False


#

custom_rows(0, 0, 1), custom_columns(1, 0, 1)

frame = QFrame(row=0, column=0, columnspan=x_fun.columns.get(), sticky="nsew")
frame.grid_propagate(False)

display_path = StringVar()

nav_bar = Entry(frame, justify="center", textvariable=display_path)
nav_bar.pack(side="left", fill="both", expand=True)

Button(frame, text="Go!", width=6, command=lambda: try_open(display_path.get())).pack(side="left", fill="y")
nav_bar.bind("<Return>", lambda *_: try_open(display_path.get()))

Border(row=1, column=0, columnspan=x_fun.columns.get(), sticky="ew")

explorer = ScrollingFrame(background="#ffffff", pady=5)
explorer.frame.grid(row=2, column=2, sticky="nsew")

Border(row=2, column=1, sticky="ns")

preview = ScrollingFrame(pady=5)
preview.frame.grid(row=2, column=0, sticky="nsew")

#

master_folder_path = join(expanduser("~"), "AppData", "Local", "Alia's App Suite", "explorer")
if not exists(master_folder_path):
    makedirs(master_folder_path, exist_ok=True)

user_settings = {"current_dir": "C:\\", "char_limit": 200}
selected = ""

load()

main.mainloop()
