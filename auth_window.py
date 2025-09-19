import tkinter as tk
from tkinter import ttk, messagebox


class AuthWindow:
    def __init__(self, master, db, on_success):
        self.master = master
        self.db = db
        self.on_success = on_success

        self.window = tk.Toplevel(master)
        self.window.title("用户认证")
        self.window.geometry("300x200")
        self._create_widgets()

    def _create_widgets(self):
        self.notebook = ttk.Notebook(self.window)

        # 登录页面
        self.login_frame = ttk.Frame(self.notebook)
        self._build_auth_form(self.login_frame, "登录", "login")
        self.notebook.add(self.login_frame, text="登录")

        # 注册页面
        self.register_frame = ttk.Frame(self.notebook)
        self._build_auth_form(self.register_frame, "注册", "register")
        self.notebook.add(self.register_frame, text="注册")

        self.notebook.pack(expand=True, fill="both")

    def _build_auth_form(self, frame, title, mode):
        ttk.Label(frame, text=title, font=('Arial', 14)).pack(pady=5)

        # 输入框容器
        form_frame = ttk.Frame(frame)

        # 用户名输入
        ttk.Label(form_frame, text="用户名:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        username_entry = ttk.Entry(form_frame)
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        # 密码输入
        ttk.Label(form_frame, text="密码:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        password_entry = ttk.Entry(form_frame, show="*")
        password_entry.grid(row=1, column=1, padx=5, pady=5)

        form_frame.pack(pady=10)

        # 按钮和输入框绑定
        if mode == "login":
            self.login_username = username_entry  # 修复1：明确绑定登录用输入框
            self.login_password = password_entry
            ttk.Button(frame,
                       text="登录",
                       command=self.login).pack(pady=5)
        else:
            self.register_username = username_entry  # 修复2：明确绑定注册用输入框
            self.register_password = password_entry
            ttk.Button(frame,
                       text="注册",
                       command=self.register).pack(pady=5)

    def login(self):
        # 修复3：直接使用绑定的输入框组件
        username = self.login_username.get().strip()
        password = self.login_password.get().strip()

        print(f"[DEBUG] 登录尝试 - 用户名: {username}, 密码: {password}")  # 调试输出

        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空")
            return

        user_id = self.db.verify_user(username, password)
        if user_id:
            print(f"[DEBUG] 登录成功 - 用户ID: {user_id}")  # 调试输出
            self.on_success(username, user_id)
            self.window.destroy()
        else:
            messagebox.showerror("错误", "用户名或密码错误")

    def register(self):
        # 修复4：使用正确的注册输入框
        username = self.register_username.get().strip()
        password = self.register_password.get().strip()

        print(f"[DEBUG] 注册尝试 - 用户名: {username}")  # 调试输出

        if len(username) < 4 or len(password) < 6:
            messagebox.showerror("错误", "用户名至少4位，密码至少6位")
            return

        if self.db.create_user(username, password):
            messagebox.showinfo("成功", "注册成功，请登录")
            self.notebook.select(0)
            # 修复5：清空注册输入框
            self.register_username.delete(0, tk.END)
            self.register_password.delete(0, tk.END)
        else:
            messagebox.showerror("错误", "用户名已存在")
