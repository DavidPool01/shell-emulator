#!/usr/bin/env python3
"""Эмулятор оболочки ОС — Этап 1 (REPL)."""

import os
import socket
import tkinter as tk
from tkinter import scrolledtext
from typing import List, Tuple


def get_prompt_info() -> str:
    """Формирует строку username@hostname на основе реальных данных ОС."""
    username = os.getenv("USER") or os.getenv("USERNAME") or "user"
    hostname = socket.gethostname()
    return f"{username}@{hostname}"


class ShellEmulator:
    """Простейший GUI-эмулятор командной оболочки."""

    def __init__(self) -> None:
        """Создаёт главное окно, область вывода и строку ввода."""
        self.root = tk.Tk()
        self.username_host = get_prompt_info()
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
            text=f"{self.username_host}:~$ ",
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

        self.write_output(
            "Эмулятор оболочки (Этап 1. REPL)\n"
            f"Пользователь: {self.username_host}\n"
            "Доступные команды: ls, cd, exit\n"
            f"{'-' * 50}\n"
        )

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

    def execute(self, command: str, args: List[str]) -> None:
        """Выполняет команду. На данном этапе ls и cd — заглушки."""
        if not command:
            return

        if command == "exit":
            self.write_output("Выход из эмулятора...\n")
            self.root.after(300, self.root.destroy)
            return

        if command == "ls":
            self.write_output(f"ls {' '.join(args)}\n")
            return

        if command == "cd":
            self.write_output(f"cd {' '.join(args)}\n")
            return

        self.write_output(f"Ошибка: неизвестная команда '{command}'\n")

    def on_enter(self, event=None) -> None:
        """Обработчик нажатия Enter. Читает ввод, разбирает и выполняет команду."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)

        self.write_output(f"{self.username_host}:~$ {line}\n")

        try:
            command, args = self.parse_command(line)
            self.execute(command, args)
        except ValueError as e:
            self.write_output(f"Ошибка: {e}\n")

    def run(self) -> None:
        """Запускает главный цикл обработки событий GUI."""
        self.root.mainloop()


def main() -> None:
    """Точка входа в программу. Создаёт и запускает эмулятор."""
    app = ShellEmulator()
    app.run()


if __name__ == "__main__":
    main()