# EXE 解压服务

在 iOS/Android 手机上解压自解压 EXE 压缩文件，支持所有加密方式包括 AES-256。

## 功能特性

- ✅ 支持 ZIP/7z/RAR 自解压 EXE 文件
- ✅ 支持 AES-256 加密
- ✅ 支持 RAR5 新压缩算法
- ✅ 快速加密检测（< 2秒）
- ✅ 输入密码后无需重新上传文件
- ✅ 最大支持 500MB 文件

## 本地运行

### 环境要求

- Python 3.8+
- Linux/macOS/Windows

### 安装依赖

```bash
# Ubuntu/Debian
sudo apt install p7zip-full unrar

# macOS
brew install p7zip unrar

# 安装 Python 依赖
pip install -r requirements.txt
```

### 启动服务

```bash
# 开发模式
python server.py

# 生产模式（推荐）
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:8080 --timeout 300 server:app
```

然后在浏览器访问 `http://localhost:8080`

### 局域网访问

如果想让手机访问，确保手机和电脑在同一 WiFi 下：

1. 查看电脑 IP：`ifconfig` 或 `ipconfig`
2. 手机浏览器访问 `http://电脑IP:8080`

## 免费部署方案

### 方案一：Cloudflare Tunnel（推荐，无需域名）

```bash
# 安装 cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# 启动服务
gunicorn -w 2 -b 0.0.0.0:8080 --timeout 300 server:app &

# 创建隧道（自动生成公网地址）
./cloudflared tunnel --url http://localhost:8080
```

会生成类似 `https://xxx.trycloudflare.com` 的公网地址，手机可直接访问。

### 方案二：Railway.app

1. 注册 [Railway](https://railway.app)（免费 $5/月额度）
2. 创建新项目 → Deploy from GitHub repo
3. 选择此仓库，自动部署

### 方案三：Render.com

1. 注册 [Render](https://render.com)
2. 创建 Web Service → Connect GitHub repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 300 server:app`

## 文件结构

```
exe-extractor/
├── server.py          # 后端服务
├── requirements.txt   # Python 依赖
├── static/
│   └── index.html     # 前端页面
└── README.md
```

## 常见问题

**Q: 为什么上传速度慢？**

A: 如果通过 CloudStudio 等代理访问，带宽有限制。部署到自己的服务器会快很多。

**Q: 支持 RAR 文件吗？**

A: 支持！包括 RAR5 新压缩算法。

**Q: 密码错误怎么办？**

A: 会提示重新输入，无需重新上传文件。

## License

MIT
