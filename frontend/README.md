# hereOffer Frontend

基于 React + TypeScript + Vite 构建的前端项目。

## 目录结构

```
frontend/
├── src/
│   ├── api/           # API 接口定义
│   ├── components/    # 公共组件
│   ├── pages/         # 页面组件
│   │   ├── Login.tsx          # 登录/注册
│   │   ├── JobList.tsx        # 职位列表 & 投递
│   │   ├── ApplicationList.tsx # 投递列表 & 入口
│   │   └── Chat.tsx           # 实时对话 (WebSocket)
│   ├── utils/         # 工具函数 (request.ts)
│   ├── App.tsx        # 路由和布局
│   └── main.tsx       # 入口
├── Dockerfile         # Docker 构建文件 (Nginx)
├── nginx.conf         # Nginx 配置
└── vite.config.ts     # Vite 配置
```

## 本地开发

1. 安装依赖:
   ```bash
   npm install
   ```

2. 启动开发服务器:
   ```bash
   npm run dev
   ```
   访问: http://localhost:3000

## 独立部署

本项目设计为可以与后端完全分离部署。

### 使用 Docker 部署

1. 构建镜像:
   ```bash
   docker build -t hereoffer-frontend .
   ```

2. 运行容器:
   ```bash
   docker run -d -p 80:80 hereoffer-frontend
   ```
   注意：如果后端不在同一网络，需要修改 `nginx.conf` 中的 `proxy_pass` 地址，或者在构建时通过环境变量注入 API 地址。

### 静态文件部署

运行 `npm run build`，将 `dist/` 目录下的文件部署到任何静态文件服务器 (Nginx, Apache, AWS S3, Vercel 等)。
需确保服务器配置了 API 反向代理，或者前端配置了正确的 API Base URL。
