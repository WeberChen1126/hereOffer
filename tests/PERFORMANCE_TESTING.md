# 性能测试指南

本文档说明如何运行性能测试来获取系统的真实性能指标。

## 前置条件

1. **服务运行**
   - API 服务运行在 `http://localhost:8000`
   - Worker 服务正在运行（用于异步任务测试）
   - 数据库、Redis、MinIO 服务正常运行

2. **获取 Token**
   ```bash
   # 登录获取 token
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "your_email@example.com", "password": "your_password"}'
   
   # 设置环境变量
   export TEST_TOKEN=your_token_here
   # Windows PowerShell:
   $env:TEST_TOKEN="your_token_here"
   ```

## 运行测试

```bash
cd tests
python test_performance_metrics.py
```

## 测试指标说明

### 1. 处理能力测试

- **简历解析时间**: 测试 LLM 解析简历的耗时
- **简历评分时间**: 测试 LLM 评分简历的耗时
- **题目生成时间**: 测试 LLM 生成面试题的耗时

这些测试会调用真实的 LLM API，需要：
- 有效的 `DASHSCOPE_API_KEY`
- `LLM_MOCK=0`（使用真实 API）

### 2. 系统性能测试

- **API 响应时间**: 测试 API 端点的响应时间（P95）
- **数据库查询时间**: 测试数据库查询的响应时间（P95）
- **WebSocket 延迟**: 测试 WebSocket 消息的往返延迟
- **文件上传速度**: 测试文件上传到 MinIO 的速度

## 测试结果

测试完成后，脚本会输出：
1. 每个指标的统计信息（最小值、最大值、平均值、中位数、P95、P99）
2. README.md 更新建议

## 更新 README.md

根据测试结果，更新 `README.md` 中的性能指标部分：

```markdown
## 📊 性能指标

### 处理能力
- 简历解析：XX 秒/份（LLM）
- 简历评分：XX 秒/份（LLM）
- 题目生成：XX 秒/份（LLM）
- 并发处理：XX+ 简历/小时（单 Worker）

### 系统性能
- API 响应：< XXms（P95）
- 数据库查询：< XXms（P95）
- WebSocket 延迟：< XXms
- 文件上传：XXMB/秒+
```

## 注意事项

1. **LLM 测试**: 需要真实的 API Key，会产生费用
2. **测试环境**: 建议在独立的测试环境中运行
3. **网络影响**: 测试结果会受到网络延迟影响
4. **多次测试**: 建议多次运行测试取平均值

## 常见问题

**Q: 测试失败，提示连接错误**
A: 确保所有服务都在运行，检查端口是否正确

**Q: LLM 测试超时**
A: 增加超时时间，或检查 LLM API 是否正常

**Q: 如何测试并发处理能力**
A: 可以修改测试脚本，使用多线程/多进程同时提交多个任务
