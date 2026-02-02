# Frontend Environment Configuration

## 本地开发环境

运行 `npm run dev` 时，Vite 会自动代理：
- `/api` → `http://localhost:8000` (API 请求)
- `/ws` → `ws://localhost:8000` (WebSocket)

无需额外配置。

## Docker 部署

- 前端通过 Nginx (port 3000) 反向代理到后端 (port 8000)
- 前端代码中使用相对路径 `/api` 和 `/ws`
- Nginx 会自动转发到 `http://api:8000`

## 环境变量

### VITE_API_URL (默认: `/api`)

生产环境时可以通过此变量指定 API 地址：
```bash
# 在构建时指定
VITE_API_URL=https://api.example.com npm run build

# 或在 .env 文件中设置
VITE_API_URL=https://api.example.com
```

**注意**: 环境变量在构建时固定，运行时无法修改。
如需运行时动态配置，参考 FRONTEND_CHECK_REPORT.md 中的方案 D3。
