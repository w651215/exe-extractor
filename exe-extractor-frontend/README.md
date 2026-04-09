# EXE 解压工具

一个纯前端的 EXE 自解压文件解压工具，无需服务器，完全在浏览器本地运行。

## 功能特点

- 🔒 **隐私安全**：文件完全在本地处理，不上传任何服务器
- 📱 **移动优先**：专为 iOS Safari 优化，支持添加到主屏幕
- 📦 **支持格式**：ZIP、7z 自解压 EXE 文件
- 🚀 **离线可用**：PWA 支持，添加到主屏幕后可离线使用
- 🆓 **完全免费**：可免费托管在 GitHub Pages

## 部署方法

### 方法一：GitHub Pages（推荐）

1. 创建一个新的 GitHub 仓库
2. 上传以下文件：
   - `index.html`
   - `manifest.json`
   - `sw.js`
   - `icon-192.png`
   - `icon-512.png`
3. 进入仓库 Settings → Pages
4. Source 选择 `main` 分支，点击 Save
5. 几分钟后即可通过 `https://你的用户名.github.io/仓库名/` 访问

### 方法二：Vercel

1. 将代码推送到 GitHub
2. 在 Vercel 导入该项目
3. 自动部署完成

### 方法三：本地使用

直接用浏览器打开 `index.html` 文件即可使用。

## 添加到主屏幕（iOS）

1. 在 Safari 中打开网页
2. 点击底部分享按钮
3. 选择「添加到主屏幕」
4. 即可像 App 一样使用

## 技术栈

- **ZIP 解压**：[JSZip](https://stuk.github.io/jszip/)
- **7z 解压**：[7z-wasm](https://github.com/nickolay/7z-wasm)
- **PWA**：Service Worker + Web App Manifest

## 限制说明

- RAR 格式因专利限制，浏览器端暂不支持
- 最大支持约 2GB 文件（受浏览器内存限制）
- 首次打开需要网络加载依赖，之后可离线使用

## License

MIT
