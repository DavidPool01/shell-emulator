#!/usr/bin/env python3
"""Эмулятор оболочки ОС — Этап 3 (VFS)."""

import argparse
import base64
import csv
import os
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
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    raise ValueError("пустой CSV-файл")

                fieldnames = [name.strip().lstrip("\ufeff") for name in reader.fieldnames]

                if "path" not in fieldnames or "type" not in fieldnames:
                    raise ValueError(f"неверный формат CSV: нужны столбцы path и type, сейчас: {fieldnames}")

                for row in reader:
                    clean_row = {
                        k.strip().lstrip("\ufeff"): (v or "").strip()
                        for k, v in row.items()
                    }

                    node_path = clean_row.get("path", "").strip()
                    node_type = clean_row.get("type", "").strip().lower()
                    content_raw = clean_row.get("content", "")

                    if not node_path or node_path == "/":
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
                                    current.children[part] = VFSNode(
                                        part, is_dir=False, content=content
                                    )
                            else:
                                current.children[part] = VFSNode(part, is_dir=True)

                        current = current.children[part]

            self.loaded = True

        except FileNotFoundError:
            raise
        except Exception as e:
            raise ValueError(str(e))


class ShellEmulator:
    """GUI-эмулятор командной оболочки с поддержкой VFS."""

    def __init__(
        self,
        vfs_path: Optional[str] = None,
        prompt: Optional[str] = None,
        script_path: Optional[str] = None,
    ) -> None:
        """Создаёт главное окно и загружает конфигурацию + VFS."""
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.username_host = get_prompt_info()
        self.vfs = VFS()

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
            "Эмулятор оболочки (Этап 3. VFS)\n"
            f"Пользователь: {self.username_host}\n"
            "Доступные команды: ls, cd, exit, conf-dump\n"
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
        """Выводит переданный текст в область вывода эмулятора."""
        self.output.configure(state="normal")
        self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def parse_command(self, line: str) -> Tuple[str, List[str]]:
        """Разбирает строку на команду и аргументы. Проверяет незакрытые кавычки."""
        if line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
            raise ValueError("незакрытые кавычки")

        parts = line.strip().split()
        if not parts:
            return "", []
        return parts[0], parts[1:]

    def execute(self, command: str, args: List[str]) -> bool:
        """Выполняет команду. Возвращает True при успехе, False при ошибке."""
        if not command:
            return True

        if command == "exit":
            self.write_output("Выход из эмулятора...\n")
            self.root.after(300, self.root.destroy)
            return True

        if command == "ls":
            self.write_output(f"ls {' '.join(args)}\n")
            return True

        if command == "cd":
            self.write_output(f"cd {' '.join(args)}\n")
            return True

        if command == "conf-dump":
            self.write_output(f"vfs_path={self.vfs_path}\n")
            self.write_output(f"prompt={self.prompt}\n")
            self.write_output(f"script_path={self.script_path}\n")
            self.write_output(f"vfs_loaded={self.vfs.loaded}\n")
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