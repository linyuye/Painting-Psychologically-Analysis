import os
import shutil
import subprocess
import sys
import threading
import time
import win32gui
import win32ui
import win32con
from datetime import datetime
from PIL import Image, ImageGrab
import logging
from tkinter import messagebox
import tkinter as tk

from painting_app_analysis import create_blank_canvas, _get_paint_tool, _update_file_info, _show_preview


def _init_save_dir():
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe文件
        base_path = os.path.dirname(sys.executable)
    else:
        # 如果是脚本运行
        base_path = os.path.dirname(__file__)
    save_path = os.path.join(base_path, 'save_images')
    os.makedirs(save_path, exist_ok=True)
    return save_path


def _load_history(app):
    history = app.db.get_user_history(app.user_id)  # 修正为传入 user_id
    app.history_text.config(state=tk.NORMAL)
    app.history_text.delete(1.0, tk.END)

    if history:
        for index, (analysis_time, file_path, analysis_result, final_report) in enumerate(history, start=1):
            try:
                time_str = datetime.fromisoformat(analysis_time).strftime("%Y-%m-%d %H:%M:%S")
                record = f"{index}. 分析时间：{time_str}\n" \
                         f"文件路径：{file_path}\n" \
                         f"分析结果：\n{analysis_result}\n"
                if final_report:
                    record += f"最终报告：\n{final_report}\n"
                record += f"------------------------\n"
                app.history_text.insert(tk.END, record)
            except ValueError:
                app.history_text.insert(tk.END, f"{index}. 无法解析分析时间\n")
    else:
        app.history_text.insert(tk.END, "暂无历史记录")
    app.history_text.config(state=tk.DISABLED)


def auto_save_progress(original_path, backup_dir):
    """智能自动保存核心逻辑"""
    try:
        version = 1
        last_change = time.time()

        while True:
            # 方案1：通过文件变化检测（兼容大部分软件）
            if os.path.exists(original_path):
                current_mtime = os.path.getmtime(original_path)
                if current_mtime > last_change:
                    _create_version(original_path, backup_dir, version)
                    version += 1
                    last_change = current_mtime

            # 方案2：通过屏幕截图捕获（备用方案）
            screenshot_path = os.path.join(backup_dir, f"screenshot_{int(time.time())}.png")
            _capture_active_window(screenshot_path)

            time.sleep(5)  # 每5s自动保存一次

    except Exception as e:
        logging.error(f"自动保存异常: {str(e)}")


def _create_version(file_path, backup_dir, version):
    """创建版本备份"""
    try:
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        version_file = f"{name}_auto_{version:03d}{ext}"
        version_path = os.path.join(backup_dir, version_file)

        shutil.copy2(file_path, version_path)
        logging.info(f"自动保存版本: {version_path}")
    except Exception as e:
        logging.error(f"版本创建失败: {str(e)}")


def _capture_active_window(save_path,app):
    """截图备用方案"""
    try:
        if app.painting_hwnd:
            rect = win32gui.GetWindowRect(app.painting_hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            hdesktop = win32gui.GetDesktopWindow()
            hwndDC = win32gui.GetWindowDC(hdesktop)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            saveDC.BitBlt((0, 0), (width, height), mfcDC, (rect[0], rect[1]), win32con.SRCCOPY)

            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = Image.frombuffer(
                "RGB",
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, "raw", "BGRX", 0, 1
            )
            img.save(save_path)
            logging.info(f"截图保存: {save_path}")
        else:
            logging.error("未找到绘画软件窗口句柄")

    except Exception as e:
        logging.error(f"截图失败: {str(e)}")
        # 使用PIL的备用截图方案
        try:
            img = ImageGrab.grab()
            img.save(save_path)
            logging.info(f"全屏截图保存: {save_path}")
        except Exception as e:
            logging.error(f"全屏截图失败: {str(e)}")


def start_painting(app):
    """启动绘画流程（支持静默自动备份）"""

    def painting_task():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{app.username}_{timestamp}"

        # 创建临时画布文件（PNG格式）
        temp_path = os.path.join(app.save_dir, f"{base_name}_temp.png")
        if not create_blank_canvas(temp_path):
            return

        # 启动绘画软件
        tool = _get_paint_tool()
        if tool:
            try:
                process = subprocess.Popen([tool, temp_path])

                # 等待绘画软件窗口出现并获取句柄
                time.sleep(2)  # 等待窗口启动

                def enum_windows_callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd)
                        if temp_path in window_text:
                            app.painting_hwnd = hwnd
                            return False
                    return True

                win32gui.EnumWindows(enum_windows_callback, None)

                # 初始化监控参数
                initial_mtime = os.path.getmtime(temp_path)
                initial_size = os.path.getsize(temp_path)
                backup_dir = os.path.join(app.save_dir, f"{base_name}_versions")
                os.makedirs(backup_dir, exist_ok=True)

                # 启动静默监控线程
                monitor_thread = threading.Thread(
                    target=monitor_file_changes,
                    args=(temp_path, backup_dir, process, initial_mtime, initial_size),
                    daemon=True
                )
                monitor_thread.start()

                process.wait()

                autosave_thread = threading.Thread(
                    target=auto_save_progress,
                    args=(temp_path, backup_dir),
                    daemon=True
                )
                autosave_thread.start()

                # 检测最终保存的文件（静默操作）
                final_path = _detect_saved_file(base_name, temp_path)
                if final_path:
                    app.latest_image = final_path
                    _update_file_info(app, final_path)
                    _show_preview(app, final_path)
                    app.status_indicator.update_status(1)

            except Exception as e:
                logging.error(f"绘画流程异常: {str(e)}")
                messagebox.showerror("错误", f"启动失败：{str(e)}")

    threading.Thread(target=painting_task, daemon=True).start()


def monitor_file_changes(file_path, backup_dir, process, initial_mtime, initial_size):
    """静默监控文件变化并自动备份（10秒间隔）"""
    version = 1
    last_mtime = initial_mtime
    last_size = initial_size

    try:
        while process.poll() is None:  # 仅在进程运行时监控
            current_mtime = os.path.getmtime(file_path)
            current_size = os.path.getsize(file_path)

            # 检测到有效变化（文件大小变化超过1KB或内容修改）
            if (current_mtime != last_mtime) and (abs(current_size - last_size) > 10):
                # 生成版本文件名
                filename = os.path.basename(file_path)
                name, ext = os.path.splitext(filename)
                version_file = f"{name}_v{version:03d}{ext}"
                version_path = os.path.join(backup_dir, version_file)

                # 静默复制文件
                try:
                    shutil.copy2(file_path, version_path)
                    logging.info(f"自动备份版本: {version_path}")
                    version += 1
                    last_mtime = current_mtime
                    last_size = current_size
                except Exception as copy_error:
                    logging.error(f"备份失败: {str(copy_error)}")

            time.sleep(1)

        # 进程结束后处理最终版本
        _save_final_version(file_path, backup_dir, version)

    except Exception as e:
        logging.error(f"监控异常中断: {str(e)}")


def _save_final_version(file_path, backup_dir, version):
    """保存最终版本且不提示"""
    try:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            version_file = f"{name}_v{version:03d}{ext}"
            version_path = os.path.join(backup_dir, version_file)
            shutil.copy2(file_path, version_path)
            logging.info(f"保存最终版本: {version_path}")
    except Exception as e:
        logging.error(f"最终版本保存失败: {str(e)}")


def _detect_saved_file(base_name, temp_path):
    """检测实际保存的文件（支持多格式）"""
    # 可能的后缀列表（根据常见绘图软件扩展名）
    possible_ext = [
        '.png', '.jpg', '.jpeg',  # 常见图片格式
        '.xcf',  # GIMP原生格式
        '.kra',  # Krita格式
        '.ora',  # OpenRaster格式
        '.psd',  # Photoshop格式
        '.tif', '.tiff'  # TIFF格式
    ]

    # 查找同名不同后缀的文件
    save_dir = os.path.dirname(temp_path)
    dir_files = os.listdir(save_dir)
    matching_files = [
        f for f in dir_files
        if f.startswith(base_name) and
           os.path.splitext(f)[1].lower() in possible_ext
    ]

    # 按修改时间排序
    if matching_files:
        latest_file = max(
            matching_files,
            key=lambda f: os.path.getmtime(os.path.join(save_dir, f))
        )
        return os.path.join(save_dir, latest_file)

    # 如果没有找到其他文件，检查临时文件是否被修改
    if os.path.exists(temp_path):
        return temp_path

    return None

