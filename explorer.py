from tkinter import *
from os.path import isdir, basename, join, isfile, dirname, exists, expanduser
from os import listdir, stat, makedirs
from tkinter.messagebox import showerror
from math import floor, log
from magic import Magic
from json import dump, load as load_json

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


def try_open(path):
    def open_path():
        if isdir(path):
            display_path.set(path)
            user_settings["current_dir"] = path

            children = explorer.winfo_children()
            contents = [f for f in listdir(path) if isdir(join(path, f))] + ["|s"] + \
                       [f for f in listdir(path) if isfile(join(path, f))]

            if dirname(path) != path:
                contents.insert(0, dirname(path))

            class Link(Label):
                def __init__(self, f_path):
                    name = basename(f_path) if basename(f_path) else f_path

                    super().__init__(explorer, text=". . ." if f_path == dirname(path) else f"{"> " if isdir(f_path) 
                                     else ""}{name}", background=explorer.cget("background"), justify="left",
                                     foreground="#505050" if isdir(f_path) and f_path != dirname(path) else "#000000")
                    self.pack(anchor="w", padx=(10, 0))
                    self.bind("<Enter>", lambda _: self.configure(background="#ffff00"))
                    self.bind("<Leave>", lambda _: self.configure(background=explorer.cget("background")))

                    if isdir(f_path):
                        self.bind("<Double-Button-1>", lambda _: try_open(f_path))
                        self.bind("<Button-1>", lambda _: try_preview(f_path))
                        self.bind("<Button-3>", lambda _: try_menu(f_path))

                    else:
                        self.bind("<Double-Button-1>", lambda _: try_open(f_path))
                        self.bind("<Button-1>", lambda _: try_preview(f_path))
                        self.bind("<Button-3>", lambda _: try_menu(f_path))

                    tooltip = [f"Name: {name}"]

                    if isdir(f_path):
                        tooltip.append("Size: N/A")

                    else:
                        tooltip.append(f"Size: {convert_size(stat(f_path).st_size)}")

                    tooltip.append("Double click to open")

                    ToolTip(self, "\n".join(tooltip), wraplength=350)

            for i in range(max(len(children), len(contents))):
                if len(children) > i:
                    children[i].destroy()

                if len(contents) > i:
                    if contents[i] == "|s":
                        Border(frame_kwargs={"master": explorer}).pack(fill="x", pady=5)

                    else:
                        Link(join(path, contents[i]))

            explorer.canvas.yview_moveto(0.0)

        else:
            print(f"Opening {basename(path)}")

    try:
        open_path()
    except Exception as e:
        showerror(main.title(), f"{e}")


def try_preview(path):
    def preview_path():
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
                char_limit = 250
                if len(file_contents) <= char_limit:
                    formatted_contents = file_contents[:char_limit] + "..." if len(file_contents) > char_limit else ""
                else:
                    formatted_contents = file_contents

                widgets |= {
                    Border({"master": preview}): {"pady": 10, "fill": "x"},
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


def try_menu(path):
    def open_menu():
        menu = Toplevel()
        menu.geometry(f"+{main.winfo_pointerx()}+{main.winfo_pointery()}")
        menu.overrideredirect(True)
        menu.focus_force()
        menu.bind("<FocusOut>", lambda _: menu.destroy())

        if isdir(path):
            pass

        else:
            pass

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

    if exists(join(master_folder_path, "user_settings.json")):
        user_settings |= load_json(open(join(master_folder_path, "user_settings.json")), object_hook=settings_parser)

    try_open(user_settings["current_dir"])


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

user_settings = {"current_dir": "C:\\"}

load()

main.mainloop()
