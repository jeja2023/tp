# 离线安装项目依赖说明

本文件夹包含了项目所需的所有Python依赖包，适用于Python 3.12版本，以及一键安装脚本。

## 安装步骤

### 方法一：使用一键安装脚本（推荐）

1. 将整个`pip_packages`文件夹复制到目标电脑的项目根目录
2. 双击运行`install_dependencies.bat`文件
3. 等待安装完成

### 方法二：手动安装

如果自动脚本不起作用，可以按照以下步骤手动安装：

1. 打开命令提示符（CMD）或PowerShell
2. 切换到项目目录
3. 创建并激活虚拟环境（可选但推荐）：
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```
4. 执行以下命令安装依赖：
   ```
   pip install --no-index --find-links=pip_packages -r requirements.txt
   ```

## 注意事项

- 这些包是为Python 3.12版本下载的，如果您使用其他Python版本，可能需要重新下载对应版本的包
- 安装完成后，请根据项目README文件配置数据库和环境变量
- 如出现安装问题，请检查Python版本是否匹配 