# HXDIEvaluationServer

HXDIEvaluationServer 是一个用于评估和报告的服务器项目。

## 功能特性

- 评估规范管理
- 证据管理
- 报告生成
- API接口

## 快速开始

1. 克隆项目：
   ```bash
   git clone https://github.com/StellarFlash/HXDIEvaluationServer.git
   ```

2. 确保已安装并运行Elasticsearch实例（版本7.x或8.x），并配置好相关认证信息

3. 复制环境变量模板：
   ```bash
   cp .env.example .env
   ```
   然后根据实际情况编辑.env文件，特别是ES_SCHEME, ES_HOST, ES_PORT, ES_USER和ES_PASSWORD配置

4. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

5. 运行服务器：
   ```bash
   python api/main.py
   ```

## API 端点

- `POST /api/upload` - 上传文档
- `GET /api/reports` - 获取报告列表
- `GET /api/reports/{report_id}` - 获取单个报告详情
- `POST /api/reports` - 创建新报告
- `PUT /api/reports/{report_id}` - 更新报告
- `DELETE /api/reports/{report_id}` - 删除报告

## ROADMAP

### 近期计划
- 实现WebUI界面
- 添加用户认证系统
- 优化报告生成性能

### 长期计划
- 支持多格式文档上传
- 集成更多AI分析功能
- 实现实时协作编辑

## 贡献指南

欢迎提交Pull Request或Issue来改进本项目。

## 许可证

本项目采用 MIT 许可证。
