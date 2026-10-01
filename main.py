# VVU-DeskShell — учебная мини-оболочка (лабораторная работа №4)
# Авторская реализация на tkinter: отличается от стороннего примера
# по названию, структуре классов, журналу и набору тем оформления.

import json
import hashlib
import math
import random
import secrets
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, messagebox, ttk

APP_TITLE = "VVU-DeskShell"
APP_VERSION = "1.0"
LOG_FILENAME = "desk_shell.log"
ICONS_DIRNAME = "icons"
WALLPAPERS_DIRNAME = "wallpapers"
WALLPAPER_NONE_LABEL = "— только цвет (без фото) —"

# Ключи ресурсов иконок → переименованные PNG (формат как в исходном примере)
ICON_ASSETS = {
    "vychislitel": "vvu_vychislitel.png",
    "fayly": "vvu_fayly.png",
    "zadachi": "vvu_zadachi.png",
    "parametry": "vvu_parametry.png",
    "zhurnal": "vvu_zhurnal.png",
    "menu": "vvu_menu.png",
}

THEME_OPTIONS = {
    "olive": {
        "root": "#dfe7d6",
        "panel": "#c7d9b7",
        "main": "#eef4e8",
        "taskbar": "#253528",
        "taskbar_button": "#4f6f57",
        "taskbar_active": "#739072",
        "start": "#3f7d58",
        "start_active": "#356a4b",
        "chip": "#dbead2",
        "text": "#17313a",
        "muted": "#66785f",
        "selection": "#dbead2",
        "selection_border": "#8caf74",
    },
    "sand": {
        "root": "#efe6da",
        "panel": "#dcc9b6",
        "main": "#fbf4ec",
        "taskbar": "#4a3526",
        "taskbar_button": "#7a573f",
        "taskbar_active": "#a87957",
        "start": "#9a6b45",
        "start_active": "#825737",
        "chip": "#efe1cf",
        "text": "#2d241c",
        "muted": "#7a6a5f",
        "selection": "#f1dcc2",
        "selection_border": "#c69a6b",
    },
    "sky": {
        "root": "#dbe9f4",
        "panel": "#bfd7ea",
        "main": "#edf6fb",
        "taskbar": "#172554",
        "taskbar_button": "#3d5a80",
        "taskbar_active": "#5f86bd",
        "start": "#2563eb",
        "start_active": "#1d4ed8",
        "chip": "#dbeafe",
        "text": "#1d3557",
        "muted": "#67809f",
        "selection": "#dbeafe",
        "selection_border": "#93c5fd",
    },
    "slate": {
        "root": "#e2e8f0",
        "panel": "#cbd5e1",
        "main": "#f1f5f9",
        "taskbar": "#1e293b",
        "taskbar_button": "#475569",
        "taskbar_active": "#64748b",
        "start": "#0f766e",
        "start_active": "#0d9488",
        "chip": "#e2e8f0",
        "text": "#0f172a",
        "muted": "#64748b",
        "selection": "#ccfbf1",
        "selection_border": "#5eead4",
    },
}

BACKGROUND_OPTIONS = {
    "white": {"label": "Белый", "surface": "#ffffff", "log": "#f8fafc", "text": "#1e293b"},
    "blue": {"label": "Голубой", "surface": "#bfdbfe", "log": "#eff6ff", "text": "#1e3a5f"},
    "green": {"label": "Зелёный", "surface": "#bbf7d0", "log": "#f0fdf4", "text": "#14532d"},
    "purple": {"label": "Фиолетовый", "surface": "#e9d5ff", "log": "#faf5ff", "text": "#581c87"},
    "gray": {"label": "Серый", "surface": "#e2e8f0", "log": "#f1f5f9", "text": "#334155"},
    "beige": {"label": "Бежевый", "surface": "#fde68a", "log": "#fffbeb", "text": "#78350f"},
}


def list_wallpaper_files(wallpapers_dir: Path) -> list[str]:
    if not wallpapers_dir.exists():
        wallpapers_dir.mkdir(parents=True, exist_ok=True)
    names: list[str] = []
    for pattern in ("*.png", "*.PNG", "*.jpg", "*.JPEG", "*.jpeg", "*.gif", "*.GIF"):
        names.extend(item.name for item in wallpapers_dir.glob(pattern))
    return sorted(set(names))

THEME_LABELS = {
    "olive": "Зелёная классика",
    "sand": "Тёплый песок",
    "sky": "Голубая волна",
    "slate": "Графитовая",
}

PROCESS_LAUNCH_OPTIONS = [
    "Калькулятор",
    "Файловый менеджер",
    "Параметры",
    "Фоновая служба",
]


class SuspendableWindowMixin:
    """Общая логика приостановки окна приложения (блокировка виджетов, без grab_set)."""

    _suspended: bool

    def freeze(self) -> None:
        if getattr(self, "_suspended", False):
            return
        self._suspended = True
        self._disable_widgets(self.window)
        current_title = self.window.title()
        if not current_title.startswith("[ПРИОСТАНОВЛЕНО] "):
            self.window.title(f"[ПРИОСТАНОВЛЕНО] {current_title}")
        try:
            self.window.attributes("-alpha", 0.7)
        except tk.TclError:
            pass

    def unfreeze(self) -> None:
        if not getattr(self, "_suspended", False):
            return
        self._suspended = False
        self._enable_widgets(self.window)
        title = self.window.title().replace("[ПРИОСТАНОВЛЕНО] ", "")
        self.window.title(title)
        try:
            self.window.attributes("-alpha", 1.0)
        except tk.TclError:
            pass

    def _disable_widgets(self, widget) -> None:
        try:
            if isinstance(
                widget,
                (
                    tk.Button,
                    tk.Entry,
                    tk.Text,
                    ttk.Combobox,
                    tk.Checkbutton,
                    tk.Radiobutton,
                    tk.Spinbox,
                    tk.Listbox,
                    ttk.Treeview,
                ),
            ):
                widget.configure(state="disabled")
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._disable_widgets(child)

    def _enable_widgets(self, widget) -> None:
        try:
            if isinstance(
                widget,
                (
                    tk.Button,
                    tk.Entry,
                    tk.Text,
                    ttk.Combobox,
                    tk.Checkbutton,
                    tk.Radiobutton,
                    tk.Spinbox,
                    tk.Listbox,
                    ttk.Treeview,
                ),
            ):
                widget.configure(state="normal")
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._enable_widgets(child)


@dataclass
class TaskEntry:
    pid: int
    name: str
    status: str
    cpu: int
    category: str
    window_id: str | None = None


class TaskNode:
    def __init__(self, record: TaskEntry) -> None:
        self.record = record
        self.prev: TaskNode | None = None
        self.next: TaskNode | None = None


class TaskChain:
    def __init__(self) -> None:
        self.head: TaskNode | None = None
        self.tail: TaskNode | None = None
        self._index: dict[int, TaskNode] = {}

    def append(self, record: TaskEntry) -> None:
        node = TaskNode(record)
        if self.tail is None:
            self.head = node
            self.tail = node
        else:
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        self._index[record.pid] = node

    def remove(self, pid: int) -> TaskEntry | None:
        node = self._index.pop(pid, None)
        if node is None:
            return None

        if node.prev is None:
            self.head = node.next
        else:
            node.prev.next = node.next

        if node.next is None:
            self.tail = node.prev
        else:
            node.next.prev = node.prev

        node.prev = None
        node.next = None
        return node.record

    def get(self, pid: int) -> TaskEntry | None:
        node = self._index.get(pid)
        return None if node is None else node.record

    def values(self) -> list[TaskEntry]:
        current = self.head
        records: list[TaskEntry] = []
        while current is not None:
            records.append(current.record)
            current = current.next
        return records

    def __contains__(self, pid: int) -> bool:
        return pid in self._index


class VirtualItem:
    def __init__(
        self,
        name: str,
        item_type: str,
        content: str = "",
        linked_path: Path | None = None,
        locked: bool = False,
    ) -> None:
        self.name = name
        self.item_type = item_type
        self.content = content
        self.linked_path = linked_path
        self.locked = locked
        self.children: list[VirtualItem] = []

    @property
    def is_dir(self) -> bool:
        return self.item_type == "dir"


class VirtualFileSystem:
    def __init__(self, log_file_path: Path) -> None:
        self.root = VirtualItem("root", "dir")
        self.log_file_path = log_file_path
        self._seed()

    def _seed(self) -> None:
        system = VirtualItem("System", "dir")
        apps = VirtualItem("Apps", "dir")
        docs = VirtualItem("Documents", "dir")
        trash = VirtualItem("Trash", "dir")

        apps.children.extend(
            [
                VirtualItem("calculator.app", "file", locked=True),
                VirtualItem("explorer.app", "file", locked=True),
                VirtualItem("settings.app", "file", locked=True),
                VirtualItem("taskmgr.app", "file", locked=True),
            ]
        )
        docs.children.extend(
            [
                VirtualItem("notes.txt", "file", content="VVU-DeskShell: виртуальная ФС для лабораторной работы №4."),
                VirtualItem("report.txt", "file", content="Каталог Documents — черновики отчёта и заметок по курсу БОС."),
                VirtualItem("desk_shell.log", "file", linked_path=self.log_file_path, locked=True),
            ]
        )
        system.children.extend([VirtualItem("kernel.sys", "file", locked=True), VirtualItem("drivers", "dir", locked=True)])
        self.root.children.extend([system, apps, docs, trash])

    def resolve(self, path_parts: list[str]) -> VirtualItem | None:
        current = self.root
        for part in path_parts:
            match = next((child for child in current.children if child.name == part and child.is_dir), None)
            if match is None:
                return None
            current = match
        return current

    def list_dir(self, path_parts: list[str]) -> list[VirtualItem]:
        directory = self.resolve(path_parts)
        if directory is None:
            raise ValueError("Каталог не найден")
        return sorted(directory.children, key=lambda item: (item.item_type != "dir", item.name.lower()))

    def find_item(self, path_parts: list[str], name: str) -> VirtualItem | None:
        directory = self.resolve(path_parts)
        if directory is None:
            return None
        return next((child for child in directory.children if child.name == name), None)

    def create_item(self, path_parts: list[str], name: str, item_type: str) -> VirtualItem:
        directory = self.resolve(path_parts)
        if directory is None:
            raise ValueError("Каталог не найден")
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Имя элемента не может быть пустым")
        if any(char in clean_name for char in "\\/"):
            raise ValueError("В имени запрещены символы / и \\")
        if any(child.name.lower() == clean_name.lower() for child in directory.children):
            raise ValueError("Объект с таким именем уже есть в каталоге")
        item = VirtualItem(clean_name, item_type)
        directory.children.append(item)
        return item

    def delete_item(self, path_parts: list[str], name: str) -> VirtualItem:
        directory = self.resolve(path_parts)
        if directory is None:
            raise ValueError("Каталог не найден")
        for index, child in enumerate(directory.children):
            if child.name == name:
                if child.locked:
                    raise ValueError("Системный объект защищён от удаления")
                return directory.children.pop(index)
        raise ValueError("Объект не найден")

    def read_file(self, item: VirtualItem) -> str:
        if item.linked_path is not None:
            if not item.linked_path.exists():
                return ""
            return item.linked_path.read_text(encoding="utf-8")
        return item.content


class CalculatorWindow(SuspendableWindowMixin):
    def __init__(self, app: "DeskShellApp", pid: int, title: str) -> None:
        self.app = app
        self.pid = pid
        self.window = tk.Toplevel(app.root)
        self.window.title(title)
        self.window.geometry("320x430")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self._suspended = False

        self.display_var = tk.StringVar(value="0")
        self.expression = ""

        container = app.create_app_shell(self.window, title, can_maximize=False, accent="#2f6b59", close_command=self.close)

        display = tk.Entry(
            container,
            textvariable=self.display_var,
            font=("Consolas", 24),
            justify="right",
            bd=0,
            relief="flat",
            bg="#f8fafc",
            fg="#0f172a",
        )
        display.pack(fill="x", pady=(0, 12), ipady=10)

        buttons = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "-"],
            ["C", "0", "=", "+"],
        ]

        for row in buttons:
            row_frame = tk.Frame(container, bg=container.cget("bg"))
            row_frame.pack(fill="x", expand=True, pady=4)
            for symbol in row:
                button = tk.Button(
                    row_frame,
                    text=symbol,
                    font=("Segoe UI", 14, "bold"),
                    bd=0,
                    relief="flat",
                    bg="#bde0d3" if symbol in {"=", "C"} else "#e2e8f0",
                    fg="#17313a",
                    activebackground="#a9d0c1" if symbol in {"=", "C"} else "#cbd5e1",
                    command=lambda value=symbol: self.handle_input(value),
                )
                button.pack(side="left", expand=True, fill="both", padx=4, ipady=14)

    def handle_input(self, value: str) -> None:
        if self._suspended:
            return
        if value == "C":
            self.expression = ""
            self.display_var.set("0")
            return
        if value == "=":
            try:
                result = str(eval(self.expression or "0", {}, {}))
                self.display_var.set(result)
                self.expression = result
            except Exception:
                self.display_var.set("Недопустимо")
                self.expression = ""
            return

        self.expression += value
        self.display_var.set(self.expression)

    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()
        self.app.terminate_process(self.pid, from_window=True)


class TextViewerWindow(SuspendableWindowMixin):
    def __init__(self, app: "DeskShellApp", pid: int, title: str, content: str) -> None:
        self.app = app
        self.pid = pid
        self.window = tk.Toplevel(app.root)
        self.window.title(title)
        self.window.geometry("640x440")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self._suspended = False

        container = app.create_app_shell(self.window, title, can_maximize=True, accent="#5661d8", close_command=self.close)

        viewer = tk.Text(container, font=("Consolas", 10), bg="#fbfdff", fg="#223244", relief="flat", bd=0, wrap="word")
        viewer.pack(fill="both", expand=True)
        viewer.insert("1.0", content)
        viewer.configure(state="disabled")

    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()
        self.app.terminate_process(self.pid, from_window=True)


class LoginWindow:
    def __init__(self, app: "DeskShellApp") -> None:
        self.app = app
        self.window = app.root
        self.window.title(f"{APP_TITLE} {APP_VERSION} | Вход")
        self.window.geometry("440x380")
        self.window.configure(bg="#e8eef5")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.app.shutdown)

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.info_var = tk.StringVar(value="Введите учётные данные или зарегистрируйте новый аккаунт.")

        self.frame = tk.Frame(self.window, bg="#e8eef5", padx=24, pady=24)
        self.frame.pack(fill="both", expand=True)

        tk.Label(self.frame, text=APP_TITLE, font=("Segoe UI", 22, "bold"), bg="#e8eef5", fg="#2c4a6e").pack(anchor="w")
        tk.Label(self.frame, text=f"Версия {APP_VERSION} · лабораторная БОС", font=("Segoe UI", 10), bg="#e8eef5", fg="#5a6f8a").pack(anchor="w", pady=(2, 8))
        tk.Label(
            self.frame,
            text="Авторизация · пароль хранится как хеш PBKDF2-SHA256 (не в открытом виде)",
            font=("Segoe UI", 9),
            bg="#e8eef5",
            fg="#5a6f8a",
            wraplength=380,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))
        tk.Label(self.frame, text="Вход в оболочку", font=("Segoe UI", 11), bg="#e8eef5", fg="#4a5f7a").pack(anchor="w", pady=(0, 12))

        tk.Label(self.frame, text="Имя пользователя", bg="#e8eef5").pack(anchor="w")
        username_entry = tk.Entry(self.frame, textvariable=self.username_var, font=("Segoe UI", 11))
        username_entry.pack(fill="x", pady=(6, 14))

        tk.Label(self.frame, text="Пароль", bg="#e8eef5").pack(anchor="w")
        password_entry = tk.Entry(self.frame, textvariable=self.password_var, font=("Segoe UI", 11), show="*")
        password_entry.pack(fill="x", pady=(6, 16))

        button_row = tk.Frame(self.frame, bg="#e8eef5")
        button_row.pack(fill="x")

        tk.Button(button_row, text="Вход в систему", command=self.login, bg="#c5d9f0", relief="flat", padx=18).pack(side="left")
        tk.Button(button_row, text="Создать аккаунт", command=self.register, bg="#d4e4f7", relief="flat", padx=18).pack(side="left", padx=8)

        tk.Label(self.frame, textvariable=self.info_var, wraplength=360, justify="left", bg="#e8eef5", fg="#5a6472").pack(anchor="w", pady=(18, 0))

        username_entry.focus_set()
        self.window.bind("<Return>", lambda _event: self.login())

    def login(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()
        if not self.app.user_store.authenticate(username, password):
            self.info_var.set("Неправильное имя пользователя или пароль.")
            return
        self.destroy()
        self.app.complete_login(username)

    def register(self) -> None:
        username = self.username_var.get().strip()
        password = self.password_var.get()
        try:
            self.app.user_store.create_user(username, password)
        except ValueError as error:
            self.info_var.set(str(error))
            return
        self.info_var.set("Аккаунт создан. Пароль записан в users.json как хеш. Выполните вход.")
        self.app.log("Зарегистрирован новый пользователь (пароль сохранён в виде хеша).")

    def destroy(self) -> None:
        self.window.unbind("<Return>")
        if self.frame.winfo_exists():
            self.frame.destroy()


class SettingsWindow(SuspendableWindowMixin):
    def __init__(self, app: "DeskShellApp", pid: int, title: str) -> None:
        self.app = app
        self.pid = pid
        self.window = tk.Toplevel(app.root)
        self.window.title(title)
        self.window.geometry("500x580")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self._suspended = False

        self.theme_label_to_key = {label: key for key, label in THEME_LABELS.items()}
        self.wallpaper_choices = app.wallpaper_choice_labels()
        current_theme = app.user_settings.get("theme", "olive")
        current_background = app.user_settings.get("background", "purple")
        current_wallpaper = app.user_settings.get("wallpaper", "")
        self.theme_var = tk.StringVar(value=THEME_LABELS.get(current_theme, THEME_LABELS["olive"]))
        self.background_key_var = tk.StringVar(value=current_background if current_background in BACKGROUND_OPTIONS else "purple")
        self.wallpaper_var = tk.StringVar(value=app.wallpaper_label_for_file(current_wallpaper))
        self.show_seconds_var = tk.BooleanVar(value=app.user_settings.get("show_seconds", True))

        frame = app.create_app_shell(self.window, title, can_maximize=True, accent="#6f5bd3", close_command=self.close)

        tk.Label(frame, text="Параметры оболочки", font=("Segoe UI", 18, "bold"), bg=frame.cget("bg"), fg="#1f2744").pack(anchor="w")
        tk.Label(frame, text=f"Аккаунт: {app.current_user}", bg=frame.cget("bg"), fg="#67738a").pack(anchor="w", pady=(4, 16))

        tk.Label(frame, text="Цветовая схема", bg=frame.cget("bg"), fg="#23324d").pack(anchor="w")
        ttk.Combobox(
            frame,
            textvariable=self.theme_var,
            values=list(self.theme_label_to_key),
            state="readonly",
        ).pack(fill="x", pady=(6, 14))

        tk.Label(frame, text="Цвет рабочего стола (без фото)", bg=frame.cget("bg"), fg="#23324d").pack(anchor="w", pady=(4, 6))
        colors_row = tk.Frame(frame, bg=frame.cget("bg"))
        colors_row.pack(fill="x")
        for key, option in BACKGROUND_OPTIONS.items():
            btn = tk.Button(
                colors_row,
                text=option["label"],
                width=10,
                bg=option["surface"],
                fg=option["text"],
                activebackground=option["surface"],
                relief="flat",
                command=lambda bg_key=key: self._pick_preset_color(bg_key),
            )
            btn.pack(side="left", padx=3, pady=3)
        tk.Button(
            frame,
            text="Свой цвет…",
            command=self._pick_custom_color,
            bg="#e2e8f0",
            relief="flat",
        ).pack(anchor="w", pady=(4, 10))

        tk.Label(frame, text="Фото-обои (PNG/JPG в папке wallpapers)", bg=frame.cget("bg"), fg="#23324d").pack(anchor="w")
        wp_row = tk.Frame(frame, bg=frame.cget("bg"))
        wp_row.pack(fill="x", pady=(6, 4))
        self.wallpaper_combo = ttk.Combobox(
            wp_row,
            textvariable=self.wallpaper_var,
            values=self.wallpaper_choices,
            state="readonly",
        )
        self.wallpaper_combo.pack(side="left", fill="x", expand=True)
        tk.Button(wp_row, text="↻", command=self._refresh_wallpaper_list, bg="#e2e8f0", relief="flat", width=3).pack(side="left", padx=4)
        self.wallpaper_combo.bind("<<ComboboxSelected>>", self._preview_wallpaper)
        tk.Label(
            frame,
            text="Положите свои .png в папку «wallpapers» рядом с main.py",
            bg=frame.cget("bg"),
            fg="#67738a",
            wraplength=380,
            justify="left",
        ).pack(anchor="w")

        tk.Checkbutton(
            frame,
            text="Отображать секунды в часах",
            variable=self.show_seconds_var,
            bg=frame.cget("bg"),
            activebackground=frame.cget("bg"),
        ).pack(anchor="w")

        features = tk.LabelFrame(frame, text="Функции проекта", bg=frame.cget("bg"), fg="#23324d", padx=10, pady=8)
        features.pack(fill="x", pady=(14, 0))
        for line in (
            "• Авторизация и регистрация пользователей",
            "• Хеширование паролей (PBKDF2 + соль)",
            "• Смена фона: цвет или PNG-фото из wallpapers/",
            "• Значки на рабочей области (ярлыки приложений)",
        ):
            tk.Label(features, text=line, anchor="w", bg=frame.cget("bg"), fg="#67738a").pack(fill="x")

        description = "Цвет — заливка без картинки. PNG — фото на всю рабочую область (значки поверх)."
        tk.Label(frame, text=description, wraplength=380, justify="left", bg=frame.cget("bg"), fg="#67738a").pack(anchor="w", pady=(12, 0))

        button_row = tk.Frame(frame, bg=frame.cget("bg"))
        button_row.pack(fill="x", side="bottom", pady=(24, 0))

        tk.Button(button_row, text="Применить", command=self.save, bg="#cfe1ff", fg="#17325f", relief="flat", padx=18).pack(side="left")
        tk.Button(button_row, text="Закрыть без сохранения", command=self.close, bg="#e8edf4", fg="#33425c", relief="flat", padx=18).pack(side="left", padx=8)

    def _pick_preset_color(self, bg_key: str) -> None:
        self.background_key_var.set(bg_key)
        self.app.user_settings.pop("custom_surface", None)
        self.app.user_settings["background"] = bg_key
        self.app.user_settings["wallpaper"] = ""
        self.wallpaper_var.set(WALLPAPER_NONE_LABEL)
        self.app.apply_user_settings()
        self.app._rebuild_desktop_icons()

    def _pick_custom_color(self) -> None:
        initial = self.app.current_background()["surface"]
        result = colorchooser.askcolor(color=initial, title="Цвет рабочего стола")
        if result[1] is None:
            return
        hex_color = result[1]
        self.app.user_settings["background"] = "custom"
        self.app.user_settings["custom_surface"] = hex_color
        self.app.user_settings["wallpaper"] = ""
        self.wallpaper_var.set(WALLPAPER_NONE_LABEL)
        self.background_key_var.set("custom")
        self.app.apply_user_settings()
        self.app._rebuild_desktop_icons()

    def _refresh_wallpaper_list(self) -> None:
        self.wallpaper_choices = self.app.wallpaper_choice_labels()
        self.wallpaper_combo.configure(values=self.wallpaper_choices)

    def _preview_wallpaper(self, _event=None) -> None:
        filename = self.app.wallpaper_file_for_label(self.wallpaper_var.get())
        self.app.user_settings["wallpaper"] = filename
        if filename:
            self.app.user_settings["background"] = self.background_key_var.get()
        self.app.apply_user_settings()
        self.app._rebuild_desktop_icons()

    def save(self) -> None:
        self.app.user_settings["theme"] = self.theme_label_to_key.get(self.theme_var.get(), "olive")
        bg_key = self.background_key_var.get()
        if bg_key in BACKGROUND_OPTIONS:
            self.app.user_settings["background"] = bg_key
        self.app.user_settings["wallpaper"] = self.app.wallpaper_file_for_label(self.wallpaper_var.get())
        self.app.user_settings["show_seconds"] = self.show_seconds_var.get()
        self.app.save_user_settings()
        self.app.apply_user_settings()
        self.app._rebuild_desktop_icons()
        bg_label = self.app.current_background()["label"]
        wp = self.app.user_settings.get("wallpaper", "")
        if wp:
            self.app.log(f"Обои рабочего стола: фото «{wp}» (цвет подложки: {bg_label}).")
        else:
            self.app.log(f"Фон рабочего стола: только цвет «{bg_label}».")
        self.app.log("Параметры аккаунта сохранены.")
        self.close()

    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()
        self.app.terminate_process(self.pid, from_window=True)


class DesktopIcon:
    def __init__(self, app: "DeskShellApp", canvas: tk.Canvas, label: str, command, x: int, y: int, asset_id: str) -> None:
        self.app = app
        self.canvas = canvas
        self.label = label
        self.command = command
        self.asset_id = asset_id
        self.x = x
        self.y = y
        self.last_root_x = 0
        self.last_root_y = 0
        self.overlay_mode = bool(app.user_settings.get("wallpaper"))
        self.frame: tk.Frame | None = None
        self.window_id: int | None = None
        self.text_id: int | None = None
        self.text_shadow_id: int | None = None
        self.icon_box: tk.Label | None = None
        self.text_label: tk.Label | None = None
        self.icon_image = app.load_icon_image(asset_id)

        if self.overlay_mode:
            self._build_overlay_icon()
        else:
            self._build_chip_icon()

    def _build_overlay_icon(self) -> None:
        """Отрисовка иконки в режиме обоев (без подложки)"""
        # 1. Защищаем картинку от Garbage Collector'а
        self.image_ref = self.app.load_icon_image(self.asset_id)

        # 2. Рисуем картинку как ЧИСТЫЙ элемент Canvas (а не tk.Label)
        # Центрируем картинку: x + 26 (половина от ширины 52)
        self.image_id = self.canvas.create_image(
            self.x + 26, self.y + 26,
            image=self.image_ref,
            tags=f"icon_{id(self)}"
        )

        # 3. Рисуем тень текста для читаемости на любых обоях
        self.text_shadow_id = self.canvas.create_text(
            self.x + 27, self.y + 63,
            text=self.label,
            font=("Segoe UI", 10),
            fill="#000000",
            width=100,
            justify="center",
            tags=f"icon_{id(self)}"
        )

        # 4. Рисуем сам текст
        self.text_id = self.canvas.create_text(
            self.x + 26, self.y + 62,
            text=self.label,
            font=("Segoe UI", 10, "bold"),
            fill="#ffffff",
            width=100,
            justify="center",
            tags=f"icon_{id(self)}"
        )

        # 5. Вешаем бинды хитбокса НА ВСЕ элементы иконки
        self._bind_events()

    def _build_chip_icon(self) -> None:
        """Отрисовка иконки в обычном режиме (однотонный фон)"""
        self.image_ref = self.app.load_icon_image(self.asset_id)

        # Точно так же уходим от виджетов и рисуем на холсте
        self.image_id = self.canvas.create_image(
            self.x + 26, self.y + 26,
            image=self.image_ref,
            tags=f"icon_{id(self)}"
        )

        self.text_id = self.canvas.create_text(
            self.x + 26, self.y + 62,
            text=self.label,
            font=("Segoe UI", 10),
            fill="#1d3557",
            width=100,
            justify="center",
            tags=f"icon_{id(self)}"
        )

        self._bind_events()

    def _bind_events(self) -> None:
        """Привязка событий клика и перетаскивания ко всем частям иконки"""
        # Собираем все ID элементов этой иконки, у которых должен быть хитбокс
        items = []
        if hasattr(self, "image_id") and self.image_id: items.append(self.image_id)
        if getattr(self, "text_id", None): items.append(self.text_id)
        if getattr(self, "text_shadow_id", None): items.append(self.text_shadow_id)

        # Обертка для обработчиков, чтобы они понимали, какая именно иконка вызвана
        def make_handler(original_method):
            return lambda event: original_method(event) if hasattr(self, original_method.__name__) else None

        for item in items:
            # Названия методов (on_click, on_drag) проверь в своем классе DesktopIcon и замени если надо
            self.canvas.tag_bind(item, "<Button-1>", lambda e: self.app.select_desktop_icon(self))
            self.canvas.tag_bind(item, "<Double-Button-1>", lambda e: self.command())

            # Если в классе реализовано перетаскивание, привяжи его сюда:
            if hasattr(self, "start_drag"):
                self.canvas.tag_bind(item, "<ButtonPress-1>", self.start_drag)
            if hasattr(self, "do_drag"):
                self.canvas.tag_bind(item, "<B1-Motion>", self.do_drag)

    def set_selected(self, is_selected: bool) -> None:
        """Визуальное выделение иконки при клике"""
        if not hasattr(self, "text_id") or not self.text_id:
            return
        if is_selected:
            self.canvas.itemconfig(self.text_id, fill="#2563eb")  # Подсвечиваем синим при выборе
        else:
            self.canvas.itemconfig(self.text_id, fill="#ffffff" if self.overlay_mode else "#1d3557")

    def destroy(self) -> None:
        """Полное удаление элементов иконки с холста"""
        for attr in ("image_id", "text_id", "text_shadow_id"):
            val = getattr(self, attr, None)
            if val is not None:
                self.canvas.delete(val)
                setattr(self, attr, None)

    def _bind_canvas_items(self) -> None:
        for item_id in (self.window_id, self.text_id, self.text_shadow_id):
            if item_id is None:
                continue
            self.canvas.tag_bind(item_id, "<Button-1>", self.start_drag, add="+")
            self.canvas.tag_bind(item_id, "<B1-Motion>", self.on_drag, add="+")
            self.canvas.tag_bind(item_id, "<Double-Button-1>", self.activate, add="+")

    def _overlay_anchor(self) -> tuple[int, int]:
        if self.window_id is not None:
            x, y = self.canvas.coords(self.window_id)
            return int(x), int(y)
        if self.text_id is not None:
            x, y = self.canvas.coords(self.text_id)
            return int(x) - 34, int(y) - 74
        return self.x, self.y

    def _move_overlay_parts(self, icon_x: int, icon_y: int) -> None:
        if self.window_id is not None:
            self.canvas.coords(self.window_id, icon_x, icon_y)
        if self.text_shadow_id is not None:
            self.canvas.coords(self.text_shadow_id, icon_x + 35, icon_y + 75)
        if self.text_id is not None:
            self.canvas.coords(self.text_id, icon_x + 34, icon_y + 74)

    def start_drag(self, event) -> None:
        self.app.select_desktop_icon(self)
        self.last_root_x = event.x_root
        self.last_root_y = event.y_root

    def on_drag(self, event) -> None:
        delta_x = event.x_root - self.last_root_x
        delta_y = event.y_root - self.last_root_y
        max_x = max(0, self.canvas.winfo_width() - 96)
        max_y = max(0, self.canvas.winfo_height() - 100)

        if self.overlay_mode:
            icon_x, icon_y = self._overlay_anchor()
            new_x = max(0, min(max_x, icon_x + delta_x))
            new_y = max(0, min(max_y, icon_y + delta_y))
            self._move_overlay_parts(new_x, new_y)
        else:
            current_x, current_y = self.canvas.coords(self.window_id)
            new_x = max(0, min(max_x, int(current_x) + delta_x))
            new_y = max(0, min(max_y, int(current_y) + delta_y))
            self.canvas.coords(self.window_id, new_x, new_y)

        self.last_root_x = event.x_root
        self.last_root_y = event.y_root

    def activate(self, _event=None) -> None:
        self.app.select_desktop_icon(self)
        self.command()

    def set_selected(self, selected: bool) -> None:
        if self.overlay_mode:
            if self.text_id is None:
                return
            fill = "#93c5fd" if selected else "#ffffff"
            font = ("Segoe UI", 9, "bold") if selected else ("Segoe UI", 9)
            self.canvas.itemconfigure(self.text_id, fill=fill, font=font)
            return

        if self.frame is None or self.icon_box is None or self.text_label is None:
            return
        bg = self.app.icon_chip_color()
        text_color = "#2563eb" if selected else self.app.current_background()["text"]
        font_style = ("Segoe UI", 9, "bold") if selected else ("Segoe UI", 9)
        self.frame.configure(bg=bg, highlightthickness=0, bd=0)
        self.icon_box.configure(bg=bg)
        self.text_label.configure(bg=bg, fg=text_color, font=font_style)

    def refresh_theme(self) -> None:
        self.set_selected(self.app.selected_desktop_icon is self)

    def destroy(self) -> None:
        for item_id in (self.window_id, self.text_id, self.text_shadow_id):
            if item_id is not None:
                try:
                    self.canvas.delete(item_id)
                except tk.TclError:
                    pass


class UserStore:
    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.users = self._load()

    def _load(self) -> dict[str, dict]:
        if not self.file_path.exists():
            return {}
        try:
            return json.loads(self.file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self) -> None:
        self.file_path.write_text(json.dumps(self.users, ensure_ascii=False, indent=2), encoding="utf-8")

    def _hash_password(self, password: str, salt_hex: str | None = None) -> tuple[str, str]:
        salt = bytes.fromhex(salt_hex) if salt_hex is not None else secrets.token_bytes(16)
        derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
        return salt.hex(), derived_key.hex()

    def authenticate(self, username: str, password: str) -> bool:
        user = self.users.get(username)
        if user is None:
            return False
        password_hash = user.get("password_hash")
        password_salt = user.get("password_salt")
        if password_hash and password_salt:
            _, derived_key_hex = self._hash_password(password, password_salt)
            return derived_key_hex == password_hash

        legacy_password = user.get("password")
        if legacy_password != password:
            return False

        salt_hex, derived_key_hex = self._hash_password(password)
        user.pop("password", None)
        user["password_salt"] = salt_hex
        user["password_hash"] = derived_key_hex
        self.save()
        return True

    def create_user(self, username: str, password: str) -> None:
        clean_username = username.strip()
        if not clean_username:
            raise ValueError("Имя пользователя не может быть пустым.")
        if len(password) < 3:
            raise ValueError("Пароль должен быть не короче 3 символов.")
        if clean_username in self.users:
            raise ValueError("Такой аккаунт уже зарегистрирован.")
        salt_hex, derived_key_hex = self._hash_password(password)
        self.users[clean_username] = {
            "password_salt": salt_hex,
            "password_hash": derived_key_hex,
            "settings": {"theme": "olive", "background": "white", "wallpaper": "", "show_seconds": True},
        }
        self.save()

    def get_settings(self, username: str) -> dict:
        user = self.users.get(username, {})
        settings = user.get("settings", {})
        result = {
            "theme": settings.get("theme", "olive"),
            "background": settings.get("background", "white"),
            "wallpaper": settings.get("wallpaper", ""),
            "show_seconds": settings.get("show_seconds", True),
        }
        if settings.get("custom_surface"):
            result["custom_surface"] = settings["custom_surface"]
        return result

    def update_settings(self, username: str, settings: dict) -> None:
        if username not in self.users:
            return
        self.users[username]["settings"] = settings
        self.save()


class ExplorerWindow(SuspendableWindowMixin):
    def __init__(self, app: "DeskShellApp", pid: int, title: str) -> None:
        self.app = app
        self.pid = pid
        self.window = tk.Toplevel(app.root)
        self.window.title(title)
        self.window.geometry("620x430")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self._suspended = False

        wrapper = app.create_app_shell(self.window, title, can_maximize=True, accent="#0f8b8d", close_command=self.close)

        self.current_path: list[str] = []
        self.selected_name: str | None = None
        self.entry_targets: list[tuple[str, VirtualItem | str]] = []

        action_bar = tk.Frame(wrapper, bg=wrapper.cget("bg"))
        action_bar.pack(fill="x", pady=(0, 10))

        tk.Button(action_bar, text="+ Каталог", command=self.create_folder, bg="#cce7f0", fg="#17325f", relief="flat").pack(side="left")
        tk.Button(action_bar, text="+ Документ", command=self.create_file, bg="#dbe7ff", fg="#17325f", relief="flat").pack(side="left", padx=6)
        tk.Button(action_bar, text="Убрать", command=self.delete_selected, bg="#f0d7d7", fg="#5b2733", relief="flat").pack(side="left")

        self.hint_var = tk.StringVar(value="Enter — открыть; Backspace — уровень вверх")
        tk.Label(action_bar, textvariable=self.hint_var, bg=wrapper.cget("bg"), fg="#67738a").pack(side="right")

        self.listbox = tk.Listbox(
            wrapper,
            font=("Consolas", 11),
            bd=0,
            exportselection=False,
            activestyle="none",
            bg="#ffffff",
            fg="#223244",
            selectbackground="#b8d8ff",
            selectforeground="#14263f",
        )
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", self.open_selected)
        self.listbox.bind("<Return>", self.open_selected)
        self.listbox.bind("<BackSpace>", lambda _event: self.go_up())
        self.listbox.bind("<<ListboxSelect>>", self.remember_selection)
        self.listbox.bind("<Delete>", lambda _event: self.delete_selected())

        self.status_var = tk.StringVar(value="")
        status_label = tk.Label(wrapper, textvariable=self.status_var, anchor="w", bg=wrapper.cget("bg"), fg="#67738a")
        status_label.pack(fill="x", pady=(8, 0))

        self.refresh()
        self.listbox.focus_set()

    def refresh(self) -> None:
        selected_name = self.selected_name
        self.listbox.delete(0, tk.END)
        self.entry_targets = []
        try:
            items = self.app.virtual_fs.list_dir(self.current_path)
        except ValueError:
            self.status_var.set("Каталог не найден")
            return

        self._insert_entry(".", ".")
        self._insert_entry("..", "..")
        for item in items:
            self._insert_entry(item.name, item)

        if selected_name is not None:
            self._restore_selection(selected_name)
        elif self.listbox.size() > 0:
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self.selected_name = self._selected_name()
        self._update_status(len(items))
        self.listbox.focus_set()

    def _insert_entry(self, name: str, target: VirtualItem | str) -> None:
        if target == ".":
            prefix = "[DIR]"
        elif target == "..":
            prefix = "[DIR]"
        elif isinstance(target, VirtualItem) and target.is_dir:
            prefix = "[DIR]"
        elif isinstance(target, VirtualItem) and target.name.endswith(".app"):
            prefix = "[APP]"
        elif isinstance(target, VirtualItem) and target.name.endswith(".log"):
            prefix = "[LOG]"
        elif isinstance(target, VirtualItem) and target.name.endswith(".txt"):
            prefix = "[TXT]"
        else:
            prefix = "[FILE]"
        self.listbox.insert(tk.END, f"{prefix} {name}")
        self.entry_targets.append((name, target))

    def open_selected(self, _event=None) -> None:
        entry = self._selected_entry()
        if entry is None:
            return
        item_name, target = entry
        if target == ".":
            self.refresh()
            return
        if target == "..":
            self.go_up()
            return
        if not isinstance(target, VirtualItem):
            return
        if target.is_dir:
            self.current_path.append(target.name)
            self.selected_name = None
            self.refresh()
            return

        if target.name.endswith(".app"):
            if self.app.launch_app_from_file(target.name):
                self.app.log(f"Из файлового менеджера запущена программа «{target.name}».")
                self.status_var.set(f"Старт программы: {target.name}")
            else:
                messagebox.showinfo(APP_TITLE, "Для выбранного объекта нет связанной программы.")
            return

        self.app.open_virtual_file(target)
        self.status_var.set(f"Открыт документ: {target.name}")

    def remember_selection(self, _event=None) -> None:
        self.selected_name = self._selected_name()
        self._update_selection_hint()

    def _selected_entry(self) -> tuple[str, VirtualItem | str] | None:
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.entry_targets[selection[0]]

    def _selected_name(self) -> str | None:
        entry = self._selected_entry()
        if entry is None:
            return None
        return entry[0]

    def _restore_selection(self, item_name: str) -> None:
        for index, (current_name, _target) in enumerate(self.entry_targets):
            if current_name == item_name:
                self.listbox.selection_set(index)
                self.listbox.activate(index)
                self.listbox.see(index)
                self._update_selection_hint()
                return

    def _display_path(self) -> str:
        return "VVU-DeskShell:/" if not self.current_path else f"VVU-DeskShell:/{'/'.join(self.current_path)}"

    def go_up(self) -> None:
        if not self.current_path:
            return
        self.current_path.pop()
        self.selected_name = ".."
        self.refresh()

    def create_folder(self) -> None:
        self._create_item("dir", "Создание каталога")

    def create_file(self) -> None:
        self._create_item("file", "Создание документа")

    def _create_item(self, item_type: str, prompt_title: str) -> None:
        name = self.app.prompt_text(prompt_title, "Укажите имя объекта:")
        if name is None:
            return
        try:
            item = self.app.virtual_fs.create_item(self.current_path, name, item_type)
        except ValueError as error:
            messagebox.showerror(APP_TITLE, str(error))
            return
        self.selected_name = item.name
        kind = "каталог" if item_type == "dir" else "документ"
        self.app.log(f"В файловом менеджере добавлен {kind} «{item.name}».")
        self.refresh()

    def delete_selected(self) -> None:
        item_name = self._selected_name()
        if item_name is None:
            messagebox.showinfo(APP_TITLE, "Сначала выделите объект в списке.")
            return
        if item_name in {".", ".."}:
            messagebox.showinfo(APP_TITLE, "Служебные записи «.» и «..» удалять нельзя.")
            return
        try:
            removed = self.app.virtual_fs.delete_item(self.current_path, item_name)
        except ValueError as error:
            messagebox.showerror(APP_TITLE, str(error))
            return
        self.selected_name = None
        kind = "каталог" if removed.is_dir else "документ"
        self.app.log(f"Из файлового менеджера удалён {kind} «{removed.name}».")
        self.refresh()

    def _update_status(self, count: int) -> None:
        path = self._display_path()
        self.status_var.set(f"{path} | Объектов: {count}")
        self._update_selection_hint()

    def _update_selection_hint(self) -> None:
        item_name = self.selected_name
        if item_name is None:
            self.hint_var.set("Enter — открыть; Backspace — уровень вверх")
            return
        if item_name == ".":
            self.hint_var.set("«.» — обновить список текущего каталога")
            return
        if item_name == "..":
            self.hint_var.set("«..» — перейти на уровень выше")
            return
        if item_name.endswith(".app"):
            self.hint_var.set(f"«{item_name}» — двойной щелчок запускает программу")
            return
        self.hint_var.set(f"Выделено: {item_name}")

    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()
        self.app.terminate_process(self.pid, from_window=True)


class TaskManagerWindow(SuspendableWindowMixin):
    columns = ("pid", "name", "status", "cpu", "category")

    def __init__(self, app: "DeskShellApp", pid: int, title: str) -> None:
        self.app = app
        self.pid = pid
        self.window = tk.Toplevel(app.root)
        self.window.title(title)
        self.window.geometry("760x460")
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.sort_state = {column: False for column in self.columns}
        self.launch_choice = tk.StringVar(value=PROCESS_LAUNCH_OPTIONS[0])
        self.cpu_var = tk.StringVar(value="Загрузка ЦП: 0%")
        self.selected_pid_value: int | None = None  # Сохраняем PID выбранного процесса
        self._suspended = False

        root_frame = app.create_app_shell(self.window, title, can_maximize=True, accent="#2453a6", close_command=self.close)

        header = tk.Frame(root_frame, bg=root_frame.cget("bg"))
        header.pack(fill="x", pady=(0, 10))

        tk.Label(header, textvariable=self.cpu_var, font=("Segoe UI", 11, "bold"), bg=root_frame.cget("bg"), fg="#23324d").pack(side="left")

        tk.Label(header, text="Запуск:", bg=root_frame.cget("bg"), fg="#67738a").pack(side="left", padx=(20, 6))
        chooser = ttk.Combobox(
            header,
            textvariable=self.launch_choice,
            values=PROCESS_LAUNCH_OPTIONS,
            state="readonly",
            width=22,
        )
        chooser.pack(side="left")

        tk.Button(header, text="Старт", command=self.launch_process, bg="#cfe1ff", fg="#17325f", relief="flat").pack(side="left", padx=6)
        tk.Button(header, text="Приостановить", command=self.suspend_selected, bg="#ffe5b4", fg="#5a3a1a", relief="flat").pack(side="left", padx=6)
        tk.Button(header, text="Возобновить", command=self.resume_selected, bg="#d4f1d4", fg="#1a5a1a", relief="flat").pack(side="left", padx=6)
        tk.Button(header, text="Стоп", command=self.stop_selected, bg="#f6ddd2", fg="#5b2733", relief="flat").pack(side="left")
        tk.Button(header, text="Выключить оболочку", command=self.app.shutdown, bg="#e8edf4", fg="#33425c", relief="flat").pack(side="right")

        self.tree = ttk.Treeview(root_frame, columns=self.columns, show="headings", height=14)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _event: self.stop_selected())
        self.tree.bind("«TreeviewSelect»", self.remember_selection)
        # Добавляем привязку для сохранения выделения при сортировке
        self.tree.bind("<ButtonRelease-1>", self._on_click)

        headings = {
            "pid": "№",
            "name": "Задача",
            "status": "Состояние",
            "cpu": "ЦП %",
            "category": "Класс",
        }
        widths = {"pid": 80, "name": 240, "status": 120, "cpu": 80, "category": 160}
        for column in self.columns:
            self.tree.heading(column, text=headings[column], command=lambda col=column: self._sort_with_selection(col))
            self.tree.column(column, width=widths[column], anchor="center")

        footer = tk.Label(
            root_frame,
            text="Двойной щелчок по строке завершает задачу. Кнопки: Приостановить/Возобновить/Стоп",
            anchor="w",
            bg=root_frame.cget("bg"),
            fg="#67738a",
        )
        footer.pack(fill="x", pady=(8, 0))

        # Запускаем периодическое обновление, но умное
        self._update_counter = 0
        self.refresh()

    def _on_click(self, event=None) -> None:
        """Сохраняем выделение при клике"""
        self.remember_selection()

    def _sort_with_selection(self, column: str) -> None:
        """Сортировка с сохранением выделения"""
        # Сохраняем текущее выделение перед сортировкой
        self.remember_selection()
        # Выполняем сортировку
        reverse = not self.sort_state.get(column, False)
        self.sort_state[column] = reverse
        self.app.sort_processes(column, reverse)
        # Обновляем таблицу с восстановлением выделения
        self.refresh()

    def launch_process(self) -> None:
        choice = self.launch_choice.get()
        if choice == "Калькулятор":
            self.app.launch_calculator()
        elif choice == "Файловый менеджер":
            self.app.launch_explorer()
        elif choice == "Параметры":
            self.app.launch_settings()
        else:
            self.app.launch_background_process()
        # После запуска нового процесса сохраняем текущее выделение
        self.remember_selection()

    def selected_pid(self) -> int | None:
        """Получаем PID выбранного процесса"""
        selection = self.tree.selection()
        if not selection:
            return self.selected_pid_value  # Возвращаем сохраненный PID, если ничего не выбрано
        try:
            values = self.tree.item(selection[0], "values")
            if values:
                return int(values[0])
        except (IndexError, ValueError, TypeError):
            pass
        return self.selected_pid_value

    def remember_selection(self, _event=None) -> None:
        """Запоминаем PID выбранного процесса"""
        selection = self.tree.selection()
        if selection:
            try:
                values = self.tree.item(selection[0], "values")
                if values:
                    self.selected_pid_value = int(values[0])
            except (IndexError, ValueError, TypeError):
                pass
        # Если ничего не выбрано, оставляем предыдущее значение

    def suspend_selected(self) -> None:
        pid = self.selected_pid()
        if pid is None:
            messagebox.showinfo(APP_TITLE, "Сначала выделите задачу в таблице.")
            return
        if pid == self.app.desktop_pid:
            messagebox.showinfo(APP_TITLE, "Нельзя приостановить рабочую зону.")
            return
        self.app.suspend_process(pid)
        # Сохраняем PID после операции
        self.selected_pid_value = pid
        self.refresh()

    def resume_selected(self) -> None:
        pid = self.selected_pid()
        if pid is None:
            messagebox.showinfo(APP_TITLE, "Сначала выделите задачу в таблице.")
            return
        self.app.resume_process(pid)
        self.selected_pid_value = pid
        self.refresh()

    def stop_selected(self) -> None:
        pid = self.selected_pid()
        if pid is None:
            messagebox.showinfo(APP_TITLE, "Сначала выделите задачу в таблице.")
            return
        if pid == self.app.desktop_pid:
            self.app.shutdown()
            return
        self.app.terminate_process(pid)
        # После удаления процесса сбрасываем выделение, если был удален выбранный
        if self.selected_pid_value == pid:
            self.selected_pid_value = None
        self.refresh()

    def sort_by(self, column: str) -> None:
        reverse = self.sort_state[column]
        self.sort_state[column] = not reverse
        self.app.sort_processes(column, reverse)
        self.refresh()

    def refresh(self) -> None:
        """Обновление таблицы с восстановлением выделения"""
        # Сохраняем текущую позицию прокрутки
        scroll_position = None
        if hasattr(self, 'tree') and self.tree.yview():
            scroll_position = self.tree.yview()

        # Обновляем данные
        self.cpu_var.set(f"Загрузка ЦП: {self.app.cpu_usage}%")

        # Сохраняем выбранный PID до очистки
        current_selected_pid = self.selected_pid_value

        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Заполняем заново
        for record in self.app.process_snapshot:
            # Форматируем статус
            status_text = record.status
            if record.status == "Приостановлена":
                status_text = "🟡 Приостановлена"

            item_id = self.tree.insert(
                "",
                tk.END,
                values=(record.pid, record.name, status_text, record.cpu, record.category),
            )

            # Применяем стиль для приостановленных процессов
            if record.status == "Приостановлена":
                self.tree.tag_configure("suspended", background="#fff3cd")
                self.tree.item(item_id, tags=("suspended",))

            # Восстанавливаем выделение, если PID совпадает
            if current_selected_pid == record.pid:
                self.tree.selection_set(item_id)
                self.tree.see(item_id)

        # Восстанавливаем позицию прокрутки
        if scroll_position:
            try:
                self.tree.yview_moveto(scroll_position[0])
            except (IndexError, tk.TclError):
                pass

        # Если выделение не восстановилось, но есть процессы, выбираем первый
        if not self.tree.selection() and self.tree.get_children():
            first_item = self.tree.get_children()[0]
            self.tree.selection_set(first_item)
            self.remember_selection()

    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()
        self.app.terminate_process(self.pid, from_window=True)


class DeskShellApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(f"{APP_TITLE} {APP_VERSION}")
        self.root.geometry("1120x720")
        self.root.minsize(960, 600)
        self.root.configure(bg="#e2e8f0")
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

        self.processes = TaskChain()
        self.process_snapshot: list[TaskEntry] = []
        self.windows: dict[int, object] = {}
        self.window_to_pid: dict[str, int] = {}
        self.task_buttons: dict[int, tk.Button] = {}
        self.taskbar_labels: dict[int, str] = {}
        self.minimized_windows: set[int] = set()
        self.log_file_path = Path(__file__).with_name(LOG_FILENAME)
        self.icons_dir = Path(__file__).with_name(ICONS_DIRNAME)
        self.wallpapers_dir = Path(__file__).with_name(WALLPAPERS_DIRNAME)
        self.wallpapers_dir.mkdir(parents=True, exist_ok=True)
        self.wallpaper_photo: tk.PhotoImage | None = None
        self.wallpaper_canvas_item: int | None = None
        self.virtual_fs = VirtualFileSystem(self.log_file_path)
        self.user_store = UserStore(Path(__file__).with_name("users.json"))
        self.current_user: str | None = None
        self.user_settings = {"theme": "slate", "background": "purple", "wallpaper": "", "show_seconds": True}
        self.desktop_pid = 1
        self.next_pid = 2
        self.cpu_usage = 0
        self.log_lines: list[str] = []
        self.login_window: LoginWindow | None = None
        self.desktop_ready = False
        self.current_time_var = tk.StringVar(value="--:--:--")
        self.user_label_var = tk.StringVar(value="Аккаунт: гость")
        self.desktop_icons: list[DesktopIcon] = []
        self.selected_desktop_icon: DesktopIcon | None = None
        self.icon_images: dict[str, tk.PhotoImage] = {}
        self._icons_wallpaper_mode: bool | None = None

        self.show_login()

    def suspend_process(self, pid: int) -> None:
        if pid == self.desktop_pid:
            messagebox.showinfo(APP_TITLE, "Нельзя приостановить рабочую зону.")
            return

        record = self.processes.get(pid)
        if record is None:
            return

        if record.status == "Приостановлена":
            messagebox.showinfo(APP_TITLE, f"Задача «{record.name}» уже приостановлена.")
            return

        record.status = "Приостановлена"
        self.log(f"Приостановлена задача «{record.name}» (№ {record.pid}).")

        window_obj = self.windows.get(pid)
        if window_obj is not None and hasattr(window_obj, 'freeze'):
            window_obj.freeze()

        self.refresh_views()

    def resume_process(self, pid: int) -> None:
        record = self.processes.get(pid)
        if record is None:
            return

        if record.status == "Активна":
            messagebox.showinfo(APP_TITLE, f"Задача «{record.name}» уже активна.")
            return

        record.status = "Активна"
        self.log(f"Возобновлена задача «{record.name}» (№ {record.pid}).")

        window_obj = self.windows.get(pid)
        if window_obj is not None and hasattr(window_obj, 'unfreeze'):
            window_obj.unfreeze()

        self.refresh_views()

    def show_login(self) -> None:
        self.login_window = LoginWindow(self)

    def complete_login(self, username: str) -> None:
        self.current_user = username
        self.user_settings = self.user_store.get_settings(username)
        if not self.desktop_ready:
            self._initialize_session()
        self.apply_user_settings()
        self.user_label_var.set(f"Аккаунт: {username}")
        self.log(f"Авторизация: пользователь «{username}» (проверка хеша пароля).")
        bg_label = self.current_background()["label"]
        self.log(f"Фон рабочего стола: «{bg_label}». На столе доступны значки приложений.")

    def _initialize_session(self) -> None:
        self.root.title(f"{APP_TITLE} {APP_VERSION}")
        self.root.geometry("1120x720")
        self.root.minsize(960, 600)
        self.root.resizable(True, True)
        self._build_desktop()
        self._register_desktop_process()
        self.launch_background_process(name="Менеджер окон")
        self.launch_background_process(name="Служба мониторинга")
        self.refresh_views()
        self._tick_cpu()
        self._tick_time()
        self.desktop_ready = True
        self.apply_user_settings()
        self.root.after_idle(self._apply_desktop_wallpaper)
        self.root.after(400, self._apply_desktop_wallpaper)

    def _build_desktop(self) -> None:
        self.top_frame = tk.Frame(self.root, bg="#d9e6f2")
        self.top_frame.pack(fill="both", expand=True)

        self.main_panel = tk.Frame(self.top_frame, bg="#eef4fb")
        self.main_panel.pack(fill="both", expand=True)

        desktop_header = tk.Frame(self.main_panel, bg="#eef4fb")
        desktop_header.pack(fill="x", padx=18, pady=(16, 10))
        self.desktop_header = desktop_header

        self.desktop_title_label = tk.Label(
            desktop_header,
            text="Рабочая область",
            font=("Segoe UI", 18, "bold"),
            bg="#eef4fb",
            fg="#1d3557",
        )
        self.desktop_title_label.pack(side="left")

        self.desktop_hint_label = tk.Label(
            desktop_header,
            text="Значки приложений: двойной щелчок — запуск, перетаскивание — смена позиции.",
            font=("Segoe UI", 10),
            bg="#eef4fb",
            fg="#67809f",
        )
        self.desktop_hint_label.pack(side="left", padx=14, pady=6)

        self.status_panel = tk.Frame(desktop_header, bg="#eef4fb")
        self.status_panel.pack(side="right")

        self.user_label = tk.Label(
            self.status_panel,
            textvariable=self.user_label_var,
            font=("Segoe UI", 10, "bold"),
            bg="#dbe8f6",
            fg="#1d3557",
            padx=10,
            pady=4,
        )
        self.user_label.pack(side="left", padx=4)

        self.process_count_label = tk.Label(
            self.status_panel,
            text="Задач: 0",
            font=("Segoe UI", 10),
            bg="#dbe8f6",
            fg="#1d3557",
            padx=10,
            pady=4,
        )
        self.process_count_label.pack(side="left", padx=4)

        self.cpu_label = tk.Label(
            self.status_panel,
            text="Загрузка ЦП: 0%",
            font=("Segoe UI", 10, "bold"),
            bg="#dbe8f6",
            fg="#1d3557",
            padx=10,
            pady=4,
        )
        self.cpu_label.pack(side="left", padx=4)

        self.workspace = tk.Frame(self.main_panel, bg="#eef4fb")
        self.workspace.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        # Только canvas без боковой панели
        self.desktop_canvas = tk.Canvas(self.workspace, bg="#f7fbff", highlightthickness=0, bd=0)
        self.desktop_canvas.pack(fill="both", expand=True)
        self.desktop_canvas.bind("<Button-1>", lambda _event: self.select_desktop_icon(None))
        self.desktop_canvas.bind("<Button-3>", self._desktop_context_menu)
        self.desktop_canvas.bind("<Configure>", self._on_desktop_resize)

        self._build_desktop_icons()

        self.taskbar = tk.Frame(self.root, bg="#0f172a", height=56)
        self.taskbar.pack(fill="x", side="bottom")
        self.taskbar.pack_propagate(False)

        self.start_button = tk.Button(
            self.taskbar,
            text="Меню",
            command=self.toggle_start_menu,
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="#f8fbff",
            activebackground="#1d4ed8",
            relief="flat",
            padx=18,
        )
        self.start_button.pack(side="left", padx=10, pady=8)
        self._apply_start_button_icon()

        self.taskbar_buttons_frame = tk.Frame(self.taskbar, bg="#0f172a")
        self.taskbar_buttons_frame.pack(side="left", fill="x", expand=True)

        self.start_menu = tk.Menu(self.root, tearoff=False, bg="#f8fbff", fg="#1d3557", activebackground="#dbe7ff",
                                  activeforeground="#1d3557")
        self.start_menu.add_command(label="Калькулятор", command=self.launch_calculator)
        self.start_menu.add_command(label="Файловый менеджер", command=self.launch_explorer)
        self.start_menu.add_command(label="Монитор задач", command=self.launch_task_manager)
        self.start_menu.add_command(label="Параметры и обои", command=self.launch_settings)
        self.start_menu.add_command(label="Журнал на диске", command=self.open_system_log)
        self.start_menu.add_command(label="Фоновая служба", command=self.launch_background_process)
        self.start_menu.add_separator()
        self.start_menu.add_command(label="Завершить сеанс", command=self.shutdown)

        self.taskbar_time_label = tk.Label(
            self.taskbar,
            textvariable=self.current_time_var,
            font=("Consolas", 11, "bold"),
            bg="#0f172a",
            fg="#f8fbff",
        )
        self.taskbar_time_label.pack(side="right", padx=12)

    def create_app_shell(self, window: tk.Toplevel, title: str, can_maximize: bool, accent: str, close_command) -> tk.Frame:
        window.overrideredirect(True)
        window.configure(bg="#dbe7f3")

        outer = tk.Frame(window, bg="#dbe7f3", padx=10, pady=10)
        outer.pack(fill="both", expand=True)

        card = tk.Frame(outer, bg="#f7fbff", highlightthickness=1, highlightbackground="#d6e2f0")
        card.pack(fill="both", expand=True)

        header = tk.Frame(card, bg=accent, height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        self._bind_custom_window_drag(window, header)

        title_label = tk.Label(header, text=title, font=("Segoe UI", 11, "bold"), bg=accent, fg="#f8fbff")
        title_label.pack(side="left", padx=14)
        self._bind_custom_window_drag(window, title_label)

        controls = tk.Frame(header, bg=accent)
        controls.pack(side="right", padx=8)

        tk.Button(controls, text="_", command=lambda current=window: self.minimize_window(current), bg=accent, fg="#f8fbff", activebackground=accent, relief="flat", width=3).pack(side="left", padx=2, pady=8)
        if can_maximize:
            tk.Button(controls, text="[]", command=lambda current=window: self.toggle_window_state(current), bg=accent, fg="#f8fbff", activebackground=accent, relief="flat", width=3).pack(side="left", padx=2, pady=8)
        tk.Button(controls, text="X", command=close_command, bg=accent, fg="#f8fbff", activebackground="#c0392b", relief="flat", width=3).pack(side="left", padx=2, pady=8)

        body = tk.Frame(card, bg="#f7fbff", padx=16, pady=16)
        body.pack(fill="both", expand=True)
        return body

    def _bind_custom_window_drag(self, window: tk.Toplevel, widget: tk.Widget) -> None:
        def start_move(event) -> None:
            window._drag_x = event.x_root  # type: ignore[attr-defined]
            window._drag_y = event.y_root  # type: ignore[attr-defined]

        def move_window(event) -> None:
            if str(window.state()) == "zoomed":
                return
            last_x = getattr(window, "_drag_x", event.x_root)
            last_y = getattr(window, "_drag_y", event.y_root)
            delta_x = event.x_root - last_x
            delta_y = event.y_root - last_y
            new_x = window.winfo_x() + delta_x
            new_y = window.winfo_y() + delta_y
            window.geometry(f"+{new_x}+{new_y}")
            window._drag_x = event.x_root  # type: ignore[attr-defined]
            window._drag_y = event.y_root  # type: ignore[attr-defined]

        widget.bind("<ButtonPress-1>", start_move)
        widget.bind("<B1-Motion>", move_window)

    def minimize_window(self, window: tk.Toplevel) -> None:
        pid = self.window_to_pid.get(str(window))
        if pid is None:
            window.withdraw()
            return
        self.minimized_windows.add(pid)
        window.withdraw()
        button = self.task_buttons.get(pid)
        if button is not None:
            button.configure(bg=self.current_palette()["taskbar_button"])

    def toggle_window_state(self, window: tk.Toplevel) -> None:
        current_state = str(window.state())
        if current_state == "zoomed":
            window.state("normal")
        else:
            window.state("zoomed")

    def wallpaper_choice_labels(self) -> list[str]:
        return [WALLPAPER_NONE_LABEL, *list_wallpaper_files(self.wallpapers_dir)]

    def wallpaper_label_for_file(self, filename: str) -> str:
        if not filename:
            return WALLPAPER_NONE_LABEL
        return filename

    def wallpaper_file_for_label(self, label: str) -> str:
        if label == WALLPAPER_NONE_LABEL:
            return ""
        return label

    def _load_wallpaper_photo(self, path: Path, target_w: int, target_h: int) -> tk.PhotoImage | None:
        target_w = max(target_w, 100)
        target_h = max(target_h, 100)
        try:
            from PIL import Image, ImageTk
        except ImportError:
            Image = None
            ImageTk = None

        if Image is not None and ImageTk is not None:
            try:
                image = Image.open(path).convert("RGB")
                # Используем Resampling.LANCZOS, если библиотека PIL доступна
                image = image.resize((target_w, target_h), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
            except OSError as error:
                self.log(f"Ошибка чтения обоев: {error}")
                return None

        try:
            source = tk.PhotoImage(file=str(path))
        except tk.TclError:
            self.log(f"Формат не поддержан. Установите: pip install pillow — для JPG/PNG.")
            return None

        current = source
        while current.width() < target_w or current.height() < target_h:
            current = current.zoom(2, 2)
        while current.width() > target_w or current.height() > target_h:
            current = current.subsample(2, 2)
        return current

    def _apply_desktop_wallpaper(self) -> None:
        if not self.desktop_ready:
            return
        self.root.update_idletasks()
        filename = self.user_settings.get("wallpaper", "")
        width = max(int(self.desktop_canvas.winfo_width()), 100)
        height = max(int(self.desktop_canvas.winfo_height()), 100)
        background = self.current_background()

        # Полностью очищаем холст от СТАРЫХ обоев, чтобы не плодить слои
        if self.wallpaper_canvas_item is not None:
            self.desktop_canvas.delete(self.wallpaper_canvas_item)
            self.wallpaper_canvas_item = None
        self.wallpaper_photo = None

        if filename:
            path = self.wallpapers_dir / filename
            if path.is_file():
                photo = self._load_wallpaper_photo(path, width, height)
                if photo is not None:
                    self.wallpaper_photo = photo
                    # Создаем обои
                    self.wallpaper_canvas_item = self.desktop_canvas.create_image(
                        0, 0, image=self.wallpaper_photo, anchor="nw", tags="wallpaper"
                    )
                    # Отправляем обои на самый нижний слой ДО того, как пересоздадим иконки
                    self.desktop_canvas.tag_lower(self.wallpaper_canvas_item)

                    # ПЕРЕЗАПУСКАЕМ создание иконок, чтобы их картинки инициализировались ПОВЕРХ новых обоев
                    self._rebuild_desktop_icons()
                    return
            self.log(f"Файл обоев не найден: {path}")

        # Если фото нет — просто красим фон
        self.desktop_canvas.configure(bg=background["surface"])
        self._rebuild_desktop_icons()

        # Умный обработчик клика по холсту
        def on_canvas_click(event):
            # Ищем, какие элементы холста находятся ровно под курсором мыши
            clicked_items = self.desktop_canvas.find_withtag("current")

            # Если мы кликнули на обои (или вообще мимо иконок)
            if not clicked_items or self.wallpaper_canvas_item in clicked_items:
                # Сбрасываем выделение, так как это клик по пустому месту
                self.select_desktop_icon(None)
            else:
                # Клик попал на элемент иконки (картинку/текст), Tkinter сам вызовет
                # нужный bind на уровне класса DesktopIcon, здесь ничего делать не нужно
                pass

        if filename:
            path = self.wallpapers_dir / filename
            if path.is_file():
                photo = self._load_wallpaper_photo(path, width, height)
                if photo is not None:
                    self.wallpaper_photo = photo
                    self.wallpaper_canvas_item = self.desktop_canvas.create_image(
                        0, 0, image=self.wallpaper_photo, anchor="nw", tags="wallpaper"
                    )

                    # Биндим клик на элемент обоев с проверкой «сквозного» клика
                    self.desktop_canvas.tag_bind(self.wallpaper_canvas_item, "<Button-1>", on_canvas_click)

                    # Принудительно отправляем обои на самый нижний слой (z-index)
                    self.desktop_canvas.tag_lower(self.wallpaper_canvas_item)

                    # Гарантированно поднимаем все остальные элементы (включая картинки иконок) выше обоев
                    for item in self.desktop_canvas.find_all():
                        if item != self.wallpaper_canvas_item:
                            self.desktop_canvas.tag_raise(item)

                    self._sync_desktop_icons()
                    return
            self.log(f"Файл обоев не найден: {path}")

        # Если фото-обоев нет, используем стандартную заливку цвета
        self.desktop_canvas.configure(bg=background["surface"])
        self.desktop_canvas.bind("<Button-1>", on_canvas_click)
        self._sync_desktop_icons()

    def icon_chip_color(self) -> str:
        return self.current_background()["surface"]

    def _rebuild_desktop_icons(self) -> None:
        selected = self.selected_desktop_icon

        # Жестко удаляем старые объекты иконок с холста
        for icon in self.desktop_icons:
            try:
                icon.destroy()
            except Exception:
                pass

        self.desktop_icons = []
        # Строим их заново. Теперь их картинки привяжутся к холсту поверх обоев
        self._build_desktop_icons()

        self.selected_desktop_icon = None
        if selected is not None:
            for icon in self.desktop_icons:
                if icon.label == selected.label:
                    self.select_desktop_icon(icon)
                    break

        # Синхронизируем слои
        self._sync_desktop_icons()

    def _sync_desktop_icons(self) -> None:
        # Убираем отсюда лишние вызовы перезагрузки, чтобы не зацикливать код
        for icon in self.desktop_icons:
            icon.refresh_theme()

        # Принудительно поднимаем иконки в самый верх стека вызовов холста
        for item in self.desktop_canvas.find_all():
            if item != self.wallpaper_canvas_item:
                self.desktop_canvas.tag_raise(item)

    def _on_desktop_resize(self, event=None) -> None:
        if event is not None and event.widget is not self.desktop_canvas:
            return
        if self.user_settings.get("wallpaper"):
            self.root.after(80, self._apply_desktop_wallpaper)

    def _desktop_context_menu(self, event) -> None:
        menu = tk.Menu(self.root, tearoff=False)
        photo_menu = tk.Menu(menu, tearoff=False)
        photo_menu.add_command(label=WALLPAPER_NONE_LABEL, command=lambda: self._set_desktop_wallpaper(""))
        files = list_wallpaper_files(self.wallpapers_dir)
        if files:
            for filename in files:
                photo_menu.add_command(
                    label=filename,
                    command=lambda name=filename: self._set_desktop_wallpaper(name),
                )
        else:
            photo_menu.add_command(label="(нет PNG в wallpapers/)", state="disabled")
        menu.add_cascade(label="Обои (PNG из wallpapers)", menu=photo_menu)

        color_menu = tk.Menu(menu, tearoff=False)
        for key, option in BACKGROUND_OPTIONS.items():
            color_menu.add_command(
                label=option["label"],
                command=lambda bg_key=key: self._set_desktop_color(bg_key),
            )
        menu.add_cascade(label="Цвет подложки (без фото)", menu=color_menu)
        menu.add_command(label="Параметры оболочки", command=self.launch_settings)
        menu.tk_popup(event.x_root, event.y_root)
        menu.grab_release()

    def _set_desktop_wallpaper(self, filename: str) -> None:
        self.user_settings["wallpaper"] = filename
        self.save_user_settings()
        self.apply_user_settings()
        self.root.after(100, self._apply_desktop_wallpaper)
        if filename:
            self.log(f"Обои рабочего стола: «{filename}».")
        else:
            label = self.current_background()["label"]
            self.log(f"Обои отключены, фон: «{label}».")

    def _set_desktop_color(self, bg_key: str) -> None:
        self.user_settings["background"] = bg_key
        if hasattr(self, "save_user_settings"):
            self.save_user_settings()
        self.apply_user_settings()

        preset = BACKGROUND_OPTIONS.get(bg_key, BACKGROUND_OPTIONS["white"])
        label = preset["label"]
        self.log(f"Цвет подложки: «{label}».")

    def _build_desktop_icons(self) -> None:
        icon_specs = [
            ("Калькулятор", self.launch_calculator, 28, 28, "vychislitel"),
            ("Файловый менеджер", self.launch_explorer, 28, 140, "fayly"),
            ("Монитор задач", self.launch_task_manager, 28, 252, "zadachi"),
            ("Параметры", self.launch_settings, 150, 28, "parametry"),
            ("События", self.open_system_log, 150, 140, "zhurnal"),
        ]
        self.desktop_icons = []
        for label, command, x_pos, y_pos, asset_id in icon_specs:
            self.desktop_icons.append(DesktopIcon(self, self.desktop_canvas, label, command, x_pos, y_pos, asset_id))

    def select_desktop_icon(self, icon: DesktopIcon | None) -> None:
        self.selected_desktop_icon = icon
        for current_icon in self.desktop_icons:
            current_icon.set_selected(current_icon is icon)

    def load_icon_image(self, asset_id: str) -> tk.PhotoImage | None:
        if asset_id in self.icon_images:
            return self.icon_images[asset_id]

        icon_name = ICON_ASSETS.get(asset_id)
        if icon_name is None:
            return None

        icon_path = self.icons_dir / icon_name
        if not icon_path.exists():
            return None

        try:
            image = tk.PhotoImage(file=str(icon_path))
        except tk.TclError:
            return None
        max_size = 52
        scale_ratio = max(image.width() / max_size, image.height() / max_size, 1)
        scale_factor = max(1, math.ceil(scale_ratio))
        if scale_factor > 1:
            image = image.subsample(scale_factor, scale_factor)
        self.icon_images[asset_id] = image
        return image

    def _apply_start_button_icon(self) -> None:
        menu_icon = self.load_icon_image("menu")
        if menu_icon is None:
            return
        self.start_button.configure(image=menu_icon, compound="left", text=" Меню", padx=12)

    def toggle_start_menu(self) -> None:
        start_x = self.start_button.winfo_rootx()
        start_y = self.start_button.winfo_rooty() - self.start_menu.index("end") * 28 - 6
        self.start_menu.tk_popup(start_x, max(0, start_y))
        self.start_menu.grab_release()

    def _register_desktop_process(self) -> None:
        desktop = TaskEntry(
            pid=self.desktop_pid,
            name="Рабочая зона",
            status="Активна",
            cpu=4,
            category="Система",
            window_id="desktop",
        )
        self.processes.append(desktop)
        self.log("Инициализирована рабочая зона сеанса.")

    def _create_process(self, name: str, category: str, window_id: str | None = None) -> TaskEntry:
        record = TaskEntry(
            pid=self.next_pid,
            name=name,
            status="Активна",
            cpu=random.randint(1, 12),
            category=category,
            window_id=window_id,
        )
        self.next_pid += 1
        self.processes.append(record)
        self.log(f"Запущена задача «{record.name}» (№ {record.pid}).")
        return record

    def launch_calculator(self) -> None:
        title = f"Калькулятор #{self.next_pid}"
        record = self._create_process(title, "Приложение")
        window = CalculatorWindow(self, record.pid, title)
        self._bind_window(record, window.window, title)
        self.windows[record.pid] = window
        self.refresh_views()

    def launch_explorer(self) -> None:
        title = f"Файловый менеджер #{self.next_pid}"
        record = self._create_process(title, "Приложение")
        window = ExplorerWindow(self, record.pid, title)
        self._bind_window(record, window.window, title)
        self.windows[record.pid] = window
        self.refresh_views()

    def launch_task_manager(self) -> None:
        title = f"Монитор задач #{self.next_pid}"
        record = self._create_process(title, "Служебное")
        window = TaskManagerWindow(self, record.pid, title)
        self._bind_window(record, window.window, title)
        self.windows[record.pid] = window
        self.refresh_views()

    def launch_settings(self) -> None:
        title = f"Параметры #{self.next_pid}"
        record = self._create_process(title, "Служебное")
        window = SettingsWindow(self, record.pid, title)
        self._bind_window(record, window.window, title)
        self.windows[record.pid] = window
        self.refresh_views()

    def open_virtual_file(self, item: VirtualItem) -> None:
        content = self.virtual_fs.read_file(item)
        self.open_text_viewer(item.name, content)

    def open_text_viewer(self, file_name: str, content: str) -> None:
        title = f"Чтение: {file_name} #{self.next_pid}"
        record = self._create_process(title, "Просмотр")
        window = TextViewerWindow(self, record.pid, title, content)
        self._bind_window(record, window.window, title)
        self.windows[record.pid] = window
        self.refresh_views()

    def open_system_log(self) -> None:
        log_item = self.virtual_fs.find_item(["Documents"], "desk_shell.log")
        if log_item is None:
            messagebox.showerror(APP_TITLE, "Файл журнала на диске не найден.")
            return
        self.open_virtual_file(log_item)

    def launch_background_process(self, name: str | None = None) -> None:
        label = name or f"Фоновая служба #{self.next_pid}"
        self._create_process(label, "Фон")
        self.refresh_views()

    def launch_app_from_file(self, file_name: str) -> bool:
        app_map = {
            "calculator.app": self.launch_calculator,
            "explorer.app": self.launch_explorer,
            "settings.app": self.launch_settings,
            "taskmgr.app": self.launch_task_manager,
        }
        launcher = app_map.get(file_name.lower())
        if launcher is None:
            return False
        launcher()
        return True

    def _bind_window(self, record: TaskEntry, window: tk.Toplevel, title: str) -> None:
        record.window_id = title
        self.window_to_pid[str(window)] = record.pid
        window.bind("<FocusIn>", lambda _event, pid=record.pid: self.highlight_taskbar(pid))
        self.add_taskbar_button(record.pid, title)
        self.highlight_taskbar(record.pid)
        self._raise_open_windows(active_pid=record.pid)

    def _raise_open_windows(self, active_pid: int | None = None) -> None:
        active_window: tk.Toplevel | None = None
        for pid, window_obj in self.windows.items():
            window = getattr(window_obj, "window", None)
            if window is None or not window.winfo_exists():
                continue
            if pid in self.minimized_windows and pid != active_pid:
                continue
            window.lift()
            if pid == active_pid:
                active_window = window

        if active_window is not None:
            self.minimized_windows.discard(active_pid)
            active_window.deiconify()
            active_window.lift()
            active_window.focus_force()

    def add_taskbar_button(self, pid: int, title: str) -> None:
        palette = self.current_palette()
        button = tk.Button(
            self.taskbar_buttons_frame,
            text=title,
            command=lambda selected_pid=pid: self.focus_process_window(selected_pid),
            relief="flat",
            bd=0,
            padx=10,
            bg=palette["taskbar_button"],
            fg="#f8f4eb",
            activebackground=palette["taskbar_active"],
        )
        button.pack(side="left", padx=6, pady=9)
        self.task_buttons[pid] = button
        self.taskbar_labels[pid] = title

    def focus_process_window(self, pid: int) -> None:
        window_obj = self.windows.get(pid)
        if window_obj is None:
            return
        window = getattr(window_obj, "window", None)
        if window is None or not window.winfo_exists():
            return
        self._raise_open_windows(active_pid=pid)
        self.highlight_taskbar(pid)

    def highlight_taskbar(self, pid: int) -> None:
        palette = self.current_palette()
        for current_pid, button in self.task_buttons.items():
            button.configure(bg=palette["taskbar_active"] if current_pid == pid else palette["taskbar_button"])

    def terminate_process(self, pid: int, from_window: bool = False) -> None:
        if pid == self.desktop_pid:
            self.shutdown()
            return

        record = self.processes.get(pid)
        if record is None:
            return

        window_obj = self.windows.pop(pid, None)
        if window_obj is not None:
            window = getattr(window_obj, "window", None)
            if window is not None and window.winfo_exists() and not from_window:
                window.destroy()
            if window is not None:
                self.window_to_pid.pop(str(window), None)

        button = self.task_buttons.pop(pid, None)
        if button is not None:
            button.destroy()
        self.taskbar_labels.pop(pid, None)
        self.minimized_windows.discard(pid)

        removed = self.processes.remove(pid)
        if removed is not None:
            self.log(f"Остановлена задача «{removed.name}» (№ {removed.pid}).")
        self.refresh_views()

    def sort_processes(self, column: str, reverse: bool) -> None:
        records = self.processes.values()
        if column in {"pid", "cpu"}:
            records.sort(key=lambda item: getattr(item, column), reverse=reverse)
        else:
            records.sort(key=lambda item: str(getattr(item, column)).lower(), reverse=reverse)

        self.processes = TaskChain()
        for record in records:
            self.processes.append(record)
        self.log(f"Таблица задач отсортирована по столбцу «{column}».")
        self.refresh_views()

    def refresh_views(self) -> None:
        if not self.desktop_ready:
            return
        # Показываем только приложения, исключая фоновые службы
        all_processes = self.processes.values()
        self.process_snapshot = [p for p in all_processes if p.category in ("Приложение", "Служебное", "Просмотр")]
        self.process_count_label.configure(text=f"Задач: {len(self.process_snapshot)}")
        self.cpu_label.configure(text=f"Загрузка ЦП: {self.cpu_usage}%")

        # Обновляем только существующие окна, но не принудительно
        for window in list(self.windows.values()):
            if hasattr(window, "refresh") and not getattr(window, '_refreshing', False):
                try:
                    window._refreshing = True
                    window.refresh()
                    window._refreshing = False
                except:
                    pass

    def _refresh_log_widget(self) -> None:
        pass

    def prompt_text(self, title: str, prompt: str) -> str | None:
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("300x130")
        dialog.configure(bg="#f7f3ed")
        dialog.transient(self.root)
        dialog.grab_set()

        value = tk.StringVar()
        result = {"text": None}

        frame = tk.Frame(dialog, bg="#f7f3ed", padx=14, pady=14)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text=prompt, bg="#f7f3ed").pack(anchor="w")
        entry = tk.Entry(frame, textvariable=value)
        entry.pack(fill="x", pady=(8, 12))
        entry.focus_set()

        button_row = tk.Frame(frame, bg="#f7f3ed")
        button_row.pack(fill="x")

        def confirm() -> None:
            result["text": ""] = value.get()
            dialog.destroy()

        def cancel() -> None:
            dialog.destroy()

        tk.Button(button_row, text="Готово", command=confirm, bg="#d8e2dc", relief="flat").pack(side="left")
        tk.Button(button_row, text="Отменить", command=cancel, bg="#eadfcb", relief="flat").pack(side="left", padx=6)

        dialog.bind("<Return>", lambda _event: confirm())
        dialog.bind("<Escape>", lambda _event: cancel())
        self.root.wait_window(dialog)
        return result["text"]

    def log(self, message: str) -> None:
        timestamped_message = f"[{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}] {message}"
        self.log_lines.append(timestamped_message)
        with self.log_file_path.open("a", encoding="utf-8") as log_file:
            log_file.write(timestamped_message + "\n")

    def current_palette(self) -> dict[str, str]:
        theme = self.user_settings.get("theme", "olive")
        return THEME_OPTIONS.get(theme, THEME_OPTIONS["olive"])

    def current_background(self) -> dict[str, str]:
        if self.user_settings.get("background") == "custom":
            surface = self.user_settings.get("custom_surface", "#ffffff")
            return {
                "label": f"Свой цвет ({surface})",
                "surface": surface,
                "log": "#ffffff",
                "text": "#1e293b",
            }
        background = self.user_settings.get("background", "white")
        if background not in BACKGROUND_OPTIONS:
            background = "white"
        return BACKGROUND_OPTIONS[background]

    def apply_user_settings(self) -> None:
        if not self.desktop_ready:
            return
        palette = self.current_palette()
        background = self.current_background()
        self.root.configure(bg=palette["root"])
        self.top_frame.configure(bg=palette["panel"])
        self.main_panel.configure(bg=palette["main"])
        self.desktop_header.configure(bg=palette["main"])
        self.status_panel.configure(bg=palette["main"])
        self.desktop_title_label.configure(bg=palette["main"], fg=palette["text"])
        self.desktop_hint_label.configure(bg=palette["main"], fg=palette["muted"])
        self.workspace.configure(bg=palette["main"])
        self._apply_desktop_wallpaper()

        # Настройка taskbar и связанных элементов
        self.taskbar.configure(bg=palette["taskbar"])
        self.taskbar_buttons_frame.configure(bg=palette["taskbar"])
        self.taskbar_time_label.configure(bg=palette["taskbar"], fg="#f8fbff")
        self.start_button.configure(bg=palette["start"], activebackground=palette["start_active"])
        self.user_label.configure(bg=palette["chip"], fg=palette["text"])
        self.process_count_label.configure(bg=palette["chip"], fg=palette["text"])
        self.cpu_label.configure(bg=palette["chip"], fg=palette["text"])
        self.start_menu.configure(bg="#f8fbff", fg=palette["text"], activebackground=palette["chip"], activeforeground=palette["text"])

        for button in self.task_buttons.values():
            button.configure(bg=palette["taskbar_button"], activebackground=palette["taskbar_active"])

        for icon in self.desktop_icons:
            icon.refresh_theme()

    def save_user_settings(self) -> None:
        if self.current_user is None:
            return
        self.user_store.update_settings(self.current_user, self.user_settings)

    def _tick_time(self) -> None:
        now = datetime.now()
        time_format = "%H:%M:%S" if self.user_settings.get("show_seconds", True) else "%H:%M"
        self.current_time_var.set(now.strftime(f"%d.%m.%Y  {time_format}"))
        self.root.after(1000, self._tick_time)

    def _tick_cpu(self) -> None:
        total = 0
        for record in self.processes.values():
            if record.status == "Активна":
                delta = random.randint(-3, 4)
                if record.pid == self.desktop_pid:
                    record.cpu = 4
                else:
                    record.cpu = max(0, min(40, record.cpu + delta))
                total += record.cpu
            elif record.status == "Приостановлена":
                record.cpu = 0  # Приостановленные процессы не потребляют CPU

        # Обновляем CPU usage только от активных процессов
        active_total = sum(r.cpu for r in self.processes.values() if r.status == "Активна")
        self.cpu_usage = min(100, active_total)
        self.refresh_views()
        self.root.after(1200, self._tick_cpu)

    def shutdown(self) -> None:
        self.log("Сеанс VVU-DeskShell завершён.")
        self.root.after(150, self.root.destroy)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DeskShellApp().run()