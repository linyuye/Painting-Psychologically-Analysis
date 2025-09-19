import json
import os
json_folder = "."
questionnaires = {}
for filename in os.listdir(json_folder):
    if filename.endswith('.json'):
        file_path = os.path.join(json_folder, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(data)
                for key, value in data.items():
                    questionnaires[key] = value
        except FileNotFoundError:
            print(f"错误: 文件 {file_path} 未找到!")
        except json.JSONDecodeError:
             print(f"错误: 无法解析 JSON 文件 {file_path}!")
print(questionnaires)