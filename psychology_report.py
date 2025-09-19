import os
import requests
import json
app_id = "d1534299-f286-48b6-98e8-f98594b36336"
with open('token.txt', 'r') as file:
    token = file.read().strip() 
def generate_psychology_report():
     # ------------------新建对话------------------

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
    
    # ------------------上传逻辑------------------
# 在这中间可以修改选择哪张照片↓↓↓↓↓↓↓↓↓↓↓↓
    # 找到 images 文件夹下最新的图片
    images_folder = 'save_images'
    if not os.path.exists(images_folder):
        print(f"错误: 文件夹 {images_folder} 不存在。")
        return None
    image_files = [os.path.join(images_folder, f) for f in os.listdir(images_folder) if
                   f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        print("错误: images 文件夹中没有图片文件。")
        return None
    latest_image = max(image_files, key=os.path.getctime)
# 在这中间可以修改选择哪张照片↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
    image_upload_url = "https://qianfan.baidubce.com/v2/app/conversation/file/upload"
    
    payload = {
        'app_id': app_id,
        'conversation_id': conversation_id,
    }
    headers = {
        'Authorization': f'Bearer {token}',
    }

    with open(latest_image, 'rb') as img_file:
        response = requests.post(image_upload_url, headers=headers, data=payload, files={'file': img_file})
    print("文件上传响应:", response.text)
    file_id = response.json().get("id")
    # ------------------上传图片------------------
    # ------------------上传逻辑------------------
    # ------------------调用工作流逻辑------------------
    if file_id:
            try:
                url = "https://qianfan.baidubce.com/v2/app/conversation/runs"
                
                payload = json.dumps({
                    "app_id": app_id,
                    "query": "这是我的绘画，请帮我分析一下我的心理状态",
                    "conversation_id": conversation_id,
                    "stream": False,
                    "file_ids": [
                        response.json().get("id")
                    ]
                }, ensure_ascii=False)
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                    
                }
                
                response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))
                print(response.text)
                return response.json().get("answer")
            # ------------------调用工作流逻辑------------------

            except requests.RequestException as e:
                print(f"错误: 对话时发生请求错误: {e}")
                return None
    else:
        print("错误: 文件上传失败，未获取到 file_id。")
        return None