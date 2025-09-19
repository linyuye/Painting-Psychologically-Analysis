import threading
import tkinter as tk
from tkinter import ttk, messagebox
import json
import requests


class UserDB:
    def add_second_final_report(self, user_id, content):
        pass


class QuestionnaireWindow:
    def __init__(self, master, on_submit, user_id, analysis_id):
        self.final_answers = None
        self.master = master
        self.on_submit = on_submit
        self.user_id = user_id  # 新增用户 ID
        self.analysis_id = analysis_id  # 新增 analysis_id
        self.answers = {}
        self.current_questionnaire = 0
        self.json_files = ["data/1.json", "data/BDI.json", "data/STAY.json"]
        # self.json_files = ["data/test.json"] #用于测试
        self.questionnaire_names = ["大五人格测试", "贝克抑郁量表", "状态特质焦虑量表"]  # 问卷中文名称
        self.questionnaires = [self.load_questions(file) for file in self.json_files]
        self.db = UserDB()  # 初始化数据库对象
        self.menu_items = []  # 用于存储菜单项
        self.questionnaire_menu = None  # 保存问卷菜单的引用

        self.window = tk.Toplevel(master)
        self.window.title("心理测评问卷")
        self.window.geometry("600x400")

        self._create_menu()
        self._create_widgets()
        self.update_menu()  # 初始化菜单显示

    def load_questions(self, json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("错误: 文件未找到!")
        except json.JSONDecodeError:
            print("错误: 无法解析 JSON 文件!")
        return []

    def _create_menu(self):
        menubar = tk.Menu(self.window)
        self.questionnaire_menu = tk.Menu(menubar, tearoff=0)

        for i, name in enumerate(self.questionnaire_names):
            # 保存菜单项以便后续更新
            self.questionnaire_menu.add_command(
                label=name,
                command=lambda idx=i: self.show_questionnaire(idx)
            )

        menubar.add_cascade(label="问卷选择", menu=self.questionnaire_menu)
        self.window.config(menu=menubar)

    def update_menu(self):
        """更新菜单显示，突出显示当前选中的问卷"""
        for i in range(len(self.questionnaires)):
            # 获取问卷的基本名称
            base_name = self.questionnaire_names[i]
            
            # 为当前选中的问卷添加突出显示符号，其他的显示基本名称
            if i == self.current_questionnaire:
                display_name = f"▶ {base_name}"
            else:
                display_name = base_name
                
            # 更新菜单项标签
            self.questionnaire_menu.entryconfig(i, label=display_name)

    def show_questionnaire(self, idx):
        self.current_questionnaire = idx
        self._create_widgets()
        self.update_menu()  # 更新菜单显示

    def _create_widgets(self):
        if hasattr(self, 'notebook'):
            self.notebook.destroy()
        if hasattr(self, 'btn_frame'):
            self.btn_frame.destroy()

        self.notebook = ttk.Notebook(self.window)
        questions = self.questionnaires[self.current_questionnaire]

        # 创建一个框架用于容纳题目和滚动条
        scrollable_frame = ttk.Frame(self.notebook)
        scrollable_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 创建垂直滚动条
        scrollbar = ttk.Scrollbar(scrollable_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 创建一个画布用于承载题目
        canvas = tk.Canvas(scrollable_frame, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar.config(command=canvas.yview)

        # 创建一个内部框架用于实际放置题目
        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor=tk.NW)

        for i, question in enumerate(questions):
            page = ttk.Frame(inner_frame)
            ttk.Label(page, text=f"{i + 1}. {question['question']}").pack(pady=5)
            if isinstance(question.get("options"), list):
                self.answers.setdefault(self.current_questionnaire, {})[f"q{i + 1}"] = tk.StringVar()
                for opt in question["options"]:
                    if isinstance(opt, dict):
                        ttk.Radiobutton(page, text=f"{opt['option']}. {opt['description']}",
                                        variable=self.answers[self.current_questionnaire][f"q{i + 1}"],
                                        value=opt['option']).pack(anchor=tk.W)
                    else:
                        print(f"Unexpected option format: {opt}")
            elif question.get("type") == "text":
                self.answers.setdefault(self.current_questionnaire, {})[f"q{i + 1}"] = tk.Text(page, height=8, width=50,
                                                                                               highlightbackground="gray",
                                                                                               highlightthickness=1)
                self.answers[self.current_questionnaire][f"q{i + 1}"].pack(padx=10, pady=5)
            elif question.get("type") == "checkbox":
                self.answers.setdefault(self.current_questionnaire, {})[f"q{i + 1}"] = []
                for opt in question["options"]:
                    var = tk.IntVar()
                    ttk.Checkbutton(page, text=opt, variable=var).pack(anchor=tk.W)
                    self.answers[self.current_questionnaire][f"q{i + 1}"].append(var)
            page.pack(fill=tk.BOTH, expand=True)

        # 更新画布的滚动区域
        inner_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.notebook.add(scrollable_frame, text=self.questionnaire_names[self.current_questionnaire])
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 控制按钮
        self.btn_frame = ttk.Frame(self.window)
        # 上一题下一题的按钮，由于采用了滑轮，故废除
        # ttk.Button(self.btn_frame, text="上一题", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        # ttk.Button(self.btn_frame, text="下一题", command=self.next_page).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="跳到上一个问卷", command=self.behind_questionnaire).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="跳到下一个问卷", command=self.next_questionnaire).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.btn_frame, text="提交", command=self.submit).pack(side=tk.RIGHT, padx=5)
        self.btn_frame.pack(pady=10)

    def prev_page(self):
        if self.notebook.index("current") > 0:
            self.notebook.select(self.notebook.index("current") - 1)

    def next_page(self):
        if self.notebook.index("current") < len(self.questionnaires[self.current_questionnaire]) - 1:
            self.notebook.select(self.notebook.index("current") + 1)

    def next_questionnaire(self):
        if self.current_questionnaire < len(self.questionnaires) - 1:
            self.current_questionnaire += 1
            self._create_widgets()
            self.update_menu()  # 更新菜单显示

    def behind_questionnaire(self):
        if self.current_questionnaire > 0:
            self.current_questionnaire -= 1
            self._create_widgets()
            self.update_menu()  # 更新菜单显示

    def submit(self):
        # 收集答案和未回答的题目
        final_answers = {}
        unanswered_questions = []  # 记录未回答的题目
        
        for q_idx, questions in enumerate(self.questionnaires):
            final_answers[q_idx] = {}
            questionnaire_name = self.questionnaire_names[q_idx]
            
            # 确保答案字典已初始化
            if q_idx not in self.answers:
                self.answers[q_idx] = {}
            
            for i in range(len(questions)):
                question = questions[i]["question"]
                question_key = f"q{i + 1}"
                
                if isinstance(questions[i].get("options"), list):
                    if question_key not in self.answers[q_idx] or not self.answers[q_idx][question_key].get():
                        unanswered_questions.append(f"{questionnaire_name} - 问题 {i + 1}: {question}")
                    else:
                        selected_option = self.answers[q_idx][question_key].get()
                        for opt in questions[i]["options"]:
                            if opt["option"] == selected_option:
                                final_answers[q_idx][question] = {
                                    "option": selected_option,
                                    "description": opt["description"],
                                    "score": opt["score"]
                                }
                                break
                elif questions[i].get("type") == "text":
                    if question_key not in self.answers[q_idx]:
                        unanswered_questions.append(f"{questionnaire_name} - 问题 {i + 1}: {question}")
                    else:
                        answer = self.answers[q_idx][question_key].get("1.0", tk.END).strip()
                        if not answer:
                            unanswered_questions.append(f"{questionnaire_name} - 问题 {i + 1}: {question}")
                        else:
                            final_answers[q_idx][question] = answer
                elif questions[i].get("type") == "checkbox":
                    if question_key not in self.answers[q_idx]:
                        unanswered_questions.append(f"{questionnaire_name} - 问题 {i + 1}: {question}")
                    else:
                        selected_options = []
                        for j, var in enumerate(self.answers[q_idx][question_key]):
                            if var.get() == 1:
                                selected_options.append(questions[i]["options"][j])
                        if not selected_options:
                            unanswered_questions.append(f"{questionnaire_name} - 问题 {i + 1}: {question}")
                        else:
                            final_answers[q_idx][question] = selected_options
        
        # 如果有未回答的题目，询问用户是否要继续提交
        if unanswered_questions:
            unanswered_text = "\n".join(unanswered_questions[:10])  # 最多显示10个未回答的题目
            if len(unanswered_questions) > 10:
                unanswered_text += f"\n... 还有{len(unanswered_questions) - 10}个未回答的题目"
            
            message = f"检测到以下题目未回答：\n\n{unanswered_text}\n\n是否要继续提交问卷？\n（点击\"是\"将提交已回答的部分，点击\"否\"返回继续填写）"
            
            result = messagebox.askyesno("提醒", message)
            if not result:  # 用户选择不提交
                return
        
        # print("提交的答案：", final_answers)
        self.handle_submit(final_answers)
        self.final_answers = final_answers
        self.on_submit(final_answers)
        self.window.destroy()

    def handle_submit(self, final_answers):
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
                report = self.generate_report(final_answers)
                if report:
                    # report 现在直接是字符串内容，不需要再解析
                    messagebox.showinfo("生成的报告", report)
                    print(report)
                    self.db.add_second_final_report(self.user_id, report)  # 保存报告到数据库
                else:
                    messagebox.showerror("错误", "无法生成报告")
                hide_loading(loading_window)
                self.window.destroy()
            except Exception as e:
                hide_loading(loading_window)
                messagebox.showerror("错误", str(e))
                self.window.destroy()

        threading.Thread(target=generate_report_async, daemon=True).start()

    def generate_report(self, final_answers):
        print("提交的答案：", final_answers)
        app_id = "af332bbb-5283-4bf2-9170-e506edf50ca5"
        with open('token.txt', 'r') as file:
            token = file.read().strip() 
        url = "https://qianfan.baidubce.com/v2/app/conversation"
        
        payload = json.dumps({
            "app_id": app_id,
        }, ensure_ascii=False)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))
        
        conversation_id = response.json().get("conversation_id")
        print("Conversation ID:", conversation_id)

        # ------------------发送消息------------------
        url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
        
        payload = {
            "app_id": app_id,
            "query": f"这是我的问卷,是用json格式发送的，请帮我分析一下我的心理状态：{str(final_answers)}，你在返回的时候不要使用markdown格式，也不要使用代码块，只需要返回纯文本就行了。",
            "conversation_id": conversation_id,
            "stream": False,
        }
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=json.dumps(payload).encode("utf-8"))

        return response.json().get("answer")