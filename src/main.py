#!/usr/bin/env python3
"""Эмулятор оболочки ОС — Этап 4 (Основные команды)."""

import argparse
import base64
import csv
import os
import platform
import socket
import tkinter as tk
from tkinter import scrolledtext
from typing import Dict, List, Optional, Tuple


def get_prompt_info() -> str:
    """Формирует строку username@hostname на основе реальных данных ОС."""
    username = os.getenv("USER") or os.getenv("USERNAME") or "user"
    hostname = socket.gethostname()
    return f"{username}@{hostname}"


class VFSNode:
    """Узел виртуальной файловой системы (файл или папка)."""

    def __init__(self, name: str, is_dir: bool = True, content: Optional[bytes] = None) -> None:
        self.name = name
        self.is_dir = is_dir
        self.content = content
        self.children: Dict[str, "VFSNode"] = {}


class VFS:
    """Виртуальная файловая система, загружаемая из CSV."""

    def __init__(self) -> None:
        self.root = VFSNode("/", is_dir=True)
        self.loaded = False
        self.source_path: Optional[str] = None

    def load_from_csv(self, path: str) -> None:
        """Загружает VFS из CSV-файла в память."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"файл VFS не найден: {path}")

        self.root = VFSNode("/", is_dir=True)
        self.source_path = path

        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames or "path" not in reader.fieldnames or "type" not in reader.fieldnames:
                    raise ValueError("неверный формат CSV: нужны столбцы path и type")

                for row in reader:
                    node_path = row["path"].strip()
                    node_type = row["type"].strip().lower()
                    content_raw = row.get("content", "") or ""

                    if node_path == "/":
                        continue

                    parts = [p for p in node_path.strip("/").split("/") if p]
                    current = self.root

                    for i, part in enumerate(parts):
                        is_last = i == len(parts) - 1
                        if part not in current.children:
                            if is_last:
                                if node_type == "dir":
                                    current.children[part] = VFSNode(part, is_dir=True)
                                else:
                                    try:
                                        content = base64.b64decode(content_raw) if content_raw else b""
                                    except Exception:
                                        content = content_raw.encode("utf-8")
                                    current.children[part] = VFSNode(part, is_dir=False, content=content)
                            else:
                                current.children[part] = VFSNode(part, is_dir=True)
                        current = current.children[part]

            self.loaded = True
        except FileNotFoundError:
            raise
        except Exception as e:
            raise ValueError(f"ошибка загрузки VFS: {e}")

    def resolve(self, path: str, cwd: str) -> Optional[VFSNode]:
        """Возвращает узел по пути (абсолютному или относительному)."""
        if not path or path == ".":
            path = cwd
        elif not path.startswith("/"):
            if cwd == "/":
                path = "/" + path
            else:
                path = cwd.rstrip("/") + "/" + path

        if path == "/":
            return self.root

        parts = [p for p in path.strip("/").split("/") if p]
        current = self.root
        for part in parts:
            if part not in current.children:
                return None
            current = current.children[part]
        return current

    def get_path_str(self, node: VFSNode, current: Optional[VFSNode] = None, path: str = "") -> Optional[str]:
        """Служебный метод (не используется напрямую)."""
        return None


class ShellEmulator:
    """GUI-эмулятор командной оболочки."""

    def __init__(
        self,
        vfs_path: Optional[str] = None,
        prompt: Optional[str] = None,
        script_path: Optional[str] = None,
    ) -> None:
        """Создаёт главное окно, загружает VFS и конфигурацию."""
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.username_host = get_prompt_info()
        self.vfs = VFS()
        self.cwd = "/"

        if prompt:
            self.prompt = prompt
        else:
            self.prompt = f"{self.username_host}:~$ "

        self.root = tk.Tk()
        self.root.title(f"Эмулятор - [{self.username_host}]")
        self.root.geometry("800x500")
        self.root.minsize(600, 400)

        self.output = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            state="disabled",
            font=("Consolas", 11),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.prompt_label = tk.Label(
            input_frame,
            text=self.prompt,
            font=("Consolas", 11),
            fg="#4ec9b0",
        )
        self.prompt_label.pack(side=tk.LEFT)

        self.entry = tk.Entry(
            input_frame,
            font=("Consolas", 11),
            bg="#252526",
            fg="white",
            insertbackground="white",
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus()

        self._print_debug_config()
        self.write_output(
            "Эмулятор оболочки (Этап 4. Основные команды)\n"
            f"Пользователь: {self.username_host}\n"
            "Доступные команды: ls, cd, tac, uname, who, conf-dump, exit\n"
            f"{'-' * 50}\n"
        )

        if self.vfs_path:
            try:
                self.vfs.load_from_csv(self.vfs_path)
                self.write_output(f"VFS успешно загружена из: {self.vfs_path}\n")
            except Exception as e:
                self.write_output(f"Ошибка загрузки VFS: {e}\n")

        if self.script_path:
            self.root.after(100, self.run_startup_script)

    def _print_debug_config(self) -> None:
        """Выводит отладочную информацию о параметрах запуска."""
        print("=== Отладочный вывод параметров ===")
        print(f"vfs_path    = {self.vfs_path}")
        print(f"prompt      = {self.prompt}")
        print(f"script_path = {self.script_path}")
        print("===================================")

    def write_output(self, text: str) -> None:
        """Выводит текст в область вывода."""
        self.output.configure(state="normal")
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def parse_command(self, line: str) -> Tuple[str, List[str]]:
        """Разбирает строку на команду и аргументы. Проверяет кавычки."""
        if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
            raise ValueError("незакрытые кавычки")

        parts = line.strip().split()
        if not parts:
            return "", []
        return parts[0], parts[1:]

    def cmd_ls(self, args: List[str]) -> bool:
        """Реализация команды ls."""
        if not self.vfs.loaded:
            self.write_output("Ошибка: VFS не загружена\n")
            return False

        path = args[0] if args else self.cwd
        node = self.vfs.resolve(path, self.cwd)

        if node is None:
            self.write_output(f"Ошибка: нет такого файла или каталога: {path}\n")
            return False

        if not node.is_dir:
            self.write_output(f"{node.name}\n")
            return True

        names = sorted(node.children.keys())
        if names:
            self.write_output("  ".join(names) + "\n")
        return True

    def cmd_cd(self, args: List[str]) -> bool:
        """Реализация команды cd."""
        if not self.vfs.loaded:
            self.write_output("Ошибка: VFS не загружена\n")
            return False

        if not args:
            self.cwd = "/"
            return True

        path = args[0]
        node = self.vfs.resolve(path, self.cwd)

        if node is None:
            self.write_output(f"Ошибка: нет такого файла или каталога: {path}\n")
            return False

        if not node.is_dir:
            self.write_output(f"Ошибка: не каталог: {path}\n")
            return False

        if path.startswith("/"):
            self.cwd = "/" + "/".join(p for p in path.strip("/").split("/") if p)
            if self.cwd != "/":
                self.cwd = self.cwd.rstrip("/") or "/"
        else:
            if self.cwd == "/":
                self.cwd = "/" + path.strip("/")
            else:
                self.cwd = self.cwd.rstrip("/") + "/" + path.strip("/")
            self.cwd = "/" + "/".join(p for p in self.cwd.strip("/").split("/") if p) or "/"

        return True

    def cmd_tac(self, args: List[str]) -> bool:
        """Реализация команды tac (вывод файла в обратном порядке)."""
        if not self.vfs.loaded:
            self.write_output("Ошибка: VFS не загружена\n")
            return False

        if not args:
            self.write_output("Ошибка: укажите имя файла\n")
            return False

        path = args[0]
        node = self.vfs.resolve(path, self.cwd)

        if node is None:
            self.write_output(f"Ошибка: нет такого файла: {path}\n")
            return False

        if node.is_dir:
            self.write_output(f"Ошибка: это каталог: {path}\n")
            return False

        try:
            text = (node.content or b"").decode("utf-8", errors="replace")
            lines = text.splitlines()
            for line in reversed(lines):
                self.write_output(line + "\n")
        except Exception as e:
            self.write_output(f"Ошибка чтения файла: {e}\n")
            return False

        return True

    def cmd_uname(self, args: List[str]) -> bool:
        """Реализация команды uname."""
        self.write_output(f"{platform.system()} {platform.release()}\n")
        return True

    def cmd_who(self, args: List[str]) -> bool:
        """Реализация команды who."""
        self.write_output(f"{self.username_host}\n")
        return True

    def execute(self, command: str, args: List[str]) -> bool:
        """Выполняет команду. Возвращает True при успехе."""
        if not command:
            return True

        if command == "exit":
            self.write_output("Выход из эмулятора...\n")
            self.root.after(300, self.root.destroy)
            return True

        if command == "ls":
            return self.cmd_ls(args)

        if command == "cd":
            return self.cmd_cd(args)

        if command == "tac":
            return self.cmd_tac(args)

        if command == "uname":
            return self.cmd_uname(args)

        if command == "who":
            return self.cmd_who(args)

        if command == "conf-dump":
            self.write_output(f"vfs_path={self.vfs_path}\n")
            self.write_output(f"prompt={self.prompt}\n")
            self.write_output(f"script_path={self.script_path}\n")
            self.write_output(f"vfs_loaded={self.vfs.loaded}\n")
            self.write_output(f"cwd={self.cwd}\n")
            return True

        self.write_output(f"Ошибка: неизвестная команда '{command}'\n")
        return False

    def on_enter(self, event=None) -> None:
        """Обработчик нажатия Enter."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.write_output(f"{self.prompt}{line}\n")

        try:
            command, args = self.parse_command(line)
            self.execute(command, args)
        except ValueError as e:
            self.write_output(f"Ошибка: {e}\n")

    def run_startup_script(self) -> None:
        """Выполняет стартовый скрипт. Останавливается при первой ошибке."""
        if not self.script_path:
            return

        if not os.path.isfile(self.script_path):
            self.write_output(f"Ошибка: файл скрипта не найден: {self.script_path}\n")
            return

        self.write_output(f"=== Выполнение стартового скрипта: {self.script_path} ===\n")

        try:
            with open(self.script_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            self.write_output(f"Ошибка чтения скрипта: {e}\n")
            return

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue

            self.write_output(f"{self.prompt}{line}\n")

            try:
                command, args = self.parse_command(line)
                success = self.execute(command, args)
                if not success:
                    self.write_output("=== Скрипт остановлен из-за ошибки ===\n")
                    return
            except ValueError as e:
                self.write_output(f"Ошибка: {e}\n")
                self.write_output("=== Скрипт остановлен из-за ошибки ===\n")
                return

        self.write_output("=== Стартовый скрипт выполнен успешно ===\n")

    def run(self) -> None:
        """Запускает главный цикл GUI."""
        self.root.mainloop()


def parse_args() -> argparse.Namespace:
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки ОС")
    parser.add_argument("--vfs", type=str, default=None, help="Путь к CSV-файлу VFS")
    parser.add_argument("--prompt", type=str, default=None, help="Пользовательское приглашение")
    parser.add_argument("--script", type=str, default=None, help="Путь к стартовому скрипту")
    return parser.parse_args()


def main() -> None:
    """Точка входа в программу."""
    args = parse_args()
    app = ShellEmulator(
        vfs_path=args.vfs,
        prompt=args.prompt,
        script_path=args.script,
    )
    app.run()


if __name__ == "__main__":
    main()