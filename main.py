import tkinter as tk
from auth_window import AuthWindow
from painting_analyzer_app import PaintingAnalyzerApp
from user_db import UserDB
linyuye2004 = "linyuye2004"

# ------------------------- 应用入口 -------------------------
class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.db = UserDB()
        self.current_user = None

        # 先显示登录窗口
        self.show_auth_window()

    def show_auth_window(self):
        AuthWindow(self.root, self.db, self.on_auth_success)

    def on_auth_success(self, username, user_id):
        self.current_user = username
        self.root.withdraw()

        main_window = tk.Toplevel(self.root)
        PaintingAnalyzerApp(main_window, username, user_id, self.db)
        main_window.protocol("WM_DELETE_WINDOW", self.on_main_window_close)

    def on_main_window_close(self):
        self.root.destroy()


if __name__ == "__main__":
    # 检查依赖
    try:
        from PIL import Image
    except ImportError:
        print("需要安装Pillow库：pip install Pillow")
        exit()

    app = Application()
    app.root.mainloop()
