import os
import shutil
import logging
import gimpformats
from tkinter import messagebox


def _on_file_change(app, event):
    """修改后的静默备份方法"""
    if event.is_directory:
        return
    if event.event_type in ['modified', 'created']:
        file_path = event.src_path
        base_name, ext = os.path.splitext(file_path)
        save_folder = f"{base_name}_1"
        os.makedirs(save_folder, exist_ok=True)
        new_file_path = os.path.join(save_folder, os.path.basename(file_path))
        try:
            if ext.lower() == '.xcf':
                xcf = gimpformats.GimpDocument(file_path)
                img = xcf.flatten()
                img.save(new_file_path, "PNG")
            else:
                shutil.copy2(file_path, new_file_path)
            logging.info(f"自动备份文件到: {new_file_path}")  # 使用日志代替弹窗
            print(f"自动备份文件到: {new_file_path}")
        except Exception as e:
            logging.error(f"备份失败: {str(e)}")  # 使用日志代替弹窗
            print(f"备份失败: {str(e)}")


def on_close(app):
    # 停止文件监控
    app.observer.stop()
    app.observer.join()
    # 关闭主窗口
    app.master.destroy()

