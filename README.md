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

## 项目结构

```
Campus-Radio-Processor/
├── frontend/                # Vue.js 前端
│   ├── src/
│   │   ├── components/      # Vue 组件
│   │   │   ├── AudioList.vue            # 待处理音频列表组件
│   │   │   ├── ProcessedAudioList.vue   # 已处理音频列表组件
│   │   │   └── AudioUploader.vue        # 音频上传组件
│   │   ├── audioState.js    # 全局音频播放状态管理
│   │   ├── assets/          # 静态资源
│   │   ├── style.css        # 全局样式
│   │   ├── main.js          # 入口文件
│   │   └── App.vue          # 主应用组件
│   ├── public/              # 公共资源
│   └── package.json         # 前端依赖配置
└── backend/                 # FastAPI 后端
    ├── app.py               # 主应用文件
    ├── run.py               # 启动脚本
    ├── requirements.txt     # 依赖项
    ├── uploads/             # 上传的音频文件存储目录
    ├── processed/           # 处理后的音频文件存储目录
    └── audio_metadata.json  # 音频元数据存储文件
```

## 安装与运行

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

## 使用说明

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

## 注意事项

- 确保系统中已正确安装FFmpeg，这对音频处理功能至关重要
- 默认支持的音频格式：MP3, WAV, OGG, FLAC等主流格式
- 处理大文件可能需要较长时间，请耐心等待

Powered By LaoShui @ 2025
