import logging
import re
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import subprocess
import shutil
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk, ImageGrab
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from questionnaire_window import QuestionnaireWindow
from psychology_report import generate_psychology_report
import time
import win32gui
import win32ui
import win32con
from painting_app_status_indicator import StatusIndicator
from painting_app_file_handling import (
    _init_save_dir,
    _load_history,
    auto_save_progress,
    _create_version,
    _capture_active_window,
    start_painting,
    monitor_file_changes,
    _save_final_version,
    _detect_saved_file
)
from painting_app_analysis import (
    _perform_analysis,
    create_blank_canvas,
    _get_paint_tool,
    _run_paint_tool,
    _update_file_info,
    _show_preview
)
from painting_app_ui_setup import _setup_ui, _setup_status_indicator
from painting_app_event_handlers import _on_file_change, on_close

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='painting_analyzer.log'
)


class PaintingAnalyzerApp:
    def __init__(self, master, username, user_id, db):
        self.status_indicator = None
        self.observer = None
        self.master = master
        self.username = username
        self.user_id = user_id
        self.db = db
        self.analysis_id = None
        self.save_dir = _init_save_dir()
        self.latest_image = None
        _setup_ui(self)
        _load_history(self)
        _setup_status_indicator(self)
        self.master.protocol("WM_DELETE_WINDOW", lambda: on_close(self))
        self.painting_hwnd = None

    def analyze_latest(self):
        if not self.latest_image:
            self._find_latest_image()

        if self.latest_image:
            self.status_indicator.update_status(1)  # 进入问卷填写状态
            # 弹出问卷窗口
            QuestionnaireWindow(self.master, self._start_analysis_with_answers, self.user_id, self.analysis_id)
        else:
            messagebox.showwarning("警告", "未找到可分析的文件")

    def _start_analysis_with_answers(self, answers):
        self.status_indicator.update_status(2)  # 进入分析完成状态

        try:
            result = _perform_analysis(self)
            # 将分析结果存入数据库
            analysis_id = self.db.add_analysis_record(
                self.user_id,
                self.latest_image,
                result,
                {"questionnaire": answers}
            )
            self.analysis_id = analysis_id  # 保存 analysis_id 为实例属性
            # 将问卷结果存入数据库
            self.db.add_questionnaire_answers(self.user_id, analysis_id, answers)
            _load_history(self)
            messagebox.showinfo("分析完成", result)
            self.status_indicator.update_status(3)  # 第三个指示灯变为黄色
        except Exception as e:
            messagebox.showerror("分析错误", str(e))
            self.status_indicator.update_status(1)  # 重置状态

    def _find_latest_image(self):
        """查找最新图片"""
        try:
            files = []
            for f in os.listdir(self.save_dir):
                if f.startswith(self.username) and f.lower().endswith(('.png', '.jpg', '.jpeg', '.xcf')):  # 添加 xcf 格式
                    files.append((f, os.path.getmtime(os.path.join(self.save_dir, f))))

            if files:
                latest = max(files, key=lambda x: x[1])[0]
                self.latest_image = os.path.join(self.save_dir, latest)
                _update_file_info(self, self.latest_image)
        except Exception as e:
            messagebox.showerror("错误", f"查找文件失败：{str(e)}")

    def analyze_psychology(self):
        if not hasattr(self, 'status_indicator'):
            print("status_indicator 属性未初始化")
            return
        if self.status_indicator.current_step < 3:
            messagebox.showwarning("警告", "未完成答题，请先完成答题流程")
            return

        def show_loading():
            loading_window = tk.Toplevel(self.master)
            loading_window.title("正在生成报告...")
            loading_window.geometry("400x300")
            loading_window.resizable(False, False)

            style = ttk.Style()
            style.theme_use('default')
            style.configure("TProgressbar", thickness=30)
            progress = ttk.Progressbar(loading_window, style="TProgressbar", mode='indeterminate')
            progress.pack(pady=20)
            progress.start()

            return loading_window

        def hide_loading(loading_window):
            loading_window.destroy()

        def generate_report_async():
            loading_window = show_loading()
            try:
                report = generate_psychology_report()
                if report:
                    print("心理分析报告:", report)
                else:
                    report = "未找到报告内容"

                hide_loading(loading_window)
                if self.analysis_id is not None:
                    self.db.add_final_report(self.analysis_id, report)
                messagebox.showinfo("心理分析报告", report)
                self.status_indicator.update_status(4)  # 第四个指示灯变为绿色
                _load_history(self)
            except Exception as e:
                hide_loading(loading_window)
                messagebox.showerror("错误", str(e))

        threading.Thread(target=generate_report_async, daemon=True).start()



class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, directory, callback):
        self.directory = directory
        self.callback = callback

    def on_modified(self, event):
        self.callback(event)

    def on_created(self, event):
        self.callback(event)