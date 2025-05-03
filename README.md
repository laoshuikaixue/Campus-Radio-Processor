# 校园广播站音频处理系统

这是一个专为校园广播站设计的音频处理系统，允许用户上传、合并、排序和管理音频文件。系统通过直观的用户界面，帮助广播站工作人员高效地处理和管理音频资源。

## 项目截图
![image](https://github.com/user-attachments/assets/0530c61f-8c5f-41cd-9b5d-8aa531407b50)
![image](https://github.com/user-attachments/assets/973af9e3-9921-46bb-9347-2e8b502d7c69)

## 功能特点

- **音频文件上传与管理**：支持批量上传音频文件，自动去重，避免重复文件占用存储空间
- **音频文件合并**：可以选择多个音频文件进行合并，支持自定义排序
- **拖拽排序功能**：直观的拖拽界面，轻松调整音频播放顺序
- **处理状态跟踪**：音频处理过程中显示进度条，支持取消处理操作
- **音频文件重命名**：便捷修改音频文件显示名称
- **音频音量标准化**：统一音频音量，避免不同音频音量差异太大
- **前后端分离部署**：支持将前端部署到Vercel等静态托管平台，后端独立部署

## 项目结构

```
Campus-Radio-Processor/
├── frontend/                # Vue.js 前端
│   ├── src/
│   │   ├── components/      # Vue 组件
│   │   │   ├── AudioList.vue            # 待处理音频列表组件
│   │   │   ├── ProcessedAudioList.vue   # 已处理音频列表组件
│   │   │   ├── AudioUploader.vue        # 音频上传组件
│   │   │   └── ServerConfig.vue         # 服务器配置组件
│   │   ├── api.js           # API服务封装
│   │   ├── config.js        # 配置文件
│   │   ├── audioState.js    # 全局音频播放状态管理
│   │   ├── assets/          # 静态资源
│   │   ├── style.css        # 全局样式
│   │   ├── main.js          # 入口文件
│   │   └── App.vue          # 主应用组件
│   ├── public/              # 公共资源
│   ├── vercel.json          # Vercel部署配置
│   └── package.json         # 前端依赖配置
└── backend/                 # FastAPI 后端
    ├── app.py               # 主应用文件
    ├── run.py               # 启动脚本
    ├── requirements.txt     # 依赖项
    ├── uploads/             # 上传的音频文件存储目录
    ├── processed/           # 处理后的音频文件存储目录
    └── audio_metadata.json  # 音频元数据存储文件
```

## 本地安装与运行

### 后端设置

1. 进入后端目录：

```bash
cd backend
```

2. 创建并激活虚拟环境：

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# 或
source venv/bin/activate  # Linux/Mac
```

3. 安装依赖：

```bash
pip install -r requirements.txt
```

4. 运行后端服务器：

```bash
python run.py
```

后端服务器将在 http://localhost:8000 上运行。

### 前端设置

1. 进入前端目录：

```bash
cd frontend
```

2. 安装依赖：

```bash
npm install
```

3. 运行开发服务器：

```bash
npm run dev
```

前端应用将在 http://localhost:5173 上运行。

### 后端部署选项

后端需要一个支持Python和文件存储的环境，可选择以下部署方案：

#### 1. 传统VPS/云服务器

适合长期运行的生产环境:

```bash
# 在服务器上
git clone https://github.com/username/campus-radio-processor.git
cd campus-radio-processor/backend
pip install -r requirements.txt
# 安装FFmpeg
apt-get update && apt-get install -y ffmpeg  # Debian/Ubuntu
# 使用gunicorn或uvicorn作为生产服务器
pip install gunicorn uvicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app:app
```

#### 2. Docker部署

创建一个包含FFmpeg的Docker镜像:

```bash
# 在backend目录创建Dockerfile
cd backend
echo 'FROM python:3.9
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]' > Dockerfile

# 构建并运行
docker build -t campus-radio-backend .
docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/processed:/app/processed campus-radio-backend
```

#### 3. 平台即服务 (PaaS)

在Railway、Render或Fly.io等平台上部署（确保支持FFmpeg安装）:

```bash
# 在backend目录创建适用于Railway的railway.toml
cd backend
echo '[build]
builder = "nixpacks"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn app:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/"

[nixpacks]
pkgs = ["ffmpeg"]' > railway.toml
```

## 注意事项

- 无论选择哪种部署方案，后端都需要配置CORS以允许前端域名的请求
- 对于生产环境，请考虑添加身份验证和HTTPS支持
- 确保部署环境中已正确安装FFmpeg，这对音频处理功能至关重要
- 在分离部署模式下，你需要在前端应用中配置正确的后端API地址

## 使用说明

### 自定义API服务器

前端应用启动后，点击页面顶部的"服务器设置"按钮，可以设置自定义的后端API地址。

### 音频文件上传

1. 点击主页上方的"选择音频文件"按钮
2. 选择一个或多个音频文件
3. 点击"上传"按钮开始上传
4. 系统会自动检测重复文件，避免重复上传

### 音频管理和排序

1. 在"待处理音频文件列表"中可以看到所有上传的音频
2. 通过拖放操作可以调整音频文件的播放顺序
3. 点击重命名按钮可以修改音频文件显示名称
4. 点击播放按钮可以预览音频内容
5. 点击删除按钮可以移除不需要的音频文件

### 音频处理

1. 点击"处理列表中的X个文件"按钮
2. 在弹出的对话框中，输入合并后的文件名
3. 可选是否开启音量标准化功能
4. 点击"合并"按钮开始处理
5. 处理过程中会显示进度条，可以点击"取消"按钮中止处理

### 已处理音频管理

1. 在"已处理音频文件列表"中可以看到所有处理完成的音频
2. 点击播放按钮可以预览处理后的音频
3. 点击下载按钮可以下载处理后的音频文件
4. 点击删除按钮可以移除不需要的处理后音频文件

## 技术栈

- **前端**：
  - Vue.js 3 (组合式API)
  - Vite (构建工具)
  - Axios (HTTP请求)
  - 现代CSS (Flexbox, Grid, 动画)

- **后端**：
  - FastAPI (高性能Python API框架)
  - PyDub (音频处理)
  - Python 3.x

## 系统要求

- **后端**：
  - Python 3.7+
  - FFmpeg (支持音频处理)
  - 足够的磁盘空间存储音频文件

- **前端**：
  - Node.js 14+
  - 现代浏览器 (Chrome, Firefox, Edge等)

Powered By LaoShui @ 2025
