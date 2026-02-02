# 🚀 hereOffer 快速启动指南

---

## ✅ 部署状态: 成功

**所有服务已启动并正常运行！**

---

## 📍 快速访问

### 🌐 立即使用

#### 前端应用
```
http://localhost:3000
```
→ 用户注册、登录、浏览职位、投递简历、实时对话

#### API 文档 (Swagger)
```
http://localhost:8000/docs
```
→ 测试所有后端接口

#### MinIO 控制台
```
http://localhost:9001
用户名: minioadmin
密码: minioadmin
```
→ 查看上传的简历文件

---

## 🎯 快速测试流程

### 第一步: 注册用户
1. 打开浏览器访问 http://localhost:3000
2. 点击"注册"标签
3. 填写信息:
   - 邮箱: test@example.com
   - 密码: test123456
4. 点击"注册"

### 第二步: 创建职位（Admin）
使用 API 文档创建职位:
1. 访问 http://localhost:8000/docs
2. 找到 `POST /admin/jobs`
3. 点击 "Try it out"
4. 输入示例数据:
```json
{
  "title": "Python 后端工程师",
  "jd_text": "负责后端开发，熟悉 Python、FastAPI、MySQL",
  "threshold_score": 70,
  "is_active": true
}
```
5. 点击 "Execute"

### 第三步: 投递简历
1. 回到前端 http://localhost:3000
2. 登录刚才注册的账号
3. 在职位列表中找到刚创建的职位
4. 点击"投递简历"
5. 上传简历文件（PDF/Word/Txt）
6. 等待处理

### 第四步: 查看状态
1. 点击"我的投递"
2. 查看投递状态变化:
   - PENDING → 等待处理
   - PARSED → 简历已解析
   - SCORED → 评分完成
   - QUESTIONS_GENERATED → 题目已生成

### 第五步: 开始对话
1. 当状态变为 `QUESTIONS_GENERATED`
2. 点击"开始对话"
3. 进入实时对话界面
4. 可以文字或语音交流

---

## 🔧 常用命令

### 查看运行状态
```bash
docker ps
```

### 查看日志
```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker logs recruit_flow_api -f
docker logs recruit_flow_frontend -f
docker logs recruit_flow_worker -f
```

### 重启服务
```bash
# 全部重启
docker-compose restart

# 单独重启
docker-compose restart api
docker-compose restart frontend
```

### 停止服务
```bash
docker-compose down
```

### 重新部署
```bash
# 停止并清理
docker-compose down

# 重新构建和启动
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 服务端口

| 服务 | 端口 | 用途 |
|------|------|------|
| 前端 | 3000 | Web 界面 |
| API | 8000 | 后端接口 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存/队列 |
| MinIO | 9000 | S3 API |
| MinIO 控制台 | 9001 | 管理界面 |

---

## ⚠️ 注意事项

### 1. 环境变量
确保 `.env` 文件包含:
```
DASHSCOPE_API_KEY=your_api_key_here
```

### 2. 首次使用
- 数据库会自动初始化
- MinIO 存储桶会自动创建
- 第一次启动可能需要几分钟

### 3. 性能
- Worker 处理任务需要时间
- 可以在日志中看到处理进度
- 刷新页面查看最新状态

---

## 🐛 常见问题

### Q: 前端显示空白页面？
A: 检查浏览器控制台，可能需要刷新缓存 (Ctrl+F5)

### Q: 登录失败？
A: 确保后端服务正常运行: `docker logs recruit_flow_api`

### Q: 投递后状态不变？
A: 查看 Worker 日志: `docker logs recruit_flow_worker -f`

### Q: 文件上传失败？
A: 检查 MinIO 服务: `docker ps | grep minio`

---

## 📚 完整文档

详细信息请参考:
- **部署报告**: `DEPLOYMENT_SUCCESS.md`
- **前端检查**: `FRONTEND_CHECK_REPORT.md`
- **架构文档**: `ARCHITECTURE.md`
- **API 文档**: `docs/frontend/API_REFERENCE.md`

---

## 🎉 享受使用！

如有问题，请查看日志或参考文档。

**项目地址**: D:\CO\AI-HR  
**部署时间**: 2026-02-01
