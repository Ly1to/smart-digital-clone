# Orbit

React + Framer Motion 日程看板，支持工作事务、娱乐、个人日常、本地音乐推荐、
GitHub 仓库同步和 25/10 番茄钟。

## 启动

需要 Node.js 18+ 和 Python 3.10+。

```bash
npm install

# 终端 1
npm run api

# 终端 2
npm run dev
```

打开 `http://127.0.0.1:5173/`。API 默认运行在
`http://127.0.0.1:8787`。

## 数据

- `data/schedules.json`：本地日程，首次由 `schedules.seed.json` 初始化。
- `data/music-source.json`：当前本地音乐源。
- `.env`：可选 Token 和时区配置。

以上运行数据与 `.env` 均已忽略。日程支持可选的 `deadline`，设为 `null`
表示无截止时间。

## GitHub

点击看板顶部的 `GitHub`，输入用户名或主页地址。系统会将最近 21 天有公开提交的
仓库同步为工作事务。

可在弹窗中直接填写 Fine-grained token：

1. 打开 GitHub `Settings → Developer settings → Personal access tokens →
   Fine-grained tokens`。
2. Repository access 选择 `Public repositories`。
3. Repository permissions 中将 `Contents` 设为 `Read-only`。
4. 生成 `github_pat_...` 并粘贴到网页。

网页 Token 只保留在当前页面内存中，不写入文件。也可以使用 `.env`：

```bash
cp .env.example .env
# 填写 GITHUB_TOKEN
```

## 音乐

点击 `音乐库`，输入本地目录或歌单路径，例如 `~/Music`。支持 M3U、PLS、JSON、
CSV、TXT，以及 MP3、FLAC、M4A、WAV、OGG 等音频文件。

## 验证

```bash
npm run build
npm test
```
