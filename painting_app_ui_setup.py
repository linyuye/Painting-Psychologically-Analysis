import tkinter as tk
from tkinter import ttk

from painting_app_file_handling import _load_history, start_painting
from painting_app_status_indicator import StatusIndicator


def _setup_ui(app):
    app.master.title(f"绘画心理智慧分析平台 - {app.username}")
    app.master.geometry("800x600")
    # 历史记录面板
    history_frame = ttk.LabelFrame(app.master, text="历史分析报告")
    scrollbar = tk.Scrollbar(history_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    app.history_text = tk.Text(history_frame, height=8, yscrollcommand=scrollbar.set, state=tk.DISABLED)
    app.history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    scrollbar.config(command=app.history_text.yview)
    history_frame.pack(fill=tk.BOTH, padx=10, pady=5)

    # 文件信息面板
    info_frame = ttk.LabelFrame(app.master, text="文件信息")
    app.file_info = tk.Label(info_frame, text="当前没有打开的文件", justify=tk.LEFT)
    app.file_info.pack(fill=tk.BOTH, padx=10, pady=5)
    info_frame.pack(fill=tk.BOTH, padx=10, pady=5)

    # 控制按钮
    btn_frame = ttk.Frame(app.master)
    ttk.Button(btn_frame, text="开始绘画", command=lambda: start_painting(app)).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="开始答题", command=app.analyze_latest).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="刷新历史", command=lambda: _load_history(app)).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="生成心理分析报告", command=app.analyze_psychology).pack(side=tk.LEFT, padx=5)
    btn_frame.pack(pady=10)

    # 预览面板
    app.preview_label = tk.Label(app.master)
    app.preview_label.pack(pady=10)


def _setup_status_indicator(app):
    status_frame = ttk.LabelFrame(app.master, text="分析进度")
    app.status_indicator = StatusIndicator(status_frame,
                                           ["等待绘画", "问卷填写", "问卷报告", "绘画报告"])
    app.status_indicator.pack(pady=5)
    status_frame.pack(fill=tk.X, padx=10, pady=5)

