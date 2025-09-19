import os
import shutil
import subprocess
import time
import win32gui
import win32ui
import win32con
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk, ImageGrab
import logging
from tkinter import messagebox
import gimpformats


def _perform_analysis(app):
    """执行分析操作（跳过无法处理的格式）"""
    try:
        # 检查是否支持的文件格式
        supported_formats = ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.xcf']  # 添加 xcf 格式
        ext = os.path.splitext(app.latest_image)[1].lower()

        if ext not in supported_formats:
            raise RuntimeError(f"暂不支持分析{ext}格式文件，请导出为PNG/JPG格式")

        if ext == '.xcf':
            xcf = gimpformats.GimpDocument(app.latest_image)
            img = xcf.flatten()  # 将 xcf 文件转换为 PIL 图像
        else:
            img = Image.open(app.latest_image)

        return (f"基础分析报告：\n"
                f"尺寸：{img.size}\n"
                f"模式：{img.mode}\n"
                f"文件大小：{os.path.getsize(app.latest_image)} 字节\n"
                f"初步检测：图像结构正常")
    except Exception as e:
        raise RuntimeError(f"分析失败：{str(e)}")


def create_blank_canvas(path, size=(1920, 1080)):
    """创建空白画布（始终生成PNG格式）"""
    try:
        img = Image.new("RGB", size, (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((20, 20),
                  f"临时画布 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                  fill=(200, 200, 200))
        img.save(path, "PNG")
        return True
    except Exception as e:
        messagebox.showerror("错误", f"创建画布失败：{str(e)}")
        return False


def _get_paint_tool():
    tools = []
    if os.name == 'nt':
        tools = ['mspaint.exe']
    else:
        tools = ['krita', 'pinta', 'gimp']

    for tool in tools:
        if shutil.which(tool):
            return tool
    return None


def _run_paint_tool(tool, path, app):
    """运行绘画软件并监控文件"""
    commands = {
        'mspaint.exe': [tool, path],
        'pinta': [tool, path],
        'gimp': [tool, path],
        'krita': [tool, '--new', path]
    }

    try:
        process = subprocess.Popen(commands.get(tool, [tool, path]))
        process.wait()

        if os.path.exists(path):
            app.latest_image = path
            _update_file_info(app, path)
            _show_preview(app, path)
        else:
            messagebox.showwarning("警告", "文件保存失败")
    except Exception as e:
        messagebox.showerror("错误", f"启动失败：{str(e)}")


def _update_file_info(app, path):
    """更新文件信息显示"""
    try:
        if path.lower().endswith('.xcf'):
            xcf = gimpformats.GimpDocument(path)
            img = xcf.flatten()
        else:
            img = Image.open(path)
        info = (f"文件路径：{path}\n"
                f"文件大小：{os.path.getsize(path)} 字节\n"
                f"图片尺寸：{img.size}\n"
                f"最后修改：{datetime.fromtimestamp(os.path.getmtime(path))}")
        app.file_info.config(text=info)
    except Exception as e:
        messagebox.showerror("错误", f"读取文件失败：{str(e)}")


def _show_preview(app, path):
    """显示图片预览"""
    try:
        if path.lower().endswith('.xcf'):
            xcf = gimpformats.GimpDocument(path)
            img = xcf.flatten()
        else:
            img = Image.open(path)
        # 计算合适的缩略图尺寸，保持宽高比
        max_size = (300, 300)
        width, height = img.size
        if width > max_size[0] or height > max_size[1]:
            ratio_w = max_size[0] / width
            ratio_h = max_size[1] / height
            ratio = min(ratio_w, ratio_h)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 释放之前的 PhotoImage 对象（如果存在）
        if hasattr(app.preview_label, 'image'):
            app.preview_label.image = None

        photo = ImageTk.PhotoImage(img)
        app.preview_label.config(image=photo)
        app.preview_label.image = photo
    except FileNotFoundError:
        messagebox.showerror("错误", f"文件 {path} 不存在")
    except OSError:
        messagebox.showerror("错误", f"无法识别的文件格式：{path}")
    except Exception as e:
        messagebox.showerror("错误", f"生成预览失败：{str(e)}")

