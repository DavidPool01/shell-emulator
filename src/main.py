#!/usr/bin/env python3
"""Эмулятор оболочки ОС — Этап 2 (Конфигурация)."""

import argparse
import os
import socket
import sys
import tkinter as tk
from tkinter import scrolledtext
from typing import List, Tuple, Optional


def get_prompt_info() -> str:
    """Формирует строку username@hostname на основе реальных данных ОС."""
    username = os.getenv("USER") or os.getenv("USERNAME") or "user"
    hostname = socket.gethostname()
    return f"{username}@{hostname}"


class ShellEmulator:
    """GUI-эмулятор командной оболочки с поддержкой конфигурации."""

    def __init__(
        self,
        vfs_path: Optional[str] = None,
        prompt: Optional[str] = None,
        script_path: Optional[str] = None,
    ) -> None:
        """Создаёт главное окно и сохраняет параметры конфигурации."""
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.username_host = get_prompt_info()

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
            "Эмулятор оболочки (Этап 2. Конфигурация)\n"
            f"Пользователь: {self.username_host}\n"
            "Доступные команды: ls, cd, exit, conf-dump\n"
            f"{'-' * 50}\n"
        )

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
        command = parts[0]
        args = parts[1:]
        return command, args

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
            return True

        self.write_output(f"Ошибка: неизвестная команда '{command}'\n")
        return False

    def on_enter(self, event=None) -> None:
        """Обработчик нажатия Enter. Читает ввод, разбирает и выполняет команду."""
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
        """Запускает главный цикл обработки событий GUI."""
        self.root.mainloop()


def parse_args() -> argparse.Namespace:
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="Эмулятор оболочки ОС")
    parser.add_argument("--vfs", type=str, default=None, help="Путь к физическому расположению VFS")
    parser.add_argument("--prompt", type=str, default=None, help="Пользовательское приглашение к вводу")
    parser.add_argument("--script", type=str, default=None, help="Путь к стартовому скрипту")
    return parser.parse_args()


def main() -> None:
    """Точка входа в программу. Создаёт и запускает эмулятор."""
    args = parse_args()
    app = ShellEmulator(
        vfs_path=args.vfs,
        prompt=args.prompt,
        script_path=args.script,
    )
    app.run()


if __name__ == "__main__":
    main()