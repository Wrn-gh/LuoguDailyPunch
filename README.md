# LuoguDailyPunch

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

一个洛谷自动打卡程序，帮你每天自动打卡并获取运势

## Ver 2.0 Change Log
- 洛谷运势看板 `lgpunch card` 唤出
![CardScreenshot](/imgs/card_screenshot.png)
- 新增 `lgpunch settings` 终端配置界面（Rich + Textual）
![SettingsScreenshot](/imgs/settings_screenshot.png)
- 新增静默模式：开启后打卡不再弹出系统通知
- 修复了打卡结果的获取与显示

## 功能特性
- 可配置开机自启，自动打卡
- 每天自动打卡一次，用Windows通知显示今日运势 
- 支持通过命令行手动打卡、查看打卡信息、配置用户信息

## 安装

**通过Release安装（推荐）**
1. 访问本项目的Release页面，获取预编译版本
2. 将程序解压到你喜欢的目录
3. 打开powershell终端，运行：
```powershell
./setup.ps1
```
4. 依照操作指引完成配置

**通过源码安装**
```powershell
# 1. 克隆并进入目录
git clone https://github.com/Wrn-gh/LuoguDailyPunch.git
cd LuoguDailyPunch

# 2. 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 安装依赖
pip install -r requirements.txt

# 4. 编译并打包
.\scripts\build.ps1

# 5. 进入 release 目录运行安装脚本
cd release
.\setup.ps1
```

## 使用

| 命令 | 说明 |
|------|------|
| `lgpunch punch` | 手动打卡 |
| `lgpunch set --uid <UID> --cid <ClientID>` | 配置用户信息 |
| `lgpunch settings` | 打开终端配置界面 |
| `lgpunch userinfo` | 查看已配置的用户信息 |
| `lgpunch punchinfo` | 查看最近一次打卡信息 |
| `lgpunch card` | 唤出运势卡片 |