# 轨迹分析系统

## 项目结构

```
tp/
├── backend/                # 后端代码
│   ├── api/               # API接口定义
│   ├── config/            # 配置文件
│   ├── crud/              # 数据库操作
│   ├── db/                # 数据库配置
│   ├── logging/           # 日志配置
│   ├── middleware/        # 中间件
│   ├── models/            # 数据模型
│   ├── routers/           # 路由处理
│   ├── tools/             # 工具函数
│   ├── utils/             # 通用工具
│   ├── migrations/        # 数据库迁移文件
│   ├── temp/              # 临时文件目录
│   └── keybackups/        # 密钥备份目录
├── frontend/              # 前端代码
│   ├── static/           # 静态资源
│   ├── admin.html        # 管理员页面
│   ├── image.html        # 图片管理页面
│   ├── index.html        # 首页
│   ├── login.html        # 登录页面
│   ├── map.html          # 地图页面
│   ├── task.html         # 任务管理页面
│   └── upload.html       # 文件上传页面
├── uploads/              # 上传文件目录
├── outputs/              # 输出文件目录
├── pip_packages/         # 离线安装包目录
├── .env                  # 环境变量配置
├── .env.example         # 环境变量示例
├── main.py              # 主程序入口
├── requirements.txt     # 依赖包列表
└── OFFLINE_INSTALL.md   # 离线安装说明
```

## 主要功能

1. 用户管理
   - 用户登录/注册
   - 权限控制
   - 管理员功能

2. 文件管理
   - 文件上传
   - 图片管理
   - 文件下载

3. 轨迹分析
   - 轨迹数据导入
   - 轨迹可视化
   - 轨迹报告生成

4. 系统管理
   - 任务管理
   - 系统配置
   - 日志记录

## 技术栈

- 后端：Python FastAPI
- 前端：HTML/CSS/JavaScript
- 数据库：MySQL
- 地图：高德地图 API
- 文档处理：python-docx

## 安装说明

详细的安装说明请参考 [OFFLINE_INSTALL.md](OFFLINE_INSTALL.md)

## 开发环境

- Python 3.8+
- MySQL 5.7+
- Node.js 14+ (可选，用于前端开发)

## 配置说明

1. 复制 `.env.example` 为 `.env`
2. 修改数据库配置
3. 配置服务器参数
4. 设置安全参数

## 运行说明

1. 启动后端服务：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

2. 访问前端页面：
```
http://localhost:8000
```

## 注意事项

1. 首次运行需要执行数据库迁移
2. 确保上传目录具有写入权限
3. 建议定期备份数据库
4. 注意保护密钥文件

## 更新日志

### 2024-04-03
- 优化轨迹报告格式
- 移除图片在线查看功能
- 添加离线安装说明文档

### 2024-04-02
- 添加文件管理功能
- 优化用户界面
- 完善错误处理

### 2024-04-01
- 初始版本发布
- 实现基本功能
- 添加用户认证