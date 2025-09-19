import sqlite3
import hashlib
import os
import sys
from datetime import datetime
import json


class UserDB:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # 如果是打包后的 exe 文件
            base_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境下的 Python 脚本
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.db_path = os.path.join(base_path, 'data', 'paint_analysis.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            # 创建用户表
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')

            # 创建分析记录表
            conn.execute('''CREATE TABLE IF NOT EXISTS analysis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        analysis_time TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        analysis_result TEXT NOT NULL,
                        additional_info TEXT,
                        final_report TEXT,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)''')

            # 创建问卷记录表
            conn.execute('''CREATE TABLE IF NOT EXISTS questionnaire_answers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        analysis_id INTEGER NOT NULL,
                        answers TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY(analysis_id) REFERENCES analysis_history(id) ON DELETE CASCADE)''')

            # 创建新表用于存储另一份分析报告
            conn.execute('''CREATE TABLE IF NOT EXISTS second_analysis_reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        report_time TEXT NOT NULL,
                        second_report TEXT NOT NULL,
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)''')

            # 迁移旧数据（如果存在旧表结构）
            try:
                conn.execute('''INSERT INTO analysis_history (user_id, analysis_time, file_path, analysis_result)
                              SELECT id, last_analysis_time, 'legacy_data', last_analysis_result
                              FROM users
                              WHERE last_analysis_time IS NOT NULL''')
                conn.execute("ALTER TABLE users DROP COLUMN last_analysis_time")
                conn.execute("ALTER TABLE users DROP COLUMN last_analysis_result")
            except sqlite3.OperationalError:
                pass

            conn.commit()

    def create_user(self, username, password):
        try:
            hashed_password = self._hash_password(password)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                             (username, hashed_password))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def verify_user(self, username, password):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            try:
                # 修复6：使用参数化查询防止SQL注入
                cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()

                print(f"[DEBUG] 数据库查询结果: {result}")  # 调试输出

                if result:
                    stored_hash = result[1]
                    input_hash = self._hash_password(password)

                    print(f"[DEBUG] 密码比对 - 存储哈希: {stored_hash}")  # 调试输出
                    print(f"[DEBUG] 输入哈希: {input_hash}")  # 调试输出

                    if stored_hash == input_hash:
                        return result[0]
            except sqlite3.Error as e:
                print(f"[ERROR] 数据库查询错误: {str(e)}")
            return None

    def add_analysis_record(self, user_id, file_path, result, additional_info=None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO analysis_history 
                          (user_id, analysis_time, file_path, analysis_result, additional_info)
                          VALUES (?, ?, ?, ?, ?)''',
                           (user_id, datetime.now().isoformat(), file_path, result,
                            json.dumps(additional_info) if additional_info else None))
            analysis_id = cursor.lastrowid
            conn.commit()
            return analysis_id

    def add_questionnaire_answers(self, user_id, analysis_id, answers):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute('''INSERT INTO questionnaire_answers 
                          (user_id, analysis_id, answers)
                          VALUES (?, ?, ?)''',
                         (user_id, analysis_id, json.dumps(answers)))
            conn.commit()

    def add_final_report(self, analysis_id, final_report):
        if isinstance(final_report, dict):
            final_report = json.dumps(final_report)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute('''UPDATE analysis_history 
                          SET final_report = ?
                          WHERE id = ?''',
                         (final_report, analysis_id))
            conn.commit()

    def add_second_final_report(self, user_id, second_final_report):
        """新增函数，用于将第二份分析报告写入新表"""
        if isinstance(second_final_report, dict):
            second_final_report = json.dumps(second_final_report)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute('''INSERT INTO second_analysis_reports 
                          (user_id, report_time, second_report)
                          VALUES (?, ?, ?)''',
                         (user_id, datetime.now().isoformat(), second_final_report))
            conn.commit()

    def get_user_history(self, user_id, limit=50):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute('''SELECT analysis_time, file_path, analysis_result, final_report 
                            FROM analysis_history 
                            WHERE user_id=?
                            ORDER BY analysis_time DESC
                            LIMIT ?''', (user_id, limit))
            return cursor.fetchall()

    def get_user_second_reports(self, user_id, limit=50):
        """新增函数，用于获取用户的第二份分析报告"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            cursor.execute('''SELECT report_time, second_report 
                            FROM second_analysis_reports 
                            WHERE user_id=?
                            ORDER BY report_time DESC
                            LIMIT ?''', (user_id, limit))
            return cursor.fetchall()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

