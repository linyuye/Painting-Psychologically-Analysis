import tkinter as tk
from tkinter import ttk


class StatusIndicator(ttk.Frame):
    def __init__(self, master, steps):
        super().__init__(master)
        self.steps = steps
        self.current_step = 0
        self._create_widgets()
        self.update_status(0)

    def _create_widgets(self):
        self.canvases = []
        self.labels = []

        for i, step in enumerate(self.steps):
            frame = ttk.Frame(self)
            # 状态灯
            canvas = tk.Canvas(frame, width=20, height=20, bd=0, highlightthickness=0)
            canvas.create_oval(2, 2, 18, 18, fill="gray", tags="status")
            canvas.pack(side=tk.LEFT, padx=2)
            # 状态文字
            label = ttk.Label(frame, text=step)
            label.pack(side=tk.LEFT, padx=2)
            frame.pack(side=tk.LEFT, padx=10)
            self.canvases.append(canvas)
            self.labels.append(label)

    def update_status(self, step_index):
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            for i, canvas in enumerate(self.canvases):
                color = "gray"
                if i == step_index:
                    color = "yellow"
                elif i < step_index:
                    color = "green"
                canvas.itemconfig("status", fill=color)

