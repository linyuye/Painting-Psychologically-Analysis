# 绘画心理分析-GitCode-文心-智源AI应用大赛  

## 项目简介

基于AI的绘画心理分析应用，集成了在线白板和问卷调查功能。调用百度千帆API，主要使用：

- **ERNIE 4.5 VL** - 利用文心4.5模型的多模态识图核心能力
- **ERNIE 4.5 Turbo** - 利用文心4.5模型对于长上下文理解的核心能力

## 项目结构

### Python主应用

- `main.py` - 主函数，启动显式界面  
- `auth_window.py` - 注册逻辑和界面  
- `painting_analyzer_app.py` - 分析逻辑  
- `psychology_report.py` - 外接大模型，返回分析结果  
- `questionnaire_window.py` - 题库界面逻辑和题库  
- `user_db.py` - MySQL管理的数据库  
- `data/` - 数据库文件  
- `save_images/` - 缓存图片  

### Node.js服务

- `auth/` - 用户认证服务
- `WBO白板/whitebophir/` - 在线绘画白板

## 安装说明

### 1. Python环境配置

```bash
cd 绘画心理分析v1.1
pip install -r requirements.txt
```

### 2. Node.js服务配置

**首次使用必须安装依赖！**

#### 安装WBO白板依赖

```bash
cd 绘画心理分析v1.1/WBO白板/whitebophir
npm install
```

#### 安装认证服务依赖

```bash
cd 绘画心理分析v1.1/auth
npm install
```

## 运行说明

### 启动认证服务

```bash
cd 绘画心理分析v1.1/auth
node server.js
```

### 启动WBO白板

```bash
cd 绘画心理分析v1.1/WBO白板/whitebophir
npm start
```

### 启动主应用

```bash
cd 绘画心理分析v1.1
python main.py
```

## 配置说明

- `token.txt` - 需要配置百度千帆API密钥
- API地址：https://qianfan.baidubce.com/v2/app/conversation

## 依赖要求

- Python 3.7+
- Node.js 12.0+
- npm 6.0+

## 注意事项

⚠️ **重要：** 项目中的 `node_modules` 目录已被忽略，首次使用前必须运行 `npm install` 安装依赖

## 许可证

详见项目内各子模块的LICENSE文件