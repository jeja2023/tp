# 离线安装说明

## 1. 环境要求
- Python 3.8 或以上版本
- pip 包管理器

## 2. 安装步骤

### 2.1 创建虚拟环境（推荐）
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2.2 安装依赖包
```bash
# 进入packages目录
cd packages

# 安装所有依赖
pip install --no-index --find-links=. -r ../requirements.txt
```

### 2.3 静态文件部署
确保以下目录结构完整：
```
static/
├── css/
│   ├── all.min.css
│   └── styles.css
├── js/
│   ├── xlsx.full.min.js
│   ├── amap/
│   │   └── AMap3.js
│   └── MAP_zxy/
│       └── [地图瓦片文件]
```

### 2.4 启动服务
```bash
# 开发环境启动
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 生产环境启动
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 3. 访问方式
- 局域网内其他设备通过 `http://[服务器IP]:8000` 访问
- 例如：`http://192.168.1.100:8000`

## 4. 注意事项
1. 确保服务器防火墙允许 8000 端口访问
2. 确保所有静态文件都已正确部署
3. 高德地图的离线瓦片文件需要完整部署
4. 数据库文件会自动创建在项目根目录

## 5. 常见问题
1. 如果安装依赖时出现错误，请检查 Python 版本是否符合要求
2. 如果静态文件无法访问，请检查目录结构是否正确
3. 如果地图无法显示，请检查地图瓦片文件是否完整

## 6. 文件清单
请确保以下文件都已包含在部署包中：
- packages/ 目录（包含所有依赖包）
- requirements.txt
- main.py
- 其他项目源代码文件
- static/ 目录及其所有内容
- templates/ 目录及其所有内容 