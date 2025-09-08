#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tkinter 多按钮计数器
功能：
1) 点击按钮自增/自减计数；
2) 可新增按钮；
3) 可重命名按钮；
4) 可删除按钮；
5) （可选）自动保存与加载上次的按钮/计数状态到本地 JSON 文件。

依赖：仅标准库（tkinter）。
运行：python counter_buttons.py
"""

import json
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog

SAVE_FILE = "button_counter_state.json"

class ButtonRow:
    """封装单个“按钮 + 操作”行。"""
    def __init__(self, master, name: str, count: int, on_change):
        self.master = master
        self.name = name
        self.count = count
        self.on_change = on_change  # 回调：任何变更时通知 App 持久化/刷新

        self.frame = ttk.Frame(master)
        self.frame.columnconfigure(0, weight=1)

        # 主计数按钮：显示 名称: 计数
        self.btn = ttk.Button(self.frame, text=self._label_text(), command=self.increment)
        self.btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        # ADDED: 减一按钮
        self.decrement_btn = ttk.Button(self.frame, width=4, text="-1", command=self.decrement)
        self.decrement_btn.grid(row=0, column=1, padx=(0, 4))

        # 重命名
        # CHANGED: width 从 6 改为 4，column 从 1 改为 2
        self.rename_btn = ttk.Button(self.frame, width=4, text="重命名", command=self.rename)
        self.rename_btn.grid(row=0, column=2, padx=(0, 4))

        # 清零
        # CHANGED: width 从 6 改为 4，column 从 2 改为 3
        self.reset_btn = ttk.Button(self.frame, width=4, text="清零", command=self.reset)
        self.reset_btn.grid(row=0, column=3, padx=(0, 4))

        # 删除
        # CHANGED: width 从 6 改为 4，column 从 3 改为 4
        self.del_btn = ttk.Button(self.frame, width=4, text="删除", command=self.delete)
        self.del_btn.grid(row=0, column=4)

    def _label_text(self):
        return f"{self.name}: {self.count}"

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def destroy(self):
        self.frame.destroy()

    # --- 行为 ---
    def increment(self):
        self.count += 1
        self.btn.config(text=self._label_text())
        self.on_change()
        
    # ADDED: 减一方法
    def decrement(self):
        self.count -= 1
        self.btn.config(text=self._label_text())
        self.on_change()

    def rename(self):
        new_name = simpledialog.askstring("重命名按钮", "输入新的名称：", initialvalue=self.name, parent=self.master.winfo_toplevel())
        if new_name:
            self.name = new_name.strip()
            self.btn.config(text=self._label_text())
            self.on_change()

    def reset(self):
        if messagebox.askyesno("清零确认", f"确定要将“{self.name}”的计数清零吗？"):
            self.count = 0
            self.btn.config(text=self._label_text())
            self.on_change()

    def delete(self):
        if messagebox.askyesno("删除确认", f"确定要删除按钮“{self.name}”吗？"):
            # 通知外部先移除管理，再销毁自身
            self.on_change(action="delete", row=self)

    # --- 序列化 ---
    def to_dict(self):
        return {"name": self.name, "count": self.count}


class ScrollableFrame(ttk.Frame):
    """可滚动容器，用于容纳大量 ButtonRow。"""
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 支持鼠标滚轮
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        # Windows 正向为 -1，macOS/Linux 可能不同；这里做简单处理
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("多按钮计数器")
        self.geometry("520x560")

        # 统一 ttk 风格
        try:
            self.style = ttk.Style()
            if "clam" in self.style.theme_names():
                self.style.theme_use("clam")
        except Exception:
            pass

        # 顶部工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(side="top", fill="x", padx=12, pady=10)

        add_btn = ttk.Button(toolbar, text="➕ 新增按钮", command=self.add_button_dialog)
        add_btn.pack(side="left")

        save_btn = ttk.Button(toolbar, text="💾 另存为…", command=self.save_as)
        save_btn.pack(side="right", padx=(6, 0))

        load_btn = ttk.Button(toolbar, text="📂 打开…", command=self.load_from_file)
        load_btn.pack(side="right")

        # 中部：可滚动按钮区
        self.scroll = ScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.rows: list[ButtonRow] = []

        # 底部状态栏
        self.status = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self, textvariable=self.status, anchor="w")
        status_bar.pack(side="bottom", fill="x")

        # 启动时尝试加载上次状态
        self._current_save_path = SAVE_FILE
        self.load_state_if_exists()

        # 关闭前自动保存
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # --- 状态持久化 ---
    def load_state_if_exists(self):
        if os.path.exists(self._current_save_path):
            try:
                with open(self._current_save_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.from_dict(data)
                self.set_status(f"已从 {self._current_save_path} 加载 {len(self.rows)} 个按钮")
            except Exception as e:
                messagebox.showwarning("加载失败", f"读取 {self._current_save_path} 失败：{e}")
                self.set_status("加载失败")
        else:
            # 无保存文件时，默认给一个按钮
            self.add_button(name="按钮A", count=0)

    def save_state(self, path=None):
        path = path or self._current_save_path
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            self.set_status(f"已保存到 {path}")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def on_change(self, action=None, row: ButtonRow | None = None):
        if action == "delete" and row is not None:
            # 从管理列表移除并销毁
            try:
                idx = self.rows.index(row)
                self.rows.pop(idx)
            except ValueError:
                pass
            row.destroy()
            self.relayout()
        # 每次变更后自动保存
        self.save_state()

    def on_close(self):
        self.save_state()
        self.destroy()

    # --- 文件菜单 ---
    def save_as(self):
        path = filedialog.asksaveasfilename(
            title="另存为",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if path:
            self._current_save_path = path
            self.save_state()

    def load_from_file(self):
        path = filedialog.askopenfilename(
            title="打开配置",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if path:
            self._current_save_path = path
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.from_dict(data)
                self.save_state()  # 立即按当前保存路径写回（便于后续自动保存）
                self.set_status(f"已打开 {path}")
            except Exception as e:
                messagebox.showerror("打开失败", str(e))

    # --- 业务逻辑 ---
    def add_button_dialog(self):
        name = simpledialog.askstring("新增按钮", "输入按钮名称：", parent=self)
        if name:
            self.add_button(name.strip(), 0)
            self.save_state()

    def add_button(self, name: str, count: int = 0):
        row = ButtonRow(self.scroll.inner, name=name, count=count, on_change=self.on_change)
        self.rows.append(row)
        row.grid(row=len(self.rows)-1, column=0, sticky="ew", pady=6)
        self.relayout()

    def relayout(self):
        # 重新摆放所有行（删除后保证顺序紧凑）
        for i, r in enumerate(self.rows):
            r.frame.grid_configure(row=i)

    def set_status(self, text: str):
        self.status.set(text)

    # --- 序列化 ---
    def to_dict(self):
        return {"buttons": [r.to_dict() for r in self.rows]}

    def from_dict(self, data: dict):
        # 先清空旧的
        for r in self.rows:
            r.destroy()
        self.rows.clear()

        for item in data.get("buttons", []):
            name = item.get("name", "未命名")
            count = int(item.get("count", 0))
            self.add_button(name, count)
        self.relayout()


if __name__ == "__main__":
    App().mainloop()