# Vue 3 + Vite

This template should help get you started developing with Vue 3 in Vite. The template uses Vue 3 `<script setup>` SFCs, check out the [script setup docs](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup) to learn more.

Learn more about IDE Support for Vue in the [Vue Docs Scaling up Guide](https://vuejs.org/guide/scaling-up/tooling.html#ide-support).

# 前端应用

这是校园广播站音频处理系统的前端部分，基于Vue.js构建。

## 开发环境设置

1. 安装依赖：

```bash
npm install
```

2. 配置环境变量：

创建`.env`文件（或复制`.env.example`），并设置后端API地址：

```
VITE_API_BASE_URL=http://localhost:8000
```

3. 运行开发服务器：

```bash
npm run dev
```

## 构建生产版本

```bash
npm run build
```

## Vercel一键部署

项目前端可以部署到Vercel，按照以下步骤操作：

1. 创建Vercel账号并连接到你的GitHub仓库
2. 导入此项目（确保在仓库根目录或设置正确的子目录）
3. 在环境变量中设置`VITE_API_BASE_URL`为你的后端API地址
4. 点击部署

或者直接点击下面的按钮：

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fusername%2Fcampus-radio-processor&env=VITE_API_BASE_URL)

## 自定义API服务器

应用启动后，点击页面顶部的"服务器设置"按钮，可以设置自定义的后端API地址。设置完成后，应用将使用新的地址连接后端服务。
